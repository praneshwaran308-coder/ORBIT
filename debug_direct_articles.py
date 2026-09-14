import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from backend.agents.research_agent import ResearchAgent

agent = ResearchAgent()

tests = [
    (
        "Capitol News Illinois",
        "Pritzker signs landmark AI regulation bill that aims to mitigate risks",
        "https://capitolnewsillinois.com/news/pritzker-signs-landmark-ai-regulation-bill-that-aims-to-mitigate-risks/",
    ),
    (
        "Nature",
        "Let 2026 be the year the world comes together for AI safety",
        "https://doi.org/10.1038/d41586-025-04106-0",
    ),
    (
        "WTTW News",
        "Pritzker Signs Landmark AI Regulation Bill That Aims to Mitigate Risks",
        "https://news.wttw.com/2026/07/06/pritzker-signs-landmark-ai-regulation-bill-aims-mitigate-risks",
    ),
]

for source, title, url in tests:
    print("\n" + "=" * 80)
    print(source)
    print("URL:", url)
    print("=" * 80)

    try:
        article = agent.fetch_article(url)

        print("ARTICLE LENGTH:", len(article or ""))
        print("TITLE MATCH:", agent.article_matches_source(
            article or "",
            title,
            source,
        ))

        if article:
            print("PREVIEW:", article[:300].replace("\n", " "))

    except Exception as e:
        print("ERROR:", type(e).__name__, str(e))
