from pathlib import Path

p = Path("backend/agents/research_agent.py")
s = p.read_text(encoding="utf-8")

s = s.replace(
    """r'href=["\\\\\\\\'](https?://[^"\\\\\\\\']+)["\\\\\\\\']',""",
    """r'href=["\\'](https?://[^"\\']+)["\\']',"""
)

p.write_text(s, encoding="utf-8")
print("REGEX FIX APPLIED")
