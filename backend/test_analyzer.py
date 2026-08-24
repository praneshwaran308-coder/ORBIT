from agents.data_analyzer import DataAnalyzer


analyzer = DataAnalyzer()

result = analyzer.analyze(
    "data/test_data.csv"
)

print(result)