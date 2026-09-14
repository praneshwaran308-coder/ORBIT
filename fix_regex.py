from pathlib import Path

p = Path("backend/agents/research_agent.py")
s = p.read_text(encoding="utf-8")

old = r'''r'href=["\\'](https?://[^"\\']+)["\\']','''

new = r'''r"""href=["'](https?://[^"']+)["']","""

count = s.count(old)

if count:
    s = s.replace(old, new)
else:
    # Directly repair the malformed source lines.
    lines = s.splitlines()
    fixed = 0

    for i, line in enumerate(lines):
        if "r'href=["\\\\'](https?://[^"\\\\']+)["\\\\']'" in line:
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = indent + r'''r"""href=["'](https?://[^"']+)["']","""
            fixed += 1

    s = "\n".join(lines) + ("\n" if s.endswith("\n") else "")
    count = fixed

p.write_text(s, encoding="utf-8")

print("FIXED REGEX OCCURRENCES:", count)
