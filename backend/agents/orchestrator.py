import os
import re

from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None

from .research_agent import ResearchAgent
from .data_agent import DataAgent
from .ml_agent import MLAgent


load_dotenv()


class Orchestrator:
    """
    ORBIT multi-agent router.

    Routing priority:
        1. Explicit ML/modeling request
        2. Explicit dataset/CSV request
        3. Research/general-information request
        4. Optional Gemini fallback
        5. Graceful failure

    The deterministic router is intentionally strong enough that common
    research questions such as "what is an LLM", "whats a llm", "what is RAG",
    and "latest developments in agentic AI" do not require Gemini.
    """

    def __init__(self):
        self.research_agent = ResearchAgent()
        self.data_agent = DataAgent()
        self.ml_agent = MLAgent()

        self.client = None

        api_key = os.getenv("GEMINI_API_KEY")

        if api_key and genai is not None:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception:
                self.client = None

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def normalize_task(task):
        if not task:
            return ""

        task = str(task).lower().strip()
        task = re.sub(r"\s+", " ", task)

        # Normalize common informal spellings.
        replacements = {
            "whats": "what is",
            "whats": "what is",
            "what's": "what is",
            "wht": "what",
            "pls": "please",
            "ml/ai": "machine learning ai",
        }

        for old, new in replacements.items():
            task = re.sub(rf"\b{re.escape(old)}\b", new, task)

        return task

    # ============================================================
    # KEYWORD MATCHING
    # ============================================================

    @staticmethod
    def contains_any(text, keywords):
        return any(keyword in text for keyword in keywords)

    # ============================================================
    # ROUTE DETECTION
    # ============================================================

    def detect_route(self, task, file_path=None):
        """
        Determine the specialized agent.

        ML has priority when the user explicitly asks for prediction,
        training, classification, regression, forecasting, or model
        evaluation.

        DATA has priority when the task is about inspecting/analyzing a
        dataset or CSV without asking the system to build/evaluate a model.

        RESEARCH handles general questions, explanations, current information,
        technology topics, definitions, comparisons, and unknown natural
        language tasks when no dataset/modeling intent exists.
        """

        task_lower = self.normalize_task(task)

        if not task_lower:
            return None

        # --------------------------------------------------------
        # FILE TYPE
        # --------------------------------------------------------

        is_csv = False

        if file_path:
            is_csv = str(file_path).lower().endswith(".csv")

        # --------------------------------------------------------
        # ML REQUESTS
        # --------------------------------------------------------

        ml_keywords = [
            "machine learning",
            "machine-learning",
            "ml model",
            "ml models",
            "train model",
            "train a model",
            "train the model",
            "model training",
            "model evaluation",
            "evaluate model",
            "predict",
            "prediction",
            "predicting",
            "forecast",
            "forecasting",
            "regression",
            "classification",
            "classifier",
            "classify",
            "accuracy",
            "precision",
            "recall",
            "f1 score",
            "f1-score",
            "r2 score",
            "mean squared error",
            "mean absolute error",
            "mse",
            "mae",
            "feature importance",
            "predict the target",
            "predict target",
            "salary prediction",
            "price prediction",
            "sales prediction",
        ]

        # These are explicit modeling actions. They should beat DATA.
        ml_action_keywords = [
            "predict",
            "prediction",
            "predicting",
            "forecast",
            "forecasting",
            "train model",
            "train a model",
            "train the model",
            "training",
            "classify",
            "classification",
            "regression",
            "model evaluation",
            "evaluate model",
            "accuracy",
            "precision",
            "recall",
            "f1 score",
            "f1-score",
            "r2 score",
            "mean squared error",
            "mean absolute error",
            "mse",
            "mae",
            "feature importance",
        ]

        has_ml = self.contains_any(task_lower, ml_keywords)
        has_ml_action = self.contains_any(task_lower, ml_action_keywords)

        # --------------------------------------------------------
        # DATA REQUESTS
        # --------------------------------------------------------

        data_keywords = [
            "analyze dataset",
            "analyse dataset",
            "analyze this dataset",
            "analyse this dataset",
            "analyze the dataset",
            "analyse the dataset",
            "analyze csv",
            "analyse csv",
            "analyze this csv",
            "analyse this csv",
            "csv analysis",
            "dataset analysis",
            "data analysis",
            "data analytics",
            "analyze data",
            "analyse data",
            "statistics",
            "statistical analysis",
            "statistical summary",
            "summary statistics",
            "correlation",
            "correlations",
            "missing values",
            "missing data",
            "data insights",
            "dataset insights",
            "data cleaning",
            "clean the data",
            "clean dataset",
            "data quality",
            "duplicates",
            "duplicate rows",
            "outliers",
            "explore dataset",
            "exploratory data analysis",
            "eda",
            "describe dataset",
            "describe the dataset",
            "summarize dataset",
            "summarize the dataset",
            "inspect dataset",
            "inspect data",
        ]

        has_data = self.contains_any(task_lower, data_keywords)

        # Explicit model operation always wins.
        if has_ml_action:
            return "ML"

        # CSV/dataset analysis without a model operation goes to DATA.
        if has_data:
            return "DATA"

        # An uploaded CSV with an analysis-like task is DATA.
        if is_csv and self.contains_any(
            task_lower,
            [
                "analyze",
                "analyse",
                "inspect",
                "explore",
                "understand",
                "summarize",
                "summary",
                "dataset",
                "data",
                "clean",
                "statistics",
            ],
        ):
            return "DATA"

        # --------------------------------------------------------
        # RESEARCH REQUESTS
        # --------------------------------------------------------

        research_keywords = [
            "research",
            "latest",
            "current",
            "news",
            "what is",
            "what are",
            "who is",
            "who are",
            "how does",
            "how do",
            "how can",
            "why does",
            "why do",
            "explain",
            "compare",
            "comparison",
            "information about",
            "tell me about",
            "definition",
            "define",
            "meaning of",

            # AI / technology topics commonly sent to Research Agent.
            "llm",
            "large language model",
            "large language models",
            "generative ai",
            "agentic ai",
            "artificial intelligence",
            " ai ",
            "machine learning",
            "deep learning",
            "transformer",
            "transformers",
            "rag",
            "retrieval augmented generation",
            "embedding",
            "embeddings",
            "vector database",
            "neural network",
            "neural networks",
            "openai",
            "gemini",
            "claude",
            "mistral",
            "hugging face",
            "computer vision",
            "natural language processing",
            "nlp",
            "technology",
        ]

        if self.contains_any(f" {task_lower} ", research_keywords):
            return "RESEARCH"

        # Pure ML terminology without a modeling action.
        # Example: "explain machine learning".
        if has_ml:
            return "RESEARCH"

        # --------------------------------------------------------
        # SAFE DEFAULT
        # --------------------------------------------------------
        #
        # If there is no file and no explicit DATA/ML operation,
        # treat a normal natural-language task as research instead
        # of returning "none". This fixes tasks such as:
        #   "whats a llm"
        #   "tell me about transformers"
        #   "why is AI important"
        #
        if not file_path:
            return "RESEARCH"

        return None

    # ============================================================
    # RUN SELECTED AGENT
    # ============================================================

    async def run_agent(self, decision, task, file_path=None):
        if decision == "ML":
            return await self.ml_agent.run(task, file_path)

        if decision == "DATA":
            return await self.data_agent.run(task, file_path)

        if decision == "RESEARCH":
            return await self.research_agent.run(task)

        return {
            "agent": "Orchestrator",
            "task": task,
            "status": "not_routed",
            "result": "No specialized agent was selected.",
        }

    # ============================================================
    # OPTIONAL GEMINI ROUTER
    # ============================================================

    async def ai_route(self, task):
        """
        Optional Gemini fallback.

        Deterministic routing is used first, so normal research questions
        do not depend on Gemini.
        """

        if self.client is None:
            return None

        prompt = f"""
You are the routing component of ORBIT.

Choose exactly one agent for this task.

RESEARCH:
- General questions
- Definitions and explanations
- Current information and news
- Technology research
- AI/LLM/RAG/agentic AI questions

DATA:
- CSV or dataset analysis
- Statistics
- Data cleaning
- Correlations
- Missing values
- EDA

ML:
- Prediction
- Forecasting
- Classification
- Regression
- Model training
- Model evaluation

TASK:
{task}

Return only:
RESEARCH
DATA
or
ML
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )

            decision = str(
                getattr(response, "text", "")
            ).strip().upper()

            # Exact match first.
            if decision in {"RESEARCH", "DATA", "ML"}:
                return decision

            # Then tolerate extra explanatory text.
            if re.search(r"\bRESEARCH\b", decision):
                return "RESEARCH"

            if re.search(r"\bDATA\b", decision):
                return "DATA"

            if re.search(r"\bML\b", decision):
                return "ML"

        except Exception:
            pass

        return None

    # ============================================================
    # MAIN ROUTER
    # ============================================================

    async def route(self, task, file_path=None):
        """
        Main ORBIT routing pipeline.

        Deterministic routing is deliberately first.
        Gemini is only a fallback.
        """

        if not task or not str(task).strip():
            return {
                "agent": "Orchestrator",
                "task": task,
                "status": "invalid_task",
                "routing": {
                    "method": "none",
                    "agent": "ORCHESTRATOR",
                },
                "result": "Please provide a task for ORBIT.",
            }

        task = str(task).strip()

        # --------------------------------------------------------
        # STEP 1: DETERMINISTIC ROUTING
        # --------------------------------------------------------

        decision = self.detect_route(task, file_path)

        if decision:
            result = await self.run_agent(
                decision,
                task,
                file_path,
            )

            if not isinstance(result, dict):
                result = {
                    "agent": decision,
                    "task": task,
                    "status": "completed",
                    "result": str(result),
                }

            result["routing"] = {
                "method": "deterministic",
                "agent": decision,
            }

            return result

        # --------------------------------------------------------
        # STEP 2: OPTIONAL GEMINI FALLBACK
        # --------------------------------------------------------

        decision = await self.ai_route(task)

        if decision:
            result = await self.run_agent(
                decision,
                task,
                file_path,
            )

            if not isinstance(result, dict):
                result = {
                    "agent": decision,
                    "task": task,
                    "status": "completed",
                    "result": str(result),
                }

            result["routing"] = {
                "method": "gemini",
                "agent": decision,
            }

            return result

        # --------------------------------------------------------
        # STEP 3: GRACEFUL FAILURE
        # --------------------------------------------------------

        return {
            "agent": "Orchestrator",
            "task": task,
            "status": "not_routed",
            "routing": {
                "method": "none",
                "agent": "ORCHESTRATOR",
            },
            "result": (
                "ORBIT could not determine the appropriate agent "
                "for this task."
            ),
        }