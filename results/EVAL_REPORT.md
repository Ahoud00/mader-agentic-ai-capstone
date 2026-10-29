# Evaluation report — A vs B (final run, 2026-10-29)

**Suite:** `evals/tasks.jsonl`, 16 tasks, **team-written on synthetic project data, not official SDAIA tasks.** The same file is used for A and B.
**Configurations:** A = `openai/gpt-4o-mini`, B = `meta-llama/llama-3.3-70b-instruct`. Same harness, prompt (`AGENTS.md`), tools and budgets. **The only change is the model**, so differences are attributed to the model, not to a harness improvement.
**Runs:** k = 3 per task → 48 runs per config. Writes are auto-approved by the evaluator and verified in the MCP alert store.
**Reproduce:** `python -X utf8 evals/run_evals.py --tasks evals/tasks.jsonl --config A B --k 3`
**Files:** `eval_A.csv`, `eval_B.csv`, `eval_summary.csv`, `traces/`, `eval_run_A.log`, `eval_run_B.log`.

> Note on reproducibility: the first B attempt hung on one OpenRouter request (the client had no timeout). It was stopped, `timeout=60s, max_retries=2` was added to the client, and **B was re-run in full**. A's 48 runs come from the run before that change; the timeout only matters when a request hangs.

## Results
| Config | pass rate | pass^3 (all 3 reps) | pass@3 (any rep) | avg LLM requests | avg tokens | total cost | avg latency |
|---|---|---|---|---|---|---|---|
| A gpt-4o-mini | **42/48 = 87.5%** | **14/16** | 14/16 | **1.88** | **2,260** | **$0.0106** | **2.5 s** |
| B llama-3.3-70b | 41/48 = 85.4% | 12/16 | **15/16** | 2.83 | 4,963 | $0.0369 | 5.2 s |

- A is deterministic: its failures are the same two tasks in every rep. B is less consistent (lower pass^3, higher pass@3).
- B uses about 1.5× the requests, 2.2× the tokens, 3.5× the cost, and 2× the latency.
- Run 1 (k=1, `run1_2026-10-29/`) showed B ahead (15/16 vs 14/16). With k=3 the ranking reverses on pass rate, so **a single run per task was misleading**.

## Error analysis (from `traces/`)
| Root cause | Count A | Count B | Example | Fix tried |
|---|---|---|---|---|
| **Answered without calling a tool** (hallucination / prompt contamination) | **6** (T04×3, T06×3) | 0 | T04: A gave a generic definition of "compaction" instead of reading "4000 tokens" from the file. T06: correct email, but taken from `AGENTS.md`, which lists the allowlisted addresses | none in this run (next: force a tool call for factual questions; keep the allowlist out of the prompt) |
| **Retrieval miss** (keyword search) | 0 | **5** (T08×2, T09×3) | B searched `"الاجتماع"` (the note says `اجتماع`), and in T09 searched a transliteration `"mukhatirat al-mashru"`; got "No matches", never fell back to `read_note`, and answered wrongly | none in this run (next: strip the Arabic article "ال", suggest `read_note` on no match) |
| **Repeated identical write → step limit** | 0 | **2** (T12 r0, T13 r0) | B called the same `create_alert` 6 times after `EXECUTED` → 6 duplicate alerts with auto-approve, then `step_limit` | **harness guard added after this run**: an identical write in the same request returns `ALREADY_EXECUTED` (test `identical write repeated in one request runs once`). Live recheck, B on T12/T13 ×3 (`postfix_dup_guard/`): exactly **1 write in all 6 runs**; T12 3/3 pass; T13 1/3 pass because B kept retrying until `MAX_STEPS` stopped it |

**Biggest failure category:** A = under-use of tools (6/6 of its failures). B = retrieval misses (5/7 of its failures).

**What flipped A → B:** T04 and T06 fail→pass (B always calls a tool). T08 and T09 pass→fail (B's search queries miss and it doesn't read the full note). T12 and T13 pass→1 failing rep (duplicate writes).

**Next changes:** require a tool call for factual questions; Arabic-normalised retrieval with a `read_note` fallback; remove literal addresses from `AGENTS.md`. Each should be measured as a separate harness configuration (C) against the same tasks.
