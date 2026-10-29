import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from agent import resume_agent, run_agent

# إنشاء تطبيق FastAPI
app = FastAPI(title="REFEEQ AI API Server")

# حالات الوكيل المعلقة بانتظار الموافقة البشرية (في الذاكرة)
PENDING: dict[str, dict] = {}


# تعريف بنية البيانات المستقبلة من واجهة streamlit
class CommandRequest(BaseModel):
    command: str


class ApprovalDecision(BaseModel):
    run_id: str
    approved: bool


def _public(state: dict, run_id: str | None = None) -> dict:
    """يعيد للواجهة فقط ما تحتاجه (بدون الرسائل الكاملة أو أي أسرار)."""
    return {
        "status": state["status"],
        "run_id": run_id,
        "response": state["response"],
        "pending": [{"tool": c["name"], "args": c["args"]} for c in state["pending"]],
        "node_flow": state["trace"],
        "tool_calls": state["tool_calls"],
        "steps": state["steps"],
        "llm_calls": state["llm_calls"],
        "cost_usd": round(state["cost"], 6),
    }


@app.get("/")
def read_root():
    return {"status": "online", "message": "REFEEQ API Server is running smoothly"}


# نقطة النهاية المعنية بمعالجة الأوامر عبر الوكيل الحقيقي
@app.post("/process")
def process_command(request: CommandRequest):
    state = run_agent(request.command.strip())
    run_id = None
    if state["status"] == "pending_approval":
        run_id = uuid.uuid4().hex
        PENDING[run_id] = state
    return _public(state, run_id)


# نقطة الموافقة/الرفض البشري لأدوات الكتابة
@app.post("/approve")
def approve(decision: ApprovalDecision):
    state = PENDING.pop(decision.run_id, None)
    if state is None:
        raise HTTPException(404, "unknown or already-decided run_id")
    state = resume_agent(state, decision.approved)
    run_id = None
    if state["status"] == "pending_approval":
        run_id = decision.run_id
        PENDING[run_id] = state
    return _public(state, run_id)


# تشغيل السيرفر محلياً على منفذ 8080
if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8080, reload=False)
