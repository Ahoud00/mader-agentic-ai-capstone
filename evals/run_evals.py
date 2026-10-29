"""
تشغيل التقييمات الحقيقية على إعدادين A و B.
A و B = نموذجان مختلفان (MODEL_A / MODEL_B) بنفس الـ harness ونفس tasks.jsonl — الفرق يُنسب للنموذج لا للـ harness.
- أدوات الكتابة: يوافق المُقيّم تلقائيًا ثم يتحقق من ملف التنبيهات المؤقت (لا Mock).
- التصحيح برمجي (بدون LLM judge): contains_any، tool_called، tool_not_called، not_contains (regex)، db (ملف التنبيهات).
الاستخدام:
    python -X utf8 evals/run_evals.py --tasks evals/tasks.jsonl --config A B --k 3
المخرجات: results/eval_A.csv، results/eval_B.csv، results/eval_summary.csv، results/traces/*.json
"""
import argparse
import csv
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
TMP = tempfile.mkdtemp()
ALERTS = os.path.join(TMP, "eval_alerts.jsonl")
os.environ["MADAR_ALERTS_FILE"] = ALERTS              # يُمرَّر لخادم MCP
os.environ["MADAR_COST_LEDGER"] = os.path.join(TMP, "eval_ledger.jsonl")  # التقييم لا يستهلك الميزانية اليومية للتطبيق

import agent  # noqa: E402

CONFIGS = {"A": os.environ.get("MODEL_A", "openai/gpt-4o-mini"),
           "B": os.environ.get("MODEL_B", "meta-llama/llama-3.3-70b-instruct")}
FIELDS = ["config", "model", "task_id", "rep", "passed", "errors", "status", "steps", "llm_calls", "tool_calls",
          "approvals", "prompt_tokens", "completion_tokens", "cost_usd", "elapsed_s", "response"]


def n_alerts():
    return sum(1 for _ in open(ALERTS, encoding="utf-8")) if os.path.exists(ALERTS) else 0


def grade(task, st, written):
    errors = []
    text = st.get("response", "")
    if st["status"] not in ("done",):
        errors.append(f"status:{st['status']}")
    for group in task.get("any_of", []):
        if not any(g.lower() in text.lower() for g in group):
            errors.append(f"missing_answer:{'/'.join(group)}")
    if task.get("tools_any") and not set(task["tools_any"]) & set(st["tool_calls"]):
        errors.append("wrong_or_no_tool")
    if task.get("forbid_regex") and re.search(task["forbid_regex"], text):
        errors.append("hallucinated_pii")
    if task.get("forbid_write") and "create_alert" in st["tool_calls"]:
        errors.append("unrequested_write")
    if task.get("expect_write"):
        if not written:
            errors.append("write_not_executed")
        elif written[-1]["recipient"].lower() != task["recipient"]:
            errors.append(f"wrong_recipient:{written[-1]['recipient']}")
    return errors


def run_task(task, model):
    before = n_alerts()
    st = agent.run_agent(task["query"], model=model)
    approvals = 0
    while st["status"] == "pending_approval":
        approvals += 1
        st = agent.resume_agent(st, approved=True)
    rows = [json.loads(line) for line in open(ALERTS, encoding="utf-8")] if os.path.exists(ALERTS) else []
    return st, rows[before:], approvals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=os.path.join(ROOT, "evals", "tasks.jsonl"))
    ap.add_argument("--config", nargs="+", default=["A", "B"], choices=list(CONFIGS))
    ap.add_argument("--k", type=int, default=1, help="repetitions per task (for pass^k)")
    ap.add_argument("--out", default=os.path.join(ROOT, "results"))
    a = ap.parse_args()

    tasks = [json.loads(line) for line in open(a.tasks, encoding="utf-8") if line.strip()]
    traces = os.path.join(a.out, "traces")
    os.makedirs(traces, exist_ok=True)
    for cfg in a.config:
        model = CONFIGS[cfg]
        path = os.path.join(a.out, f"eval_{cfg}.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for t in tasks:
                for rep in range(a.k):
                    try:
                        st, written, approvals = run_task(t, model)
                        errs = grade(t, st, written)
                    except Exception as e:  # تسجيل الفشل الحقيقي بدل إخفائه
                        st = {"status": "error", "steps": 0, "llm_calls": 0, "tool_calls": [], "prompt_tokens": 0,
                              "completion_tokens": 0, "cost": 0, "elapsed_s": 0, "trace": [], "messages": [],
                              "response": f"{type(e).__name__}: {e}"}
                        errs, approvals = ["runtime_error"], 0
                    w.writerow({"config": cfg, "model": model, "task_id": t["id"], "rep": rep, "passed": not errs,
                                "errors": ";".join(errs), "status": st["status"], "steps": st["steps"],
                                "llm_calls": st["llm_calls"], "tool_calls": "|".join(st["tool_calls"]),
                                "approvals": approvals, "prompt_tokens": st["prompt_tokens"],
                                "completion_tokens": st["completion_tokens"], "cost_usd": round(st["cost"], 6),
                                "elapsed_s": st["elapsed_s"], "response": st["response"].replace("\n", " ")[:300]})
                    f.flush()
                    # trace كامل لكل تشغيل (بدون system prompt لتقليل الحجم)
                    with open(os.path.join(traces, f"{cfg}_{t['id']}_r{rep}.json"), "w", encoding="utf-8") as tf:
                        json.dump({"config": cfg, "model": model, "task": t, "errors": errs,
                                   "trace": st.get("trace", []),
                                   "messages": [m for m in st.get("messages", []) if m.get("role") != "system"]},
                                  tf, ensure_ascii=False, indent=1)
                    print(cfg, t["id"], rep, "PASS" if not errs else "FAIL " + ";".join(errs), flush=True)
        print("wrote", path)
    summarize(a.out, a.config)


def summarize(out, configs):
    rows = []
    for cfg in configs:
        rows += list(csv.DictReader(open(os.path.join(out, f"eval_{cfg}.csv"), encoding="utf-8-sig")))
    summary = []
    for cfg in configs:
        r = [x for x in rows if x["config"] == cfg]
        by_task = {}
        for x in r:
            by_task.setdefault(x["task_id"], []).append(x["passed"] == "True")
        n = len(r)
        summary.append({
            "config": cfg, "model": r[0]["model"], "tasks": len(by_task), "runs": n,
            "pass_rate": round(sum(x["passed"] == "True" for x in r) / n, 4),
            "pass_all_k": f"{sum(all(v) for v in by_task.values())}/{len(by_task)}",
            "pass_any_k": f"{sum(any(v) for v in by_task.values())}/{len(by_task)}",
            "avg_llm_requests": round(sum(int(x["llm_calls"]) for x in r) / n, 3),
            "avg_tokens": round(sum(int(x["prompt_tokens"]) + int(x["completion_tokens"]) for x in r) / n, 1),
            "total_cost_usd": round(sum(float(x["cost_usd"]) for x in r), 5),
            "avg_latency_s": round(sum(float(x["elapsed_s"]) for x in r) / n, 2),
        })
    with open(os.path.join(out, "eval_summary.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
