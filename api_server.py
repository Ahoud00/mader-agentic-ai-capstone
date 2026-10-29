import streamlit as st
import os
import json
from agent import resume_agent, run_agent

# 1. إعداد الصفحة وتأصيل نمط الخلفية السائلة المتداخلة والتصميم الحر (Borderless Liquid Neon UI)
st.set_page_config(page_title="REFEEQ | Real Graph Workflow", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    /* بناء خلفية سائلة فخمة متداخلة الألوان لتعطي روقان مذهل */
    .stApp, body, [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        background: linear-gradient(135deg, #040306 0%, #0A0714 45%, #050716 85%, #020204 100%) !important;
        color: #E2E2E8 !important;
        background-attachment: fixed !important;
    }
    
    /* الحقن القسري الصارم لتحويل خلفية حقل المحادثة البيضاء تماماً إلى الأسود الملكي المطفي وإلغاء البياض */
    div[data-testid="stChatMessageContainer"], 
    .stChatInputContainer, 
    div[data-testid="stChatInput"],
    [data-testid="stForm"],
    .stChatInputContainer textarea {
        background-color: #0A0A0F !important;
        background: #0A0A0F !important;
        border: 1px solid rgba(255, 215, 0, 0.2) !important;
        box-shadow: none !important;
    }
    
    /* تعديل لون نصوص المدخلات والرسائل داخل الشات لتظهر بنقاء ناصع فوق السواد */
    .stChatInputContainer textarea, 
    div[data-testid="stChatMessage"] p, 
    .stMarkdown,
    div[data-testid="stChatInput"] textarea {
        color: #E2E2E8 !important;
        -webkit-text-fill-color: #E2E2E8 !important;
    }
    
    /* تصميم العناوين بشكل حر ونقي تماماً متناسب مع الألوان المتوهجة */
    h1, h2, h3, .stTitle {
        color: #FFD700 !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 200 !important;
        letter-spacing: -0.5px !important;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.4) !important;
    }
    
    /* دمج صورتكِ ثلاثية الأبعاد بشكل حر تماماً وبدون أي إطار لتبدو عائمة بنقاء */
    img {
        border-radius: 12px !important;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.15) !important;
        mix-blend-mode: lighten !important; /* دمج مثالي مع السواد الخلفي لتبدو عائمة */
    }
    
    /* إزالة كافة الإطارات والمربعات الصندوقية لتكون العناصر حرة وعائمة */
    .stChatMessage, .stAlert, div[data-testid="stVerticalBlock"] > div {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 12px 0px !important;
    }
    
    /* شريط تتبع عقد الـ Graph العلوي عائم وحر بنصوص بيضاء مضيئة ناعمة */
    .graph-node-free {
        text-align: center;
        font-size: 0.95rem;
        color: #FFD700;
        font-weight: bold;
        padding: 10px !important;
        text-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
    }
    
    /* تخصيص أزرار الدخول والتفاعل */
    div.stButton > button {
        background-color: transparent !important;
        color: #FFD700 !important;
        border: 1px solid rgba(255, 215, 0, 0.5) !important;
        border-radius: 24px !important; 
        font-size: 1.1rem !important;
        padding: 10px 36px !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background-color: #FFD700 !important;
        color: #040306 !important;
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.6) !important;
        border: 1px solid #FFD700 !important;
    }
    </style>
