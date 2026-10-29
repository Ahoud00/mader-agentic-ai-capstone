"""إعادة تشغيل استدعاءات create_alert الخبيثة الملتقطة فعليًا (قبل الدفاع) على سياسة الإخراج البرمجية."""
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from security_guard import check_egress_policy  # noqa: E402

rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "injection_results.csv"), encoding="utf-8-sig")))
captured = [a for r in rows if r["defenses"] == "before" and r.get("gate_args") not in (None, "", "[]")
            for a in json.loads(r["gate_args"])]
blocked = 0
for args in captured:
    ok, reason = check_egress_policy("create_alert", args)
    blocked += not ok
    print("BLOCKED" if not ok else "ALLOWED", "->", args["recipient"], "|", reason)
# حالة ضابطة: تنبيه مشروع يجب أن يُسمح به
ok, _ = check_egress_policy("create_alert", {"title": "تذكير", "message": "راجعي README", "recipient": "self"})
print(f"captured malicious calls: {len(captured)}, blocked: {blocked}; benign control allowed: {ok}")
