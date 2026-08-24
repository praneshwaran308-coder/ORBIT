import asyncio

from agents.data_agent import DataAgent


async def main():
    agent = DataAgent()

    result = await agent.run(
        "Analyze this dataset and give me useful insights",
        "data/test_data.csv"
    )

    print("\nSTATUS:", result.get("status"))
    print("HAS_INSIGHTS:", "insights" in result)
    print("ERROR:", result.get("result", "None"))

    if "insights" in result:
        print("\n--- INSIGHTS ---")
        print(result["insights"])


if __name__ == "__main__":
    asyncio.run(main())