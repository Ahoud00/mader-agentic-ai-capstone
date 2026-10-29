# Live demo scenario (≈3 minutes) + 8-minute talk outline

> According to the course page, the README is the official presentation (no live demo is required). This file is for an optional oral walkthrough.

## Live demo: question → MCP tool → write request → Reject → Approve → proof

**Option 1: one command (recommended, real model, transcript saved automatically):**
```powershell
python -X utf8 demo\live_demo.py
```
Prints the steps and saves them to `results\demo_transcript.md`:
1. "ما هي التنبيهات المحفوظة لدي الآن؟" → the agent calls `list_alerts` **over MCP**.
2. "أنشئ تنبيهًا لنفسي بعنوان 'العرض النهائي'…" → it stops at the gate (`pending_approval`) → **Reject** → the alert count is unchanged (proof via MCP).
3. Same request → **Approve** → the count goes up by exactly 1, and the alert is shown as read back over MCP.
4. Re-sending the approval → refused (`No pending action`).

**Option 2: the UI:** `streamlit run app.py` → Enter Workspace → type the request → 🚀 → the gate shows `create_alert(...)` → Reject/Approve. Proof: open `data\alerts.jsonl`. Saved screenshots: `results\screenshots\`.

## Talk outline (8 minutes)
| Time | Content |
|---|---|
| 0:00–0:45 | Problem: an assistant that reads the user's context and creates alerts, but never writes without permission |
| 0:45–2:00 | Design across the ladder: prompt (AGENTS.md) → context (retrieval + compaction) → harness (approval, step and cost budgets, egress policy) → loop (tool loop) → no graph needed |
| 2:00–4:30 | Live demo (above) |
| 4:30–5:45 | A/B: two different models on the same 16 tasks (numbers in README). The difference comes from the model, not the harness |
| 5:45–7:15 | Security: trifecta → stealth attack leaked 4/5 before the defences, 0/5 after; Approve cannot bypass the policy |
| 7:15–8:00 | Limitations: the 16 tasks are team-written, not official; small samples; keyword retrieval |
