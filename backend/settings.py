import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# CONFIGURATION HELPERS
# ============================================================

def _positive_int(name, default):
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a positive integer."
        ) from exc

    if value <= 0:
        raise ValueError(
            f"{name} must be a positive integer."
        )

    return value


def _boolean(name, default=False):
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()

    if normalized not in {
        "true",
        "false",
    }:
        raise ValueError(
            f"{name} must be true or false."
        )

    return normalized == "true"


# ============================================================
# SETTINGS
# ============================================================

@dataclass(frozen=True)
class Settings:

    # --------------------------------------------------------
    # General ORBIT
    # --------------------------------------------------------

    api_key: str | None

    max_upload_bytes: int
    max_task_length: int

    max_csv_rows: int
    max_csv_columns: int

    rate_limit_requests: int
    rate_limit_window_seconds: int

    max_concurrent_requests: int
    request_timeout_seconds: int

    agent_executor_workers: int

    # --------------------------------------------------------
    # Gemini
    # --------------------------------------------------------

    enable_gemini: bool
    gemini_api_key: str | None

    # --------------------------------------------------------
    # FreeLLMAPI
    # --------------------------------------------------------

    freellmapi_api_key: str | None
    freellmapi_base_url: str | None
    freellmapi_model: str

    # --------------------------------------------------------
    # DeepSeek
    # --------------------------------------------------------

    deepseek_api_key: str | None
    deepseek_base_url: str
    deepseek_model: str

    # --------------------------------------------------------
    # OpenRouter
    # --------------------------------------------------------

    openrouter_api_key: str | None
    openrouter_base_url: str
    openrouter_model: str

    # ========================================================
    # LOAD FROM ENVIRONMENT
    # ========================================================

    @classmethod
    def from_environment(cls):

        # ----------------------------------------------------
        # Gemini
        # ----------------------------------------------------

        gemini_api_key = (
            os.getenv("GEMINI_API_KEY")
            or None
        )

        enable_gemini = _boolean(
            "ORBIT_ENABLE_GEMINI"
        )

        if (
            enable_gemini
            and not gemini_api_key
        ):
            raise ValueError(
                "ORBIT_ENABLE_GEMINI=true "
                "requires GEMINI_API_KEY."
            )

        # ----------------------------------------------------
        # Return configuration
        # ----------------------------------------------------

        return cls(

            # ------------------------------------------------
            # General ORBIT
            # ------------------------------------------------

            api_key=(
                os.getenv("ORBIT_API_KEY")
                or None
            ),

            max_upload_bytes=_positive_int(
                "ORBIT_MAX_UPLOAD_BYTES",
                10 * 1024 * 1024,
            ),

            max_task_length=_positive_int(
                "ORBIT_MAX_TASK_LENGTH",
                2000,
            ),

            max_csv_rows=_positive_int(
                "ORBIT_MAX_CSV_ROWS",
                100000,
            ),

            max_csv_columns=_positive_int(
                "ORBIT_MAX_CSV_COLUMNS",
                100,
            ),

            rate_limit_requests=_positive_int(
                "ORBIT_RATE_LIMIT_REQUESTS",
                60,
            ),

            rate_limit_window_seconds=_positive_int(
                "ORBIT_RATE_LIMIT_WINDOW_SECONDS",
                60,
            ),

            max_concurrent_requests=_positive_int(
                "ORBIT_MAX_CONCURRENT_REQUESTS",
                4,
            ),

            request_timeout_seconds=_positive_int(
                "ORBIT_REQUEST_TIMEOUT_SECONDS",
                60,
            ),

            agent_executor_workers=_positive_int(
                "ORBIT_AGENT_EXECUTOR_WORKERS",
                4,
            ),

            # ------------------------------------------------
            # Gemini
            # ------------------------------------------------

            enable_gemini=enable_gemini,

            gemini_api_key=gemini_api_key,

            # ------------------------------------------------
            # FreeLLMAPI
            # ------------------------------------------------

            freellmapi_api_key=(
                os.getenv(
                    "FREELLMAPI_API_KEY"
                )
                or None
            ),

            freellmapi_base_url=(
                os.getenv(
                    "FREELLMAPI_BASE_URL"
                )
                or None
            ),

            freellmapi_model=os.getenv(
                "FREELLMAPI_MODEL",
                "auto",
            ),

            # ------------------------------------------------
            # DeepSeek
            # ------------------------------------------------

            deepseek_api_key=(
                os.getenv(
                    "DEEPSEEK_API_KEY"
                )
                or None
            ),

            deepseek_base_url=os.getenv(
                "DEEPSEEK_BASE_URL",
                "https://api.deepseek.com",
            ),

            deepseek_model=os.getenv(
                "DEEPSEEK_MODEL",
                "deepseek-v4-flash",
            ),

            # ------------------------------------------------
            # OpenRouter
            # ------------------------------------------------

            openrouter_api_key=(
                os.getenv(
                    "OPENROUTER_API_KEY"
                )
                or None
            ),

            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL",
                "https://openrouter.ai/api/v1",
            ),

            openrouter_model=os.getenv(
                "OPENROUTER_MODEL",
                "openrouter/free",
            ),
        )


# ============================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================

settings = Settings.from_environment()