""", unsafe_allow_html=True)

# إدارة حالة التنقل والصفحات
if "page" not in st.session_state:
    st.session_state.page = "LANDING"

# ==========================================
# 🌌 الشاشة الأولى: صفحة الهبوط الترحيبية بصورتكِ الذهبية الفخمة المحدّثة
# ==========================================
if st.session_state.page == "LANDING":
    st.markdown("<br><h1 style='text-align: center; font-size: 3.5rem;'>REFEEQ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1rem; color: #888; font-weight: 300;'>INTEGRATED AGENTIC GRAPH WORKFLOW</p>", unsafe_allow_html=True)
    
    # خدعة كسر الكاش البرمجية الصارمة بقراءة الصورة المحلية وإلحاق معرّف التحديث الإجباري لإجبار المتصفح على عرضها
    if os.path.exists("dashbord.png"):
        st.image("dashbord.png?v=2", use_container_width=True)
    else:
        st.warning("⏳ يرجى التأكد من وجود ملف الصورة داخل مجلد الـ VS Code باسم dashbord.png")
        
    st.markdown("<p style='text-align: center; color: rgba(255,215,0,0.4); font-size: 0.8rem; letter-spacing: 2px;'>SYSTEM ARCHITECTURE INITIALIZED</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_btn_center, _ = st.columns(2)
    with col_btn_center:
        if st.button("🚀 Enter Workspace", use_container_width=True):
            st.session_state.page = "APPLICATION"
            st.rerun()

# ==========================================
# ⚙️ الشاشة الثانية: شاشة الاستعمال والـ Graph (Borderless App)
# ==========================================
elif st.session_state.page == "APPLICATION":
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; font-weight: 200;'>📊 INTEG. DASHBOARD</h2>", unsafe_allow_html=True)
        st.markdown("---")
        st.metric(label="💰 ميزانية استهلاك الوكيل", value="$5.00 / Daily Max")
        st.metric(label="🧠 قاعدة تقليص الذاكرة", value="4000 Tokens")
        st.markdown("---")
        if st.button("⬅️ العودة للرئيسية", use_container_width=True):
            st.session_state.page = "LANDING"
            st.rerun()

    st.markdown("<h1 style='text-align: center; font-weight: 200;'>REFEEQ | بوابتك التنفيذية</h1>", unsafe_allow_html=True)
    st.caption("<p style='text-align: center; color: #888;'>أرسل أوامرك لـ 'مدار' لمسح مستنداتك أو تفعيل تنبيهات بروتوكول MCP</p>", unsafe_allow_html=True)
    st.markdown("---")

    col_n1, col_n2, col_n3 = st.columns(3)
    with col_n1:
        st.markdown("<div class='graph-node-free'>🛡️ Node 1:<br>Security Guard</div>", unsafe_allow_html=True)
    with col_n2:
        st.markdown("<div class='graph-node-free'>🧠 Node 2:<br>Reasoning Loop</div>", unsafe_allow_html=True)
    with col_n3:
        st.markdown("<div class='graph-node-free'>⚙️ Node 3:<br>Execution Hub</div>", unsafe_allow_html=True)
    st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_alert" not in st.session_state:
        st.session_state.pending_alert = None

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    def _final_text(state):
        """نص الرد النهائي — النجاح يظهر فقط إذا نُفذ الإجراء فعليًا عبر MCP."""
        lines = []
        for t in state["trace"]:
            if t.get("event") == "human_approved":
                lines.append(f"✅ تم التنفيذ فعليًا عبر MCP: {t['result']}" if t["executed"]
                             else f"❌ فشل التنفيذ: {t['result']}")
            elif t.get("event") == "human_rejected":
                lines.append("🛑 تم رفض الإجراء ولم يُنفذ أي تغيير.")
            elif t.get("event") == "egress_blocked_after_approval":
                lines.append(f"🛡️ حُجب الإجراء رغم الموافقة (سياسة منع التسريب): {t['reason']}")
        if state["status"] != "pending_approval":
            lines.append(state["response"])
        return (chr(10) * 2).join(lines)

    if user_query := st.chat_input("بماذا يمكنني مساعدتك اليوم في جدولك ومهامك؟"):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.spinner("⛓️ جاري تمرير الطلب عبر الـ Graph Nodes..."):
            state = run_agent(user_query)
            if state["status"] == "pending_approval":
                st.session_state.pending_alert = state
                st.rerun()
            else:
                response_content = _final_text(state)
                st.session_state.messages.append({"role": "assistant", "content": response_content})
                with st.chat_message("assistant"):
                    st.markdown(response_content)

    if st.session_state.pending_alert:
        call = st.session_state.pending_alert["pending"][0]
        st.warning("⛓️ **[Graph Node: Human Approval Gate]** تم تعليق المسار بانتظار موافقتك — لم يُنفذ شيء بعد.")
        st.info(f"📝 **الأداة:** {call['name']} — **المدخلات:** {call['args']}")

        decision = None
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ موافقة وتمرير في الـ Graph", use_container_width=True):
                decision = True
        with col2:
            if st.button("❌ رفض وحظر المسار", use_container_width=True):
                decision = False
        if decision is not None:
            state = resume_agent(st.session_state.pending_alert, decision)
            st.session_state.pending_alert = state if state["status"] == "pending_approval" else None
            if state["status"] != "pending_approval":
                st.session_state.messages.append({"role": "assistant", "content": _final_text(state)})
            st.rerun()
