import asyncio
import json
import urllib.error
import urllib.request


try:
    from ..settings import settings
except ImportError:
    from settings import settings


class OpenRouterClient:
    """
    OpenRouter-compatible LLM client.

    Uses OpenRouter's OpenAI-compatible Chat Completions API.

    Default model:
        openrouter/free
    """

    def __init__(self):
        self.api_key = getattr(
            settings,
            "openrouter_api_key",
            None,
        )

        self.base_url = getattr(
            settings,
            "openrouter_base_url",
            "https://openrouter.ai/api/v1",
        )

        self.model = getattr(
            settings,
            "openrouter_model",
            "openrouter/free",
        )

        self.timeout = getattr(
            settings,
            "request_timeout_seconds",
            60,
        )

    @property
    def available(self):
        return bool(
            self.api_key
            and self.base_url
        )

    def _build_url(self):
        base_url = str(
            self.base_url or ""
        ).strip().rstrip("/")

        if not base_url:
            return ""

        if base_url.endswith(
            "/chat/completions"
        ):
            return base_url

        return (
            f"{base_url}/chat/completions"
        )

    def _request(
        self,
        messages,
        temperature=0.2,
        max_tokens=2048,
    ):
        url = self._build_url()

        if not url:
            raise RuntimeError(
                "OpenRouter base URL is not configured."
            )

        if not self.api_key:
            raise RuntimeError(
                "OpenRouter API key is not configured."
            )

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        body = json.dumps(
            payload
        ).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": (
                    f"Bearer {self.api_key}"
                ),
                "Content-Type": (
                    "application/json"
                ),
                "Accept": (
                    "application/json"
                ),

                # Optional OpenRouter metadata.
                "HTTP-Referer": (
                    "http://localhost:5173"
                ),
                "X-Title": "ORBIT",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                raw = response.read(
                    2 * 1024 * 1024
                )

                data = json.loads(
                    raw.decode(
                        "utf-8",
                        errors="replace",
                    )
                )

        except urllib.error.HTTPError as exc:

            try:
                error_body = exc.read(
                    8192
                ).decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                error_body = ""

            raise RuntimeError(
                f"OpenRouter HTTP {exc.code}: "
                f"{error_body}"
            ) from exc

        except urllib.error.URLError as exc:

            raise RuntimeError(
                "OpenRouter connection failed: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:

            raise RuntimeError(
                "OpenRouter request timed out."
            ) from exc

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "OpenRouter returned invalid JSON."
            ) from exc

        if not isinstance(
            data,
            dict,
        ):
            raise RuntimeError(
                "OpenRouter returned an invalid response."
            )

        # OpenRouter may return an explicit API error
        # inside the JSON response.
        error = data.get("error")

        if isinstance(
            error,
            dict,
        ):
            message = error.get(
                "message",
                "Unknown OpenRouter error.",
            )

            code = error.get(
                "code"
            )

            if code:
                raise RuntimeError(
                    f"OpenRouter error {code}: "
                    f"{message}"
                )

            raise RuntimeError(
                f"OpenRouter error: {message}"
            )

        choices = data.get(
            "choices"
        )

        if not isinstance(
            choices,
            list,
        ) or not choices:

            raise RuntimeError(
                "OpenRouter response contained "
                "no choices."
            )

        first_choice = choices[0]

        if not isinstance(
            first_choice,
            dict,
        ):
            raise RuntimeError(
                "OpenRouter returned an invalid choice."
            )

        message = first_choice.get(
            "message"
        )

        if isinstance(
            message,
            dict,
        ):
            content = message.get(
                "content"
            )

            if isinstance(
                content,
                str,
            ):
                return content.strip()

        text = first_choice.get(
            "text"
        )

        if isinstance(
            text,
            str,
        ):
            return text.strip()

        raise RuntimeError(
            "OpenRouter response contained "
            "no text content."
        )

    async def chat(
        self,
        messages,
        temperature=0.2,
        max_tokens=2048,
    ):
        """
        Async wrapper around the blocking HTTP client.
        """

        return await asyncio.to_thread(
            self._request,
            messages,
            temperature,
            max_tokens,
        )

    async def complete(
        self,
        prompt,
        system_prompt=None,
        temperature=0.2,
        max_tokens=2048,
    ):
        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": str(prompt),
            }
        )

        return await self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate(
        self,
        prompt,
        system_prompt=None,
        temperature=0.2,
        max_tokens=2048,
    ):
        """
        Generate text through the ORBIT LLM interface.
        """

        return await self.complete(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )


# ------------------------------------------------------------
# Backwards compatibility
# ------------------------------------------------------------

LLMClient = OpenRouterClient
FreeLLMAPIClient = OpenRouterClient
DeepSeekClient = OpenRouterClient