import json
from dataclasses import dataclass
from typing import Any

import httpx2 as httpx

from app.ai.errors import AIServiceError
from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class AICompletion:
    data: dict[str, Any]
    input_tokens: int | None
    output_tokens: int | None


class DeepSeekClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def complete_json(self, system_prompt: str, user_prompt: str) -> AICompletion:
        api_key = (
            self.settings.deepseek_api_key.get_secret_value().strip()
            if self.settings.deepseek_api_key is not None
            else ""
        )
        if not api_key:
            raise AIServiceError("AI_NOT_CONFIGURED", "DeepSeek API key is not configured")

        url = f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "temperature": 0.2,
            "max_tokens": self.settings.deepseek_max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.deepseek_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise AIServiceError("AI_TIMEOUT", "DeepSeek request timed out", retryable=True) from exc
        except httpx.RequestError as exc:
            raise AIServiceError("AI_UNAVAILABLE", "DeepSeek request failed", retryable=True) from exc

        if response.status_code in {401, 403}:
            raise AIServiceError("AI_AUTH_FAILED", "DeepSeek API key is invalid")
        if response.status_code == 402:
            raise AIServiceError("AI_BALANCE_INSUFFICIENT", "DeepSeek account balance is insufficient")
        if response.status_code == 429:
            raise AIServiceError("AI_RATE_LIMITED", "DeepSeek rate limit reached", retryable=True)
        if response.status_code >= 500:
            raise AIServiceError("AI_UNAVAILABLE", "DeepSeek service is unavailable", retryable=True)
        if response.status_code >= 400:
            raise AIServiceError("AI_REQUEST_REJECTED", "DeepSeek rejected the request")

        try:
            response_body = response.json()
            choice = response_body["choices"][0]
            if choice.get("finish_reason") == "length":
                raise AIServiceError("AI_RESPONSE_TRUNCATED", "DeepSeek response was truncated", retryable=True)
            content = choice["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise AIServiceError("AI_RESPONSE_EMPTY", "DeepSeek returned empty content", retryable=True)
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("JSON root is not an object")
            usage = response_body.get("usage") or {}
            return AICompletion(
                data=data,
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
            )
        except AIServiceError:
            raise
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise AIServiceError("AI_RESPONSE_INVALID", "DeepSeek returned invalid JSON", retryable=True) from exc

