import asyncio
from backend.agents.research_agent import ResearchAgent

async def main():
    agent = ResearchAgent()

    print("=" * 80)
    print("ORBIT RESEARCH PIPELINE TEST")
    print("=" * 80)

    try:
        result = await agent.run("AI safety and regulation")

        print("RESULT TYPE:", type(result).__name__)

        if isinstance(result, dict):
            print("STATUS:", result.get("status"))
            print("SOURCES:", len(result.get("sources", [])))
            print("FINDINGS:", len(result.get("findings", [])))
            print("EVIDENCE:", len(result.get("evidence", [])))

            print("\nSOURCE DETAILS:")
            for i, source in enumerate(result.get("sources", []), 1):
                print(
                    f"[{i}]",
                    source.get("source", source.get("title", "")),
                    "| valid=", source.get("valid"),
                    "| available=", source.get("available"),
                    "| url=", source.get("url", ""),
                )

            print("\nFINDINGS:")
            for i, finding in enumerate(result.get("findings", []), 1):
                print(f"[{i}]", finding)

            print("\nERROR:", result.get("error"))

        else:
            print(result)

    except Exception as e:
        print("PIPELINE ERROR:", type(e).__name__, str(e))

if __name__ == "__main__":
    asyncio.run(main())
