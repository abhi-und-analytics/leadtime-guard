"""Use the OpenCode CLI (installed in your terminal) as the LLM provider - EUR 0 with OpenCode's free models.

How it works:
  1. The instructions, the JSON schema and the email are written to a temporary prompt file.
  2. `opencode run --format json --agent plan -f prompt.txt "..."` runs in an EMPTY temporary folder,
     with the read-only "plan" agent, so OpenCode cannot read or edit your project files.
  3. The text answer is taken from the JSON events, the JSON object is cut out and validated with Pydantic.
     If validation fails, it retries once and tells the model what was wrong.

Settings (environment variables):
  LTG_MODEL           OpenCode model id, e.g. a free one from `opencode models` (if empty: OpenCode's default model)
  LTG_OPENCODE_BIN    path to the opencode executable (default: found on PATH)
  LTG_OPENCODE_AGENT  agent to use (default: plan = read-only)
  LTG_OPENCODE_TIMEOUT seconds per call (default: 180)
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from pydantic import ValidationError


def find_opencode() -> str:
    exe = os.environ.get("LTG_OPENCODE_BIN") or shutil.which("opencode")
    if exe and os.path.exists(exe):
        exe = os.path.abspath(exe)      # calls run in a temporary folder, so a relative path would break
    if not exe:
        sys.exit("The 'opencode' command was not found. Check that `opencode --version` works in this terminal, "
                 "or set LTG_OPENCODE_BIN to its full path.")
    return exe


def _texts_and_tokens(stdout: str):
    """Collect the answer text and token counts from `--format json` events (one JSON object per line)."""
    texts, tin, tout, events = [], 0, 0, 0
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(ev, dict) or "type" not in ev:   # a bare JSON answer is not an event
            continue
        events += 1
        part = ev.get("part") or {}
        if ev.get("type") == "text" and part.get("text"):
            texts.append(part["text"])
        tokens = part.get("tokens") or ev.get("tokens") or {}
        if isinstance(tokens, dict):
            tin += int(tokens.get("input") or 0)
            tout += int(tokens.get("output") or 0)
    if not events:              # older versions print plain text
        texts = [stdout]
    return "\n".join(texts), tin, tout


def _cut_json(text: str) -> str:
    """Remove markdown fences and cut out the outermost {...} object."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in the model's answer.")
    return text[start:end + 1]


def run_once(prompt: str, model: str | None, workdir: Path) -> tuple[str, int, int]:
    prompt_file = workdir / "prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    cmd = [find_opencode(), "run", "--format", "json",
           "--agent", os.environ.get("LTG_OPENCODE_AGENT", "plan"), "-f", str(prompt_file)]
    if model:
        cmd += ["-m", model]
    cmd.append("Follow the instructions in the attached file prompt.txt. Reply with the JSON object only.")
    proc = subprocess.run(cmd, cwd=workdir, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=float(os.environ.get("LTG_OPENCODE_TIMEOUT", "180")))
    if proc.returncode != 0:
        raise RuntimeError(f"opencode exited with code {proc.returncode}: {proc.stderr.strip()[:500]}")
    return _texts_and_tokens(proc.stdout)


def parse(output_model, *, system: str, user_text: str, model: str | None):
    """Return (parsed Pydantic object, response-like object with .choices[0] and .usage)."""
    schema = json.dumps(output_model.model_json_schema())
    base = (f"{system}\n\nDo not use any tools. Do not read, search or edit any files.\n"
            f"Return ONLY one JSON object, no markdown and no explanation, matching this JSON schema:\n{schema}\n\n"
            f"INPUT:\n{user_text}\n")
    prompt, tin_total, tout_total = base, 0, 0
    with tempfile.TemporaryDirectory(prefix="ltg_opencode_") as tmp:
        for attempt in (1, 2):
            text, tin, tout = run_once(prompt, model, Path(tmp))
            tin_total += tin
            tout_total += tout
            try:
                parsed = output_model.model_validate_json(_cut_json(text))
                break
            except (ValueError, ValidationError) as err:
                if attempt == 2:
                    raise RuntimeError(f"OpenCode answer did not match the schema twice: {err}") from err
                prompt = base + f"\nYour previous answer was invalid ({str(err)[:300]}). Return valid JSON only.\n"
    response = SimpleNamespace(
        choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=text))],
        usage=SimpleNamespace(prompt_tokens=tin_total, completion_tokens=tout_total))
    return parsed, response
