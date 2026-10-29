"""
خادم MCP حقيقي (stdio) لأداة التنبيهات التجريبية الخاصة بمدار/رفيق.
يكتب التنبيهات في ملف محلي alerts.jsonl (لا يرسل بريدًا حقيقيًا).
التشغيل يتم تلقائيًا من agent.py عبر MCP stdio client.
"""
import json
import os
import uuid
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

ALERTS_FILE = os.environ.get(
    "MADAR_ALERTS_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "alerts.jsonl"),
)

mcp = FastMCP("madar-alerts")


@mcp.tool()
def create_alert(title: str, message: str, recipient: str = "self", request_id: str = "") -> str:
    """Create a demo alert/reminder (write action). Returns the stored alert id."""
    os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
    # Idempotency: نفس request_id لا يكتب مرتين (حماية من إعادة إرسال الموافقة)
    if request_id and os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                if row.get("request_id") == request_id:
                    return json.dumps({"ok": True, "alert_id": row["id"], "duplicate": True}, ensure_ascii=False)
    alert = {
        "id": uuid.uuid4().hex[:8],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "title": title[:200],
        "message": message[:1000],
        "recipient": recipient[:200],
        "request_id": request_id[:100],
    }
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert, ensure_ascii=False) + "\n")
    return json.dumps({"ok": True, "alert_id": alert["id"]}, ensure_ascii=False)


@mcp.tool()
def list_alerts(limit: int = 10) -> str:
    """List the most recent stored alerts (read-only)."""
    if not os.path.exists(ALERTS_FILE):
        return "[]"
    with open(ALERTS_FILE, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return json.dumps(rows[-limit:], ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
