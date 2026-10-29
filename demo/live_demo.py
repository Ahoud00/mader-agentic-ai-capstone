"""
سيناريو العرض الحي (تشغيل حقيقي عبر OpenRouter + MCP):
  1) سؤال يستدعي أداة MCP (list_alerts)
  2) طلب كتابة create_alert → يتوقف عند البوابة → Reject → التحقق أنه لم يُكتب شيء
  3) نفس الطلب → Approve → التحقق عبر MCP أن التنبيه كُتب مرة واحدة
  4) محاولة Approve ثانية على نفس التشغيل → مرفوضة
يكتب نصًا كاملًا للجلسة في results/demo_transcript.md
التشغيل:  python -X utf8 demo/live_demo.py
"""
import json
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if "--keep" not in sys.argv:  # افتراضيًا: ملف تنبيهات مؤقت حتى لا يتلوث data/
    os.environ["MADAR_ALERTS_FILE"] = os.path.join(tempfile.mkdtemp(), "demo_alerts.jsonl")

import agent  # noqa: E402

LOG = []


def say(line=""):
    print(line, flush=True)
    LOG.append(line)


def alerts_via_mcp():
    return json.loads(agent.mcp_call("list_alerts", {"limit": 50}))


def show(st):
    for t in st["trace"]:
        if "node" in t and t["node"] == "tool":
            say(f"  🔧 tool: `{t['tool']}` args={json.dumps(t['args'], ensure_ascii=False)}")
        elif t.get("event"):
            say(f"  📌 event: {json.dumps(t, ensure_ascii=False)}")
    say(f"  status=`{st['status']}` llm_calls={st['llm_calls']} cost=${st['cost']:.5f}")
    if st["response"]:
        say(f"  🤖 Madar: {st['response']}")


def main():
    say(f"# Live demo transcript — {time.strftime('%Y-%m-%d %H:%M')} — model `{agent.DEFAULT_MODEL}`\n")
    say("## 1) Question answered with an MCP tool")
    q = "ما هي التنبيهات المحفوظة لدي الآن؟"
    say(f"👤 User: {q}")
    show(agent.run_agent(q))

    req = "أنشئ تنبيهًا لنفسي بعنوان 'العرض النهائي' ونصه: تجهيز العرض قبل الخميس"
    say("\n## 2) Write request → Reject")
    say(f"👤 User: {req}")
    before = len(alerts_via_mcp())
    st = agent.run_agent(req)
    show(st)
    say(f"  ⛔ Human gate: pending `{st['pending'][0]['name']}` {json.dumps(st['pending'][0]['args'], ensure_ascii=False)}")
    say(f"  alerts before decision (via MCP list_alerts): {before}")
    st = agent.resume_agent(st, approved=False)
    say("  👤 Decision: **Reject**")
    show(st)
    after_reject = len(alerts_via_mcp())
    say(f"  ✅ proof: alerts after Reject = {after_reject} (unchanged: {after_reject == before})")

    say("\n## 3) Same request → Approve")
    say(f"👤 User: {req}")
    st = agent.run_agent(req)
    show(st)
    st = agent.resume_agent(st, approved=True)
    say("  👤 Decision: **Approve**")
    show(st)
    rows = alerts_via_mcp()
    say(f"  ✅ proof: alerts after Approve = {len(rows)} (exactly +1: {len(rows) == before + 1})")
    if rows:
        say(f"  last alert (via MCP): {json.dumps(rows[-1], ensure_ascii=False)}")

    say("\n## 4) Re-sending the approval")
    try:
        agent.resume_agent(st, approved=True)
        say("  ❌ second approval was accepted")
    except ValueError as e:
        say(f"  ✅ second approval refused: {e}; alerts still = {len(alerts_via_mcp())}")

    out = os.path.join(ROOT, "results", "demo_transcript.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
