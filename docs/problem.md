# Problem statement

**On data-centre builds, a late transformer or switchboard delays power-on, and today the warning often comes too late.**

- Long-lead electrical and cooling equipment now takes many months to over two years to arrive (large power transformers: lead times more than doubled since 2019 according to BloombergNEF; switchgear has become a critical-path item).
- Supplier updates arrive as free-text emails with vague or tricky dates: "CW 6", "Q2 2027", "ready for collection at our works", "subject to drawing approval", "partial shipment", "force majeure".
- Procurement and project-controls teams re-type these dates into spreadsheets and compare them with the schedule by hand. Reading "ready at our works in CW 6" as a site date can make an item look safe when it is not.

**LeadTime Guard** reads each supplier update, extracts the promised date with the exact sentence as evidence, converts it into an on-site date with fixed rules, compares it with the required-on-site date and the milestone it feeds, and rates the item green / amber / red with reasons. It drafts a chaser or escalation email, and **a person approves every email** before anything is sent.

**Users:** procurement / expediting manager, project controls / planner, project manager.

**Success measure:** missed risks (an item that is truly amber or red but rated green) - target: at most 1 in about 20 risky items, measured on a synthetic test set with planted traps.
