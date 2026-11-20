# Running LeadTime Guard on your own hardware (on-premise / local model)

Supplier emails contain prices, delivery dates, penalties and contract terms. Under GDPR and typical customer and supplier contracts, many European companies are not allowed to send this text to a public AI API. LeadTime Guard therefore supports **local models**: the language model runs on a laptop or server you control, and **no email text leaves your network**.

Everything else in the pipeline (date rules, risk rules, Excel report, draft emails, approval log, dashboard) is plain Python and already runs locally.

---

## Option A – your own laptop (Ollama, free)

1. Install **Ollama** from [ollama.com](https://ollama.com) (Windows, macOS or Linux).
2. Download an open model once (about 5 GB):
   ```
   ollama pull qwen2.5:7b
   ```
   `llama3.1:8b` also works. Both support the JSON output mode LeadTime Guard uses.
3. Run the pipeline and the evaluation against it:
   ```
   python -m leadtime_guard.run --provider ollama
   python -m leadtime_guard.evaluate --provider ollama
   ```
   No API key is needed. After the model download you can switch off the internet: the run still works, which is an easy way to prove that nothing is sent outside.

To use a different model: `set LTG_MODEL=llama3.1:8b` (Windows) or `export LTG_MODEL=llama3.1:8b` (Linux/macOS).

## Option B – a shared company server (Ollama)

1. On the server (Linux with a GPU is ideal), install Ollama and pull the model as above.
2. Let Ollama listen on the internal network, not only on localhost: start it with `OLLAMA_HOST=0.0.0.0` (for the systemd service, add `Environment="OLLAMA_HOST=0.0.0.0"`).
3. **Security:** Ollama has no login of its own. Only expose port 11434 inside the company network or VPN (firewall rule), or put it behind a reverse proxy with authentication.
4. On each user's machine, point LeadTime Guard to the server:
   ```
   set OLLAMA_BASE_URL=http://ai-server.internal:11434/v1
   set LTG_MODEL=qwen2.5:7b
   python -m leadtime_guard.run --provider ollama
   ```

## Option C – any other OpenAI-compatible server (vLLM, LM Studio, llama.cpp)

Many teams already run an internal model server with an OpenAI-compatible API (for example **vLLM** on a GPU server, or **LM Studio** on a desktop). Use the `local` provider:
```
set LTG_BASE_URL=http://localhost:8000/v1
set LTG_MODEL=Qwen/Qwen2.5-7B-Instruct
set LTG_API_KEY=your-internal-key        (only if your server requires one)
python -m leadtime_guard.run --provider local
```
The same works for an **EU-hosted** private endpoint (for example a model deployed in an EU cloud region under a data processing agreement).

---

## Hardware and speed (rough guide)

| Setup | What to expect |
|---|---|
| Laptop, 16 GB RAM, no GPU, 7–8B model | works; roughly 10–60 seconds per email |
| Desktop / server with a mid-range GPU (8–16 GB VRAM) | a few seconds per email |
| Larger models (14B+) | better reading of tricky emails, needs more memory |

Local calls have no rate limit, so the pipeline does not wait between emails (it does for the free cloud tiers).

## Check accuracy before relying on it

The published results in the README were measured with Gemini. A smaller local model may read some dates differently. Always run:
```
python -m leadtime_guard.evaluate --provider ollama
```
and compare with the README table. Use the local model only if it keeps the **missed-risk rate** at or below your target (this project uses at most 1 in about 20). Every value still has to pass the evidence check, and anything unclear is flagged amber for a person, never guessed.

## Data-protection checklist for a real pilot

- [ ] Test with the synthetic emails first, then with a small set of real emails.
- [ ] The model runs on your hardware (`ollama` or `local`); no cloud provider is configured.
- [ ] `outputs/` (extractions, reports, drafts, approval log) is stored on a protected drive with access limited to the project team.
- [ ] Use the dashboard locally (`streamlit run app/dashboard.py`), not the public Streamlit Cloud demo, for real data.
- [ ] Agree a retention period for extracted data and delete old outputs.
- [ ] Ask your data protection officer to confirm the setup; if a third party hosts the model, a data processing agreement is needed.

The only internet access needed is for installing Python packages and downloading the model once.
