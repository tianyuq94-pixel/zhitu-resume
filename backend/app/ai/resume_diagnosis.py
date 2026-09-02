import asyncio
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.ai.client import DeepSeekClient
from app.ai.errors import AIServiceError
from app.ai.prompts.resume_diagnosis import PROMPT_VERSION, SYSTEM_PROMPT, build_user_prompt
from app.core.config import Settings, get_settings
from app.schemas.diagnosis import ResumeDiagnosisResult, validate_diagnosis_facts


@dataclass(frozen=True)
class GeneratedDiagnosis:
    result: ResumeDiagnosisResult
    input_tokens: int | None
    output_tokens: int | None


async def generate_resume_diagnosis(
    resume_text: str,
    profile: dict[str, Any],
    *,
    client: DeepSeekClient | None = None,
    settings: Settings | None = None,
) -> GeneratedDiagnosis:
    active_settings = settings or get_settings()
    if len(resume_text) > active_settings.ai_resume_max_chars:
        raise AIServiceError("AI_INPUT_TOO_LONG", "Resume text is too long")

    active_client = client or DeepSeekClient(active_settings)
    user_prompt = build_user_prompt(profile, resume_text)
    last_error: AIServiceError | None = None

    for attempt in range(active_settings.deepseek_max_attempts):
        try:
            completion = await active_client.complete_json(SYSTEM_PROMPT, user_prompt)
            result = ResumeDiagnosisResult.model_validate(completion.data)
            validate_diagnosis_facts(result, resume_text)
            return GeneratedDiagnosis(
                result=result,
                input_tokens=completion.input_tokens,
                output_tokens=completion.output_tokens,
            )
        except ValidationError as exc:
            last_error = AIServiceError(
                "AI_RESPONSE_INVALID",
                "DeepSeek response did not match the diagnosis schema",
                retryable=True,
            )
            last_error.__cause__ = exc
        except ValueError as exc:
            last_error = AIServiceError(
                "AI_RESPONSE_UNSAFE",
                str(exc),
                retryable=True,
            )
        except AIServiceError as exc:
            last_error = exc

        if last_error is not None and (not last_error.retryable or attempt + 1 >= active_settings.deepseek_max_attempts):
            raise last_error
        await asyncio.sleep(0.35 * (attempt + 1))

    raise last_error or AIServiceError("AI_RESPONSE_INVALID", "Unable to generate diagnosis")

