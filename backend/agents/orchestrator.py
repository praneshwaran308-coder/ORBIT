import re

from .data_agent import DataAgent
from .ml_agent import MLAgent
from .research_agent import ResearchAgent
from .llm_client import OpenRouterClient


# ============================================================
# ORBIT ORCHESTRATOR
# ============================================================

class Orchestrator:
    """
    ORBIT multi-agent orchestration system.

    Agents:

        RESEARCH
        DATA
        ML

    OpenRouter is used for:

        - Direct general AI questions
        - AI response generation
        - Optional intelligent routing

    Deterministic routing is preferred whenever possible.
    """

    def __init__(self):

        # ----------------------------------------------------
        # Specialized agents
        # ----------------------------------------------------

        self.research_agent = ResearchAgent()
        self.data_agent = DataAgent()
        self.ml_agent = MLAgent()

        # ----------------------------------------------------
        # OpenRouter
        # ----------------------------------------------------

        try:
            self.client = OpenRouterClient()

            if not self.client.available:
                self.client = None

        except Exception:
            self.client = None

    # =========================================================
    # HELPER
    # =========================================================

    @staticmethod
    def contains_any(
        text,
        keywords,
    ):
        return any(
            keyword in text
            for keyword in keywords
        )

    # =========================================================
    # DETECT SIMPLE AI QUESTION
    # =========================================================

    def is_direct_ai_question(
        self,
        task,
    ):
        """
        Detect questions that should go directly to OpenRouter
        instead of the web Research Agent.

        Examples:

            What is Python?
            Explain machine learning.
            What is ORBIT?
            Explain APIs.
            How does an LLM work?
        """

        task_lower = str(
            task or ""
        ).lower().strip()

        if not task_lower:
            return False

        # -----------------------------------------------------
        # Actual web/current research should NOT be direct AI.
        # -----------------------------------------------------

        research_only_keywords = [
            "latest",
            "current",
            "today",
            "recent",
            "news",
            "this week",
            "this month",
            "research the latest",
            "find recent",
            "search the web",
            "web search",
            "sources",
            "articles",
            "published",
            "developments",
            "breaking",
        ]

        if self.contains_any(
            task_lower,
            research_only_keywords,
        ):
            return False

        # -----------------------------------------------------
        # Direct explanatory patterns
        # -----------------------------------------------------

        direct_patterns = [
            r"^what\s+is\b",
            r"^what\s+are\b",
            r"^what's\b",
            r"^whats\b",
            r"^who\s+is\b",
            r"^why\s+is\b",
            r"^why\s+are\b",
            r"^why\s+does\b",
            r"^why\s+do\b",
            r"^how\s+does\b",
            r"^how\s+do\b",
            r"^how\s+is\b",
            r"^how\s+are\b",
            r"^explain\b",
            r"^define\b",
            r"^definition\s+of\b",
            r"^meaning\s+of\b",
            r"^tell\s+me\s+about\b",
            r"^describe\b",
        ]

        if any(
            re.search(
                pattern,
                task_lower,
            )
            for pattern in direct_patterns
        ):
            return True

        return False

    # =========================================================
    # DETECT ROUTE
    # =========================================================

    def detect_route(
        self,
        task,
        file_path=None,
    ):
        """
        Determine which specialized agent should handle the
        task.

        Returns:

            ML
            DATA
            RESEARCH
            DIRECT_AI
            None
        """

        task_lower = str(
            task or ""
        ).lower().strip()

        is_csv = False

        if file_path:
            is_csv = str(
                file_path
            ).lower().endswith(
                ".csv"
            )

        # =====================================================
        # ML KEYWORDS
        # =====================================================

        ml_keywords = [
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

        # =====================================================
        # EXPLICIT ML ACTIONS
        # =====================================================

        ml_action_keywords = [
"predict",
"prediction",
"forecast",
"train model",
"train a model",
"train the model",
"training model",
"build model",
"create model",
"fit model",
"classify the",
"classify this",
"classify these",
"evaluate model",
"calculate accuracy",
"calculate precision",
"calculate recall",
"calculate f1 score",
"feature importance",
        ]

        has_ml = self.contains_any(
            task_lower,
            ml_keywords,
        )

        has_ml_action = self.contains_any(
            task_lower,
            ml_action_keywords,
        )

        # Explicit modeling operation wins.
        if has_ml_action:
            return "ML"

        # =====================================================
        # DATA
        # =====================================================

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

        has_data = self.contains_any(
            task_lower,
            data_keywords,
        )

        if has_data:
            return "DATA"

        # =====================================================
        # CSV + ANALYSIS
        # =====================================================

        if (
            is_csv
            and self.contains_any(
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
            )
        ):
            return "DATA"

        # =====================================================
        # DIRECT AI
        # =====================================================

        if self.is_direct_ai_question(
            task
        ):
            return "DIRECT_AI"

        # =====================================================
        # RESEARCH
        # =====================================================

        research_keywords = [
            "research",
            "latest",
            "current",
            "news",
            "recent",
            "today",
            "this week",
            "this month",
            "developments",
            "breaking",
            "search the web",
            "web search",
            "find recent",
            "find sources",
            "articles",
            "published",
        ]

        if self.contains_any(
            task_lower,
            research_keywords,
        ):
            return "RESEARCH"

        # =====================================================
        # AI / TECHNOLOGY
        # =====================================================

        technology_keywords = [
            "llm",
            "large language model",
            "large language models",
            "generative ai",
            "agentic ai",
            "artificial intelligence",
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

        if self.contains_any(
            task_lower,
            technology_keywords,
        ):
            return "DIRECT_AI"

        # Pure ML terminology without a modeling operation.
        if has_ml:
            return "DIRECT_AI"

        # =====================================================
        # GENERAL TASK
        # =====================================================

        if not file_path:
            return "DIRECT_AI"

        return None

    # =========================================================
    # DIRECT OPENROUTER RESPONSE
    # =========================================================

    async def direct_ai(
        self,
        task,
    ):
        """
        Send a normal AI question directly to OpenRouter.
        """

        if self.client is None:

            return {
                "agent": "OpenRouter AI",
                "task": task,
                "status": "unavailable",
                "ai_status": "unavailable",
                "result": (
                    "OpenRouter is not configured."
                ),
            }

        system_prompt = """
You are ORBIT's AI assistant.

ORBIT means:

Real-Time Multi-Agent AI Orchestration Platform.

ORBIT is a software platform that coordinates multiple
specialized AI agents, including Research, Data Analysis,
and Machine Learning agents.

When the user asks what ORBIT is, they are referring to
this ORBIT platform unless the user explicitly specifies
another meaning.

Answer the user's question directly.

Rules:
- Be accurate.
- Do not invent ORBIT features.
- Be concise when the user requests a short answer.
- Do not mention internal routing.
- Do not mention OpenRouter.
- Do not output safety classifications.
- Return only the answer.
"""

        try:

            response = await self.client.complete(
                task,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=2048,
            )

            response = str(
                response or ""
            ).strip()

            if not response:
                raise RuntimeError(
                    "OpenRouter returned an empty response."
                )

            return {
                "agent": "OpenRouter AI",
                "task": task,
                "status": "completed",
                "ai_status": "completed",
                "ai_model": getattr(
                    self.client,
                    "model",
                    "openrouter/free",
                ),
                "result": response,
            }

        except Exception as error:

            return {
                "agent": "OpenRouter AI",
                "task": task,
                "status": "error",
                "ai_status": "error",
                "result": (
                    "ORBIT AI could not generate "
                    "a response."
                ),
                "error": str(error),
            }

    # =========================================================
    # RUN SPECIALIZED AGENT
    # =========================================================

    async def run_agent(
        self,
        decision,
        task,
        file_path=None,
    ):

        if decision == "ML":

            return await self.ml_agent.run(
                task,
                file_path,
            )

        if decision == "DATA":

            return await self.data_agent.run(
                task,
                file_path,
            )

        if decision == "RESEARCH":

            return await self.research_agent.run(
                task,
            )

        if decision == "DIRECT_AI":

            return await self.direct_ai(
                task,
            )

        return {
            "agent": "Orchestrator",
            "task": task,
            "status": "not_routed",
            "result": (
                "No specialized agent "
                "was selected."
            ),
        }

    # =========================================================
    # OPENROUTER ROUTING FALLBACK
    # =========================================================

    async def ai_route(
        self,
        task,
    ):
        """
        OpenRouter fallback routing.

        Used only when deterministic routing cannot decide.
        """

        if self.client is None:
            return None

        prompt = f"""
You are the routing component of ORBIT.

ORBIT is a Real-Time Multi-Agent AI Orchestration Platform.

Choose exactly ONE agent.

RESEARCH:
Use for current information, latest news, recent events,
web research, sources, or article-based questions.

DATA:
Use for CSV/dataset analysis, statistics, cleaning,
correlations, missing values, and EDA.

ML:
Use for prediction, forecasting, classification,
regression, model training, or model evaluation.

DIRECT_AI:
Use for ordinary questions, explanations, definitions,
coding concepts, general knowledge, and conversational AI.

TASK:
{task}

Return ONLY:

RESEARCH
DATA
ML
or
DIRECT_AI
"""

        try:

            response = await self.client.complete(
                prompt,
                temperature=0.0,
                max_tokens=20,
            )

            decision = str(
                response or ""
            ).strip().upper()

            if decision in {
                "RESEARCH",
                "DATA",
                "ML",
                "DIRECT_AI",
            }:
                return decision

            if re.search(
                r"\bDIRECT_AI\b",
                decision,
            ):
                return "DIRECT_AI"

            if re.search(
                r"\bRESEARCH\b",
                decision,
            ):
                return "RESEARCH"

            if re.search(
                r"\bDATA\b",
                decision,
            ):
                return "DATA"

            if re.search(
                r"\bML\b",
                decision,
            ):
                return "ML"

        except Exception:
            pass

        return None

    # =========================================================
    # MAIN ROUTE
    # =========================================================

    async def route(
        self,
        task,
        file_path=None,
    ):
        """
        Main ORBIT pipeline.

        User
          ↓
        Deterministic router
          ↓
        ┌───────────────┬──────────────┬─────────────┐
        │               │              │             │
        AI          Research         Data           ML
        │               │              │             │
        └───────────────┴──────────────┴─────────────┘
                          ↓
                       Response
        """

        # =====================================================
        # VALIDATE
        # =====================================================

        if not task or not str(
            task
        ).strip():

            return {
                "agent": "Orchestrator",
                "task": task,
                "status": "invalid_task",
                "routing": {
                    "method": "none",
                    "agent": "ORCHESTRATOR",
                },
                "result": (
                    "Please provide a task "
                    "for ORBIT."
                ),
            }

        task = str(
            task
        ).strip()

        # =====================================================
        # STEP 1
        # DETERMINISTIC ROUTING
        # =====================================================

        decision = self.detect_route(
            task,
            file_path,
        )

        routing_method = "deterministic"

        # =====================================================
        # STEP 2
        # OPENROUTER FALLBACK
        # =====================================================

        if not decision:

            decision = await self.ai_route(
                task
            )

            routing_method = "openrouter"

        # =====================================================
        # FAILURE
        # =====================================================

        if not decision:

            return {
                "agent": "Orchestrator",
                "task": task,
                "status": "not_routed",
                "ai_status": "unavailable",
                "routing": {
                    "method": "none",
                    "agent": "ORCHESTRATOR",
                },
                "result": (
                    "ORBIT could not determine "
                    "the appropriate agent."
                ),
            }

        # =====================================================
        # STEP 3
        # RUN AGENT
        # =====================================================

        result = await self.run_agent(
            decision,
            task,
            file_path,
        )

        if not isinstance(
            result,
            dict,
        ):

            result = {
                "agent": decision,
                "task": task,
                "status": "completed",
                "result": str(
                    result
                ),
            }

        # =====================================================
        # ROUTING METADATA
        # =====================================================

        result["routing"] = {
            "method": routing_method,
            "agent": decision,
        }

        return result


# ============================================================
# GLOBAL ORCHESTRATOR
# ============================================================

orchestrator = Orchestrator()