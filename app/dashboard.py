"""LeadTime Guard dashboard (Streamlit).

    streamlit run app/dashboard.py

Reads the results in outputs/<provider>/ (run the pipeline first). Shows the risk register with colours,
the reasons and evidence for each item, and the draft emails with Approve / Reject buttons.
Decisions are logged in outputs/<provider>/approval_log.csv - nothing is ever sent from here.
"""

import getpass
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
COLOURS = {"RED": "#F8D7DA", "AMBER": "#FFF3CD", "GREEN": "#D4EDDA"}

st.set_page_config(page_title="LeadTime Guard", layout="wide")
st.title("LeadTime Guard")
st.caption("Delivery-risk check for long-lead equipment · FRA-DC1 (fictional data centre) · all data is synthetic")

providers = sorted(p.name for p in OUT.glob("*") if (p / "risk_register.csv").exists()) if OUT.exists() else []
if not providers:
    st.warning("No results yet. Run first:  python -m leadtime_guard.run")
    st.stop()
provider = st.sidebar.selectbox("Extractor", providers, index=providers.index("offline") if "offline" in providers else 0)
d = OUT / provider
reg = pd.read_csv(d / "risk_register.csv", dtype=str).fillna("")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Red", int((reg.rag == "RED").sum()))
c2.metric("Amber", int((reg.rag == "AMBER").sum()))
c3.metric("Green", int((reg.rag == "GREEN").sum()))
c4.metric("Items", len(reg))

st.subheader("Risk register")
show = st.multiselect("Show", ["RED", "AMBER", "GREEN"], default=["RED", "AMBER", "GREEN"])
milestones = st.sidebar.multiselect("Milestone", sorted(reg.milestone.unique()), default=sorted(reg.milestone.unique()))
view = reg[reg.rag.isin(show) & reg.milestone.isin(milestones)]
cols = ["item_id", "description", "milestone", "supplier_says", "on_site_forecast", "ros_date", "float_wd", "rag", "reasons"]
st.dataframe(view[cols].style.apply(lambda r: [f"background-color: {COLOURS.get(r.rag, '')}"] * len(r), axis=1),
             width="stretch", hide_index=True)

st.subheader("Items per milestone")
chart = reg.groupby(["milestone", "rag"]).size().unstack(fill_value=0).reindex(columns=["RED", "AMBER", "GREEN"], fill_value=0)
st.bar_chart(chart, color=["#C83232", "#D68C00", "#228B54"])

st.subheader("Why? Evidence per item")
item = st.selectbox("Item", reg.item_id)
r = reg[reg.item_id == item].iloc[0]
st.markdown(f"**{r.item_id} – {r.description}** · {r.rag}")
st.markdown(f"- Supplier says: `{r.supplier_says or '-'}` (basis: {r.date_basis})\n- On site: {r.on_site_forecast or 'unknown'} "
            f"· needed: {r.ros_date} · float: {r.float_wd or '-'} working days\n- Reasons: {r.reasons}")
st.info(f"Evidence from email {r.email_id or '-'}: “{r.evidence}”")

st.subheader("Draft emails – a person decides")
log_path = d / "approval_log.csv"
log = pd.read_csv(log_path, dtype=str) if log_path.exists() else pd.DataFrame(columns=["item_id", "decision"])
drafts = pd.read_csv(d / "drafts.csv", dtype=str).fillna("") if (d / "drafts.csv").exists() else pd.DataFrame()
for x in drafts.to_dict("records"):
    decided = log[log.item_id == x["item_id"]]
    label = f"{x['item_id']} · {x['kind']} · " + (decided.decision.iloc[-1].upper() if len(decided) else "PENDING")
    with st.expander(label):
        st.text((d / "drafts" / f"{x['item_id']}_{x['kind']}.txt").read_text(encoding="utf-8"))
        a, b = st.columns(2)
        for btn, decision in ((a, "approved"), (b, "rejected")):
            if btn.button(decision.capitalize(), key=f"{x['item_id']}-{decision}"):
                row = pd.DataFrame([{"item_id": x["item_id"], "kind": x["kind"], "decision": decision,
                                     "by": getpass.getuser(), "at": datetime.now().isoformat(timespec="seconds")}])
                row.to_csv(log_path, mode="a", header=not log_path.exists(), index=False)
                st.rerun()
st.caption("Nothing is sent automatically (config: auto_send = false). Approved drafts are sent by a person from Outlook.")
