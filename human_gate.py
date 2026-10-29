import os
from pydantic import BaseModel

class ApprovalRequest(BaseModel):
    action_type: str  # نوع الإجراء (مثلاً: إرسال بريد، تعديل ملف)
    details: str      # تفاصيل ما يريد الوكيل كتابته أو تنفيذه
    status: str = "Pending"  # الحالات: Pending, Approved, Denied

def ask_human_for_approval(action_type: str, details: str) -> bool:
    """
    بوابة الموافقة البشرية (Human-in-the-loop Gate)
    تقوم بتعليق عمل الوكيل وعرض تفاصيل الإجراء للمستخدم لطلب الإذن
    """
    print("\n" + "="*40)
    print("🚨 [طلب موافقة بشرية - Human Approval Required] 🚨")
    print(f"نوع الإجراء: {action_type}")
    print(f"التفاصيل: {details}")
    print("="*40)
    
    user_input = input("هل توافق على تنفيذ هذا الإجراء؟ (نعم/لا): ").strip().lower()
    
    if user_input in ['نعم', 'yes', 'y']:
        print("✅ تم منح الموافقة. جاري التنفيذ...")
        return True
    else:
        print("❌ تم رفض الطلب من قبل المستخدم.")
        return False

def run_cli(user_query: str) -> dict:
    """تشغيل الوكيل الحقيقي من الطرفية مع بوابة الموافقة البشرية."""
    from agent import resume_agent, run_agent
    state = run_agent(user_query)
    while state["status"] == "pending_approval":
        call = state["pending"][0]
        approved = ask_human_for_approval(call["name"], str(call["args"]))
        state = resume_agent(state, approved)
    print(state["response"])
    return state


if __name__ == "__main__":
    import sys
    run_cli(" ".join(sys.argv[1:]) or "أنشئ تنبيهًا لنفسي بمراجعة README يوم الخميس")
