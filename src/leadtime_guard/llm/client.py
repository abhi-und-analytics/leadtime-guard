"""LLM client for FREE providers.

Pick the provider with the environment variable LTG_PROVIDER (default: opencode):
  opencode - the OpenCode CLI installed in your terminal, with one of its free models (see opencode_cli.py).
             Model: env LTG_MODEL, e.g. a "-free" model from `opencode models` (empty = OpenCode's default model)
  gemini  - Google Gemini API free tier. Key from Google AI Studio -> env GEMINI_API_KEY. Model: gemini-3.8-flash
  ollama  - local open model on your own laptop (fully offline, no key). Model: env LTG_MODEL, e.g. llama3.1:8b
  groq    - Groq free plan. Key from console.groq.com -> env GROQ_API_KEY. Model: openai/gpt-oss-120b

Override the model with env LTG_MODEL. All of these cost EUR 0 within their free limits.
Free-tier note: Gemini free-tier prompts may be used by Google to improve its products, so only ever
send SYNTHETIC data (this project uses synthetic data only). For confidential data use Ollama (local).
"""

import json
import os
import sys
import time

from .cost import Usage

PROVIDERS = {
    "opencode": {"base_url": None, "key_env": None, "model": None},   # uses the opencode CLI, no key in Python
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
               "key_env": "GEMINI_API_KEY", "model": "gemini-3.8-flash"},
    "ollama": {"base_url": "http://localhost:11434/v1", "key_env": None, "model": "llama3.1:8b"},
    "groq":   {"base_url": "https://api.groq.com/openai/v1",
               "key_env": "GROQ_API_KEY", "model": "openai/gpt-oss-120b"},
}

# Free tiers have requests-per-minute limits. Wait this many seconds between calls (env LTG_MIN_INTERVAL).
MIN_INTERVAL_S = float(os.environ.get("LTG_MIN_INTERVAL", "4"))
_last_call = [0.0]


def provider_settings():
    name = os.environ.get("LTG_PROVIDER", "opencode").lower()
    if name not in PROVIDERS:
        sys.exit(f"Unknown LTG_PROVIDER '{name}'. Use one of: {', '.join(PROVIDERS)}")
    p = dict(PROVIDERS[name], name=name)
    p["model"] = os.environ.get("LTG_MODEL", p["model"])
    return p


def get_client():
    """Return (OpenAI-compatible client, settings). Stops with a clear message if the key is missing."""
    p = provider_settings()
    if p["name"] == "opencode":
        from .opencode_cli import find_opencode
        find_opencode()          # stops with a clear message if opencode is not installed
        return None, p
    key = "ollama"  # Ollama ignores the key, but the SDK needs a non-empty string
    if p["key_env"]:
        key = os.environ.get(p["key_env"])
        if not key:
            sys.exit(f"{p['key_env']} is not set. Get a free key and set it first (see README, Day 1 checklist).")
    from openai import OpenAI  # imported here so the rest of the project works without the SDK installed
    return OpenAI(base_url=p["base_url"], api_key=key), p


def _wait_for_rate_limit():
    gap = time.time() - _last_call[0]
    if gap < MIN_INTERVAL_S:
        time.sleep(MIN_INTERVAL_S - gap)
    _last_call[0] = time.time()


def _is_temporary(err) -> bool:
    """Rate limit (429) or server busy (500/503): worth waiting and trying the SAME call again."""
    code = getattr(err, "status_code", None)
    name = type(err).__name__
    return code in (429, 500, 502, 503, 504) or name in ("RateLimitError", "InternalServerError",
                                                         "APITimeoutError", "APIConnectionError")


def _with_retries(call, what: str):
    """Free tiers often answer 429 (too many requests) or 503 (model busy). Wait and retry: 20 s, 40 s, 80 s."""
    waits = [20, 40, 80]
    for attempt in range(len(waits) + 1):
        try:
            _wait_for_rate_limit()
            return call()
        except Exception as err:
            if not _is_temporary(err) or attempt == len(waits):
                raise
            print(f"  ({what}: {type(err).__name__}, waiting {waits[attempt]} s and retrying)", flush=True)
            time.sleep(waits[attempt])


def parse(client, settings, usage: Usage, output_model, *, system: str, user_text: str, max_tokens: int = 1024):
    """One structured call. Returns (parsed Pydantic object, raw response).

    Gemini, Ollama and Groq: JSON mode + the schema in the prompt + Pydantic validation (one call per email,
    works on every OpenAI-compatible API). Temporary errors (429 rate limit, 503 busy) are retried with waits.
    """
    if settings["name"] == "opencode":
        _wait_for_rate_limit()
        from .opencode_cli import parse as opencode_parse
        parsed, response = opencode_parse(output_model, system=system, user_text=user_text, model=settings["model"])
        usage.add(settings["model"] or "opencode-default", response.usage)
        return parsed, response
    model = settings["model"]
    schema = json.dumps(output_model.model_json_schema())
    messages = [{"role": "system", "content": system + "\n\nReturn ONLY one JSON object that matches this JSON schema:\n"
                 + schema},
                {"role": "user", "content": user_text}]
    response = _with_retries(lambda: client.chat.completions.create(
        model=model, messages=messages, max_tokens=max_tokens, response_format={"type": "json_object"}), "AI call")
    usage.add(model, response.usage)
    if response.choices[0].finish_reason == "length":
        raise RuntimeError("Model ran out of tokens - increase max_tokens.")
    text = response.choices[0].message.content or ""
    start, end = text.find("{"), text.rfind("}")
    parsed = output_model.model_validate_json(text[start:end + 1] if start != -1 else text)
    return parsed, response
