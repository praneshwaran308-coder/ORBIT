import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from backend.agents.research_agent import ResearchAgent

agent = ResearchAgent()

tests = [
    (
        "Nature",
        "Let 2026 be the year the world comes together for AI safety",
        "https://www.nature.com",
    ),
    (
        "SiliconANGLE",
        "AI researchers call for new tools that can slow automated model development",
        "https://siliconangle.com",
    ),
]

for source, title, source_url in tests:
    print("\n" + "=" * 80)
    print("SOURCE:", source)
    print("TITLE:", title)
    print("=" * 80)

    try:
        url = agent.find_publisher_article(
            title,
            source,
            source_url,
        )

        print("RESOLVED:", url or "<none>")

        if url:
            article = agent.fetch_article(url)
            print("ARTICLE LENGTH:", len(article or ""))
            print(
                "TITLE MATCH:",
                agent.article_matches_source(
                    article or "",
                    title,
                    source,
                ),
            )

    except Exception as e:
        print("ERROR:", type(e).__name__, str(e))
