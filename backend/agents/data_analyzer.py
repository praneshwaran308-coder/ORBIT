import pandas as pd


class DataAnalyzer:

    def analyze(self, file_path: str) -> dict:
        """
        Analyze a CSV dataset and return structured information.
        """

        df = pd.read_csv(file_path)

        numeric_columns = df.select_dtypes(
            include="number"
        ).columns.tolist()

        analysis = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_types": {
                column: str(dtype)
                for column, dtype in df.dtypes.items()
            },
            "missing_values": {
                column: int(value)
                for column, value in df.isnull().sum().items()
            },
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_summary": {},
            "insights": []
        }

        for column in numeric_columns:
            values = df[column]
            standard_deviation = values.std()

            analysis["numeric_summary"][column] = {
                "mean": float(values.mean()),
                "median": float(values.median()),
                "minimum": float(values.min()),
                "maximum": float(values.max()),
                "std": (
                    float(standard_deviation)
                    if pd.notna(standard_deviation)
                    else None
                )
            }

        if len(numeric_columns) >= 2:
            correlation = df[numeric_columns].corr()

            analysis["correlations"] = {
                column: {
                    other_column: float(
                        correlation.loc[column, other_column]
                    )
                    for other_column in numeric_columns
                }
                for column in numeric_columns
            }
        else:
            analysis["correlations"] = {}

        non_numeric_count = len(df.columns) - len(numeric_columns)

        analysis["insights"].append(
            "Dataset contains "
            f"{len(df)} row(s) and {len(df.columns)} column(s) "
            f"({len(numeric_columns)} numeric, "
            f"{non_numeric_count} non-numeric)."
        )

        missing_columns = [
            (column, count)
            for column, count in analysis["missing_values"].items()
            if count > 0
        ]

        if missing_columns:
            missing_details = ", ".join(
                f"{column} ({count})"
                for column, count in missing_columns[:3]
            )

            analysis["insights"].append(
                "Missing values detected in: "
                f"{missing_details}."
            )

        if analysis["duplicate_rows"]:
            analysis["insights"].append(
                f"Found {analysis['duplicate_rows']} duplicate row(s)."
            )

        variability = [
            (column, values["std"])
            for column, values in analysis["numeric_summary"].items()
            if values["std"] is not None
        ]

        if variability:
            column, standard_deviation = max(
                variability,
                key=lambda item: item[1]
            )

            analysis["insights"].append(
                f"'{column}' has the highest variability "
                f"(standard deviation {standard_deviation:.2f})."
            )

        correlation_pairs = []

        for column, values in analysis["correlations"].items():
            for other_column, value in values.items():
                if column >= other_column or not pd.notna(value):
                    continue

                if abs(value) >= 0.7:
                    correlation_pairs.append(
                        (abs(value), column, other_column, value)
                    )

        if correlation_pairs:
            _, column, other_column, value = max(correlation_pairs)
            direction = "positive" if value > 0 else "negative"

            analysis["insights"].append(
                f"Strong {direction} correlation between "
                f"'{column}' and '{other_column}' (r={value:.2f})."
            )

        return analysis
