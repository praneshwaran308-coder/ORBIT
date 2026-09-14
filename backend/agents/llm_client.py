import asyncio
import json
import urllib.error
import urllib.request


try:
    from ..settings import settings
except ImportError:
    from settings import settings


class OpenRouterClient:
    provider_name = "OpenRouter"
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
class DeepSeekClient(OpenRouterClient):

    provider_name = "DeepSeek"

    def __init__(self):
        self.api_key = getattr(settings, "deepseek_api_key", None)
        self.base_url = getattr(
            settings,
            "deepseek_base_url",
            "https://api.deepseek.com",
        )
        self.model = getattr(
            settings,
            "deepseek_model",
            "deepseek-v4-flash",
        )
        self.timeout = getattr(
            settings,
            "request_timeout_seconds",
            60,
        )


class FreeLLMAPIClient(OpenRouterClient):

    provider_name = "FreeLLMAPI"

    def __init__(self):
        self.api_key = getattr(
            settings,
            "freellmapi_api_key",
            None,
        )
        self.base_url = getattr(
            settings,
            "freellmapi_base_url",
            "",
        )
        self.model = getattr(
            settings,
            "freellmapi_model",
            "auto",
        )
        self.timeout = getattr(
            settings,
            "request_timeout_seconds",
            60,
        )


class GeminiClient(OpenRouterClient):

    provider_name = "Gemini"

    def __init__(self):
        self.api_key = getattr(
            settings,
            "gemini_api_key",
            None,
        )
        self.base_url = (
            "https://generativelanguage.googleapis.com/v1beta/openai"
        )
        self.model = "gemini-3.6-flash"
        self.timeout = getattr(
            settings,
            "request_timeout_seconds",
            60,
        )

    def _request(
        self,
        messages,
        temperature=0.2,
        max_tokens=2048,
    ):
        url = self._build_url()

        if not self.api_key:
            raise RuntimeError(
                "Gemini API key is not configured."
            )

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
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
                f"Gemini HTTP {exc.code}: "
                f"{error_body}"
            ) from exc

        except urllib.error.URLError as exc:

            raise RuntimeError(
                f"Gemini connection failed: "
                f"{exc.reason}"
            ) from exc

        except TimeoutError as exc:

            raise RuntimeError(
                "Gemini request timed out."
            ) from exc

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Gemini returned an invalid response."
            )

        error = data.get("error")

        if isinstance(error, dict):
            raise RuntimeError(
                f"Gemini error: "
                f"{error.get('message', 'Unknown error.')}"
            )

        choices = data.get("choices")

        if not isinstance(choices, list) or not choices:
            raise RuntimeError(
                f"Gemini returned no choices: {data}"
            )

        message = choices[0].get("message", {})

        if isinstance(message, dict):
            content = message.get("content")

            if isinstance(content, str) and content.strip():
                return content.strip()

        raise RuntimeError(
            f"Gemini returned no text: {data}"
        )


class LLMFallbackManager:

    def __init__(self):
        self.providers = [
            OpenRouterClient(),
            DeepSeekClient(),
            GeminiClient(),
            FreeLLMAPIClient(),
        ]

        self.last_provider = None
        self.last_error = None

    @property
    def available(self):
        return any(
            provider.available
            for provider in self.providers
        )

    @property
    def model(self):
        if self.last_provider:
            return self.last_provider.model

        for provider in self.providers:
            if provider.available:
                return provider.model

        return None

    @property
    def provider_name(self):
        if self.last_provider:
            return self.last_provider.provider_name

        return None

    async def complete(
        self,
        prompt,
        system_prompt=None,
        temperature=0.2,
        max_tokens=2048,
    ):
        errors = []

        for provider in self.providers:

            if not provider.available:
                continue

            try:
                response = await provider.complete(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                response = str(
                    response or ""
                ).strip()

                if not response:
                    raise RuntimeError(
                        "Provider returned empty response."
                    )

                self.last_provider = provider
                self.last_error = None

                return response

            except Exception as exc:

                message = str(exc)

                errors.append(
                    f"{provider.provider_name}: {message}"
                )

                self.last_error = message

        raise RuntimeError(
            "All configured LLM providers failed. "
            + " | ".join(errors)
        )

    async def chat(
        self,
        messages,
        temperature=0.2,
        max_tokens=2048,
    ):
        errors = []

        for provider in self.providers:

            if not provider.available:
                continue

            try:
                response = await provider.chat(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                response = str(
                    response or ""
                ).strip()

                if not response:
                    raise RuntimeError(
                        "Provider returned empty response."
                    )

                self.last_provider = provider
                self.last_error = None

                return response

            except Exception as exc:

                message = str(exc)

                errors.append(
                    f"{provider.provider_name}: {message}"
                )

                self.last_error = message

        raise RuntimeError(
            "All configured LLM providers failed. "
            + " | ".join(errors)
        )

    async def generate(
        self,
        prompt,
        system_prompt=None,
        temperature=0.2,
        max_tokens=2048,
    ):
        return await self.complete(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )


