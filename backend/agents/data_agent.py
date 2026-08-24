import os
import json

from dotenv import load_dotenv
from google import genai

from .base_agent import BaseAgent
from .data_analyzer import DataAnalyzer


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# GEMINI
# ============================================================

ENABLE_GEMINI = (
    os.getenv(
        "ORBIT_ENABLE_GEMINI",
        "false"
    ).lower()
    == "true"
)


# ============================================================
# DATA AGENT
# ============================================================

class DataAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            "Data Agent"
        )

        self.analyzer = DataAnalyzer()

        self.client = None

        if ENABLE_GEMINI:

            api_key = os.getenv(
                "GEMINI_API_KEY"
            )

            if api_key:

                self.client = genai.Client(
                    api_key=api_key
                )


    # ========================================================
    # NORMALIZE ANALYSIS
    # ========================================================

    def normalize_analysis(
        self,
        analysis: dict
    ) -> dict:

        """
        Convert the DataAnalyzer output into the
        stable structure expected by the ORBIT frontend.

        This handles both:

        1. New nested analyzer output
        2. Older/top-level analyzer output
        """

        # ----------------------------------------------------
        # Existing nested dataset
        # ----------------------------------------------------

        existing_dataset = analysis.get(
            "dataset"
        )

        if isinstance(
            existing_dataset,
            dict
        ):

            dataset = existing_dataset.copy()

        else:

            dataset = {}


        # ====================================================
        # DATASET OVERVIEW
        # ====================================================

        dataset_overview = (
            dataset.get(
                "dataset_overview"
            )
            if isinstance(
                dataset.get(
                    "dataset_overview"
                ),
                dict
            )
            else {}
        )


        rows = (
            dataset_overview.get(
                "rows"
            )
            if dataset_overview.get(
                "rows"
            ) is not None
            else analysis.get(
                "rows"
            )
        )


        columns = (
            dataset_overview.get(
                "columns"
            )
            if dataset_overview.get(
                "columns"
            ) is not None
            else analysis.get(
                "columns"
            )
        )


        column_names = (
            dataset_overview.get(
                "column_names"
            )
            if dataset_overview.get(
                "column_names"
            ) is not None
            else analysis.get(
                "column_names",
                []
            )
        )


        dataset_overview = {

            "rows":
                rows if rows is not None else 0,

            "columns":
                columns if columns is not None else 0,

            "column_names":
                column_names or []
        }


        # ====================================================
        # DATA TYPES
        # ====================================================

        column_types = dataset.get(
            "column_types"
        )

        if not isinstance(
            column_types,
            dict
        ):

            column_types = {}


        # ----------------------------------------------------
        # If column_types is missing, build it from
        # DataAnalyzer's data_types.
        # ----------------------------------------------------

        if (
            not column_types.get(
                "numeric"
            )
            and
            not column_types.get(
                "categorical"
            )
        ):

            data_types = analysis.get(
                "data_types",
                {}
            )

            numeric = []
            categorical = []


            if isinstance(
                data_types,
                dict
            ):

                for column, dtype in (
                    data_types.items()
                ):

                    dtype_text = str(
                        dtype
                    ).lower()


                    if any(
                        numeric_type
                        in dtype_text
                        for numeric_type in [
                            "int",
                            "float",
                            "double",
                            "number"
                        ]
                    ):

                        numeric.append(
                            column
                        )

                    else:

                        categorical.append(
                            column
                        )


            column_types = {

                "numeric":
                    numeric,

                "categorical":
                    categorical
            }


        else:

            column_types = {

                "numeric":
                    column_types.get(
                        "numeric",
                        []
                    ),

                "categorical":
                    column_types.get(
                        "categorical",
                        []
                    )
            }


        # ====================================================
        # STATISTICS
        # ====================================================

        statistics = dataset.get(
            "statistics"
        )

        if not isinstance(
            statistics,
            dict
        ):

            statistics = {}


        # ----------------------------------------------------
        # Convert numeric_summary into the frontend format
        # ----------------------------------------------------

        if not statistics:

            numeric_summary = analysis.get(
                "numeric_summary",
                {}
            )

            if isinstance(
                numeric_summary,
                dict
            ):

                for column, values in (
                    numeric_summary.items()
                ):

                    if not isinstance(
                        values,
                        dict
                    ):

                        continue


                    statistics[column] = {

                        "mean":
                            values.get(
                                "mean"
                            ),

                        "median":
                            values.get(
                                "median"
                            ),

                        "minimum":
                            values.get(
                                "minimum"
                            ),

                        "maximum":
                            values.get(
                                "maximum"
                            ),

                        "std":
                            values.get(
                                "std"
                            )
                    }


        # ====================================================
        # MISSING VALUES
        # ====================================================

        missing_values = dataset.get(
            "missing_values"
        )

        if not isinstance(
            missing_values,
            dict
        ):

            missing_values = {}


        # ----------------------------------------------------
        # Fall back to analyzer's top-level missing values
        # ----------------------------------------------------

        if not missing_values:

            raw_missing = analysis.get(
                "missing_values",
                {}
            )

            if isinstance(
                raw_missing,
                dict
            ):

                missing_values = {

                    str(column):
                        int(value or 0)

                    for column, value
                    in raw_missing.items()
                }


        # ====================================================
        # DUPLICATES
        # ====================================================

        duplicate_rows = dataset.get(
            "duplicate_rows"
        )

        if duplicate_rows is None:

            duplicate_rows = analysis.get(
                "duplicate_rows",
                0
            )


        try:

            duplicate_rows = int(
                duplicate_rows or 0
            )

        except (
            TypeError,
            ValueError
        ):

            duplicate_rows = 0


        # ====================================================
        # CORRELATIONS
        # ====================================================

        correlations = dataset.get(
            "correlations"
        )

        if not isinstance(
            correlations,
            dict
        ):

            correlations = {}


        # ----------------------------------------------------
        # Existing analyzer correlation format:
        #
        # {
        #   "age": {
        #       "age": 1.0,
        #       "salary": 1.0
        #   }
        # }
        #
        # Frontend wants:
        #
        # {
        #   "age vs salary": 1.0
        # }
        # ----------------------------------------------------

        if not correlations:

            raw_correlations = analysis.get(
                "correlations",
                {}
            )

            if isinstance(
                raw_correlations,
                dict
            ):

                # --------------------------------------------
                # Detect matrix format
                # --------------------------------------------

                matrix_format = any(
                    isinstance(
                        value,
                        dict
                    )
                    for value
                    in raw_correlations.values()
                )


                if matrix_format:

                    converted = {}

                    for column_a, row in (
                        raw_correlations.items()
                    ):

                        if not isinstance(
                            row,
                            dict
                        ):

                            continue


                        for column_b, value in (
                            row.items()
                        ):

                            if column_a == column_b:

                                continue


                            try:

                                numeric_value = float(
                                    value
                                )

                            except (
                                TypeError,
                                ValueError
                            ):

                                continue


                            pair = (
                                f"{column_a} vs {column_b}"
                            )


                            reverse_pair = (
                                f"{column_b} vs {column_a}"
                            )


                            if (
                                reverse_pair
                                not in converted
                                and
                                pair
                                not in converted
                            ):

                                converted[pair] = (
                                    numeric_value
                                )


                    correlations = converted


                else:

                    # Already in frontend format
                    correlations = {

                        str(key):
                            value

                        for key, value
                        in raw_correlations.items()
                    }


        # ====================================================
        # INSIGHTS
        # ====================================================

        insights = dataset.get(
            "insights"
        )

        if not isinstance(
            insights,
            list
        ):

            insights = []


        # ----------------------------------------------------
        # Fall back to top-level insights
        # ----------------------------------------------------

        if not insights:

            raw_insights = analysis.get(
                "insights",
                []
            )

            if isinstance(
                raw_insights,
                list
            ):

                insights = raw_insights


        # ====================================================
        # ML RECOMMENDATION
        # ====================================================

        ml_recommendation = dataset.get(
            "ml_recommendation"
        )

        if not isinstance(
            ml_recommendation,
            dict
        ):

            ml_recommendation = (
                analysis.get(
                    "ml_recommendation"
                )
            )


        if not isinstance(
            ml_recommendation,
            dict
        ):

            ml_recommendation = {}


        # ====================================================
        # FINAL NORMALIZED DATASET
        # ====================================================

        normalized_dataset = {

            "dataset_overview":
                dataset_overview,

            "column_types":
                column_types,

            "missing_values":
                missing_values,

            "duplicate_rows":
                duplicate_rows,

            "statistics":
                statistics,

            "correlations":
                correlations,

            "insights":
                insights,

            "ml_recommendation":
                ml_recommendation
        }


        return normalized_dataset


    # ========================================================
    # BUILD LOCAL RESULT
    # ========================================================

    def build_local_result(
        self,
        task: str,
        analysis: dict
    ) -> dict:

        """
        Build the final local Data Agent response.
        """

        dataset = self.normalize_analysis(
            analysis
        )


        return {

            "agent":
                self.name,

            "task":
                task,

            "status":
                "completed",

            # Original analyzer output
            "analysis":
                analysis,

            # Normalized frontend output
            "dataset":
                dataset,

            # Top-level insights
            "insights":
                dataset.get(
                    "insights",
                    []
                ),

            # Gemini disabled
            "ai_insights":
                None,

            "ai_status":
                "disabled",

            "message":
                (
                    "Dataset analysis completed "
                    "successfully using local Python "
                    "and Pandas."
                ),

            # ML recommendation
            "ml_recommendation":
                dataset.get(
                    "ml_recommendation",
                    {}
                )
        }


    # ========================================================
    # OPTIONAL GEMINI
    # ========================================================

    async def generate_ai_insights(
        self,
        task: str,
        analysis: dict
    ) -> dict:

        """
        Optional Gemini interpretation.

        Gemini is NOT used unless explicitly enabled.
        """

        if not self.client:

            return {

                "ai_insights":
                    None,

                "ai_status":
                    "disabled",

                "message":
                    (
                        "Dataset analysis completed "
                        "using local Python and Pandas."
                    )
            }


        prompt = f"""
You are a senior data analyst.

A dataset was analyzed using Python and Pandas.

Dataset analysis:

{json.dumps(
    analysis,
    indent=2
)}

User request:

{task}

Provide a concise data analysis containing:

1. Dataset overview
2. Important statistical findings
3. Missing-data observations
4. Interesting patterns or trends
5. Practical insights

Do not invent information that is not present
in the analysis.
"""


        try:

            response = (
                self.client
                .models
                .generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
            )


            return {

                "ai_insights":
                    response.text,

                "ai_status":
                    "available",

                "message":
                    (
                        "Dataset analysis and "
                        "AI interpretation completed."
                    )
            }


        except Exception as error:

            error_message = str(
                error
            )


            if (
                "429" in error_message
                or
                "RESOURCE_EXHAUSTED"
                in error_message
            ):

                return {

                    "ai_insights":
                        None,

                    "ai_status":
                        "quota_exhausted",

                    "message":
                        (
                            "Dataset analysis completed "
                            "successfully using local Python "
                            "and Pandas. Gemini AI "
                            "interpretation is unavailable "
                            "because the API quota is exhausted."
                        )
                }


            if "503" in error_message:

                return {

                    "ai_insights":
                        None,

                    "ai_status":
                        "temporarily_unavailable",

                    "message":
                        (
                            "Dataset analysis completed "
                            "successfully using local Python "
                            "and Pandas. Gemini is temporarily "
                            "unavailable."
                        )
                }


            return {

                "ai_insights":
                    None,

                "ai_status":
                    "error",

                "message":
                    (
                        "Dataset analysis completed "
                        "successfully using local Python "
                        "and Pandas, but AI interpretation "
                        "could not be generated."
                    ),

                "ai_error":
                    error_message
            }


    # ========================================================
    # MAIN RUN
    # ========================================================

    async def run(
        self,
        task: str,
        file_path: str = None
    ) -> dict:

        """
        Analyze a CSV dataset.

        Local analysis is always performed first.

        Gemini is optional and disabled by default.
        """

        # ----------------------------------------------------
        # File required
        # ----------------------------------------------------

        if not file_path:

            return {

                "agent":
                    self.name,

                "task":
                    task,

                "status":
                    "waiting_for_file",

                "result":
                    (
                        "Please provide a CSV "
                        "dataset for analysis."
                    )
            }


        # ----------------------------------------------------
        # CSV only
        # ----------------------------------------------------

        if not file_path.lower().endswith(
            ".csv"
        ):

            return {

                "agent":
                    self.name,

                "task":
                    task,

                "status":
                    "invalid_file",

                "result":
                    (
                        "Only CSV files are supported "
                        "for dataset analysis."
                    )
            }


        try:

            # ------------------------------------------------
            # LOCAL PANDAS ANALYSIS
            # ------------------------------------------------

            analysis = (
                self.analyzer.analyze(
                    file_path
                )
            )


            # ------------------------------------------------
            # LOCAL-FIRST MODE
            # ------------------------------------------------

            if not ENABLE_GEMINI:

                return self.build_local_result(
                    task,
                    analysis
                )


            # ------------------------------------------------
            # OPTIONAL GEMINI
            # ------------------------------------------------

            ai_result = (
                await self.generate_ai_insights(
                    task,
                    analysis
                )
            )


            # ------------------------------------------------
            # Normalize regardless of Gemini status
            # ------------------------------------------------

            dataset = self.normalize_analysis(
                analysis
            )


            return {

                "agent":
                    self.name,

                "task":
                    task,

                "status":
                    "completed",

                "analysis":
                    analysis,

                "dataset":
                    dataset,

                "insights":
                    dataset.get(
                        "insights",
                        []
                    ),

                "ai_insights":
                    ai_result.get(
                        "ai_insights"
                    ),

                "ai_status":
                    ai_result.get(
                        "ai_status"
                    ),

                "message":
                    ai_result.get(
                        "message"
                    ),

                "ml_recommendation":
                    dataset.get(
                        "ml_recommendation",
                        {}
                    )
            }


        # ----------------------------------------------------
        # File not found
        # ----------------------------------------------------

        except FileNotFoundError:

            return {

                "agent":
                    self.name,

                "task":
                    task,

                "status":
                    "error",

                "result":
                    (
                        "The uploaded dataset "
                        "could not be found."
                    )
            }


        # ----------------------------------------------------
        # General error
        # ----------------------------------------------------

        except Exception as error:

            return {

                "agent":
                    self.name,

                "task":
                    task,

                "status":
                    "error",

                "result":
                    str(error)
            }