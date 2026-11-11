"""Token and request tracking (reused from the AI Data Room project).

This project runs on FREE tiers (Gemini free tier, Groq free plan, or Ollama locally), so the cost is EUR 0.
We still count tokens and requests: free tiers have daily request limits, and the README reports
"tokens per email", which is what a company would pay for if it moved to a paid tier.
"""


class Usage:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0
        self.by_model = {}

    def add(self, model: str, usage) -> None:
        """`usage` is response.usage from an OpenAI-compatible API (prompt_tokens, completion_tokens)."""
        tin = getattr(usage, "prompt_tokens", 0) or 0
        tout = getattr(usage, "completion_tokens", 0) or 0
        self.input_tokens += tin
        self.output_tokens += tout
        self.calls += 1
        m = self.by_model.setdefault(model, [0, 0])
        m[0] += tin
        m[1] += tout

    def summary(self) -> str:
        return (f"{self.calls} API call(s), {self.input_tokens:,} input + {self.output_tokens:,} output tokens, "
                f"cost EUR 0 (free tier)")
