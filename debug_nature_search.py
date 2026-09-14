from pathlib import Path
import requests

title = "Let 2026 be the year the world comes together for AI safety"

r = requests.get(
    "https://www.google.com/search",
    params={"q": f'"{title}" site:nature.com', "num": 10},
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/142.0 Safari/537.36"
        )
    },
    timeout=8,
)

print("STATUS:", r.status_code)
print("LENGTH:", len(r.text))

import re

links = re.findall(
    r"""href=["'](https?://[^"']+)["']""",
    r.text,
    flags=re.I,
)

for x in links[:30]:
    print(x)
