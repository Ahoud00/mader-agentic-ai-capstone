import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTEXT_FILE = os.path.join(BASE_DIR, "my_context.text")
NOTES_DIR = os.path.join(BASE_DIR, "data", "notes")
MAX_TOOL_CHARS = 3000  # حد حجم مخرجات الأداة لإدارة السياق


def _read(path: str) -> str:
    # قراءة الملف بطريقة ثنائية آمنة تمنع أخطاء التشفير
    with open(path, "rb") as f:
        return f.read().decode("utf-8", errors="ignore")


def read_context_file(query: str = "") -> str:
    """أداة قراءة ملف السياق المحلي للمستخدم (قراءة فقط)."""
    if not os.path.exists(CONTEXT_FILE):
        return "ERROR: context file my_context.text not found."
    content = _read(CONTEXT_FILE).strip()
    if not content:
        return "Context file is empty."
    return content[:MAX_TOOL_CHARS]


def search_notes(query: str) -> str:
    """أداة استرجاع: بحث بالكلمات داخل ملف السياق وملاحظات data/notes (قراءة فقط)."""
    terms = [t for t in query.lower().split() if len(t) > 1]
    if not terms:
        return "No search terms given."
    sources = [CONTEXT_FILE] + sorted(glob.glob(os.path.join(NOTES_DIR, "*.md")))
    hits = []
    for path in sources:
        if not os.path.exists(path):
            continue
        name = os.path.relpath(path, BASE_DIR).replace("\\", "/")
        lines = _read(path).splitlines()
        for i, line in enumerate(lines):
            low = line.lower()
            if any(t in low for t in terms):
                hits.append(f"[{name}:{i + 1}] {line.strip()}")
    if not hits:
        return f"No matches for: {query}"
    return "\n".join(hits)[:MAX_TOOL_CHARS]


def read_note(name: str) -> str:
    """أداة قراءة ملاحظة كاملة من data/notes (قراءة فقط، داخل المجلد فقط)."""
    path = os.path.realpath(os.path.join(NOTES_DIR, os.path.basename(name)))
    if not path.startswith(os.path.realpath(NOTES_DIR)) or not os.path.exists(path):
        available = [os.path.basename(p) for p in glob.glob(os.path.join(NOTES_DIR, "*.md"))]
        return f"ERROR: note not found. Available notes: {available}"
    return _read(path)[:MAX_TOOL_CHARS]
