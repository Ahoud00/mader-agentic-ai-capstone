# Requirements audit vs. SDAIA capstone minimum bar

Source: https://sdaiaacademy.github.io/agentic-ai/ and `labs/capstone` in https://github.com/SDAIAAcademy/agentic-ai (read 2026-10-29).
Track: **1 · Rafeeq in production** (Madar assistant as a service with MCP tools, approvals, security, evals and an API).

| Requirement | Status | Evidence |
|---|---|---|
| 3+ tools, one over MCP | PASS | 3 local tools (`context_tool.py`) + 2 MCP stdio tools (`mcp_alert_server.py`), discovered at runtime via `list_tools` (`agent.mcp_tool_defs`); `results/demo_transcript.md` shows `list_alerts` over MCP |
| Context file | PASS | `my_context.text` (synthetic), read by `read_context` |
| Memory or retrieval | PASS (retrieval) | `search_notes` keyword retrieval over context + `data/notes/`; no cross-session memory (documented) |
| Compaction or budget rule | PASS | `agent._compact` (older tool outputs shrunk above `MAX_CONTEXT_CHARS`), tool output cap 3000 chars; test `context compaction shrinks old tool outputs` |
| Approval on a write action | PASS | `WRITE_TOOLS={"create_alert"}` always pauses; Reject → no write, Approve → exactly one write; re-sent approval, replayed state and identical repeated writes are refused (`tests/test_harness.py` 13/13, `results/demo_transcript.md`, `results/screenshots/`) |
| Step budget | PASS | `MAX_STEPS=6` enforced in `agent._loop` → `step_limit`; tested |
| Cost budget | PASS (fixed today) | `MAX_COST_USD=$0.05`/request and `DAILY_BUDGET_USD=$5`/day enforced before each LLM call via `data/cost_ledger.jsonl`; 2 tests. *Was MISSING before this audit (only in docs).* |
| 15+ eval tasks on two configurations | PASS | 16 tasks in `evals/tasks.jsonl`, same file for A and B; `results/eval_A.csv`, `results/eval_B.csv` |
| Error analysis | PASS | README "Error analysis" + `results/EVAL_REPORT.md` |
| Security note: trifecta, one attack, one defence | PASS | README "Security note", `security/THREAT_MODEL.md`, `security/SECURITY_REPORT.md`, `results/injection_results.csv` |
| Synthetic or public data only | PASS | all data synthetic (`my_context.text` uses `example.com`, notes marked synthetic) |
| README from template with exact course line | PASS | README top |
| Runs with `uv sync`/`uv run` + OpenRouter key | PASS | `pyproject.toml` + `uv.lock`; clean-clone test in README |
| No keys in repository | PASS | `.env` git-ignored; scan in README "Evidence" |
| Run evidence (CSVs, traces, transcript, screenshots) | PASS | `results/eval_*.csv`, `results/traces/`, `results/demo_transcript.md`, `results/screenshots/` |
| Robustness found during audit | FIXED | LLM client had no timeout (a B eval run hung); B looped identical writes (6 duplicate alerts). Both fixed + tested |
| Public GitHub repository | **NOT DONE (by design)** | push not performed in this session; owner must push and set the repo public |
| Official SDAIA eval tasks | N/A | the course asks for your own suite; our 16 tasks are team-written, not official |
