# Optional: run LeadTime Guard every morning with n8n

`leadtime_guard_daily.json` is an n8n workflow: **Schedule (07:00) → Execute Command (runs the pipeline) → IF any amber/red → notify**.

**Status: example, not part of the tested pipeline.** Import it and test it before you rely on it.

1. Install Node.js, then start n8n on the same Windows laptop as the project: `npx n8n` and open http://localhost:5678.
   (The Execute Command node runs commands on the machine where n8n runs. n8n in Docker cannot see your Windows Python.)
2. Workflows → Import from file → `n8n/leadtime_guard_daily.json`.
3. Change the path in **Run LeadTime Guard** if your project is not in `C:\projects\leadtime-guard`.
4. Newer n8n versions disable the Execute Command node by default for security. If it is missing, enable it as
   described in the n8n documentation (environment variable for allowed nodes), or run the pipeline with Windows Task Scheduler instead.
5. Add a notification node (Teams, Slack or Email) after **Any amber or red?**.

Drafts are never sent by the workflow. A person approves them in the dashboard (`streamlit run app/dashboard.py`).
