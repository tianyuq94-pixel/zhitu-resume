import asyncio
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.client import DeepSeekClient
from app.ai.errors import AIServiceError
from app.ai.prompts.interview import (
    FEEDBACK_SYSTEM_PROMPT,
    QUESTIONS_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    build_feedback_prompt,
    build_questions_prompt,
    build_report_prompt,
)
from app.core.config import Settings, get_settings
from app.schemas.interview import (
    GeneratedInterviewQuestions,
    InterviewFinalReport,
    InterviewQuestionFeedback,
    validate_final_report,
    validate_generated_questions,
    validate_question_feedback,
)

ResultType = TypeVar("ResultType", bound=BaseModel)


@dataclass(frozen=True)
class GeneratedInterviewResult:
    result: BaseModel
    input_tokens: int | None
    output_tokens: int | None


async def _complete_validated(
    result_type: type[ResultType],
    system_prompt: str,
    user_prompt: str,
    *,
    client: DeepSeekClient,
    settings: Settings,
    post_validate=None,
) -> GeneratedInterviewResult:
    last_error: AIServiceError | None = None
    for attempt in range(settings.deepseek_max_attempts):
        try:
            completion = await client.complete_json(system_prompt, user_prompt)
            result = result_type.model_validate(completion.data)
            if post_validate is not None:
                post_validate(result)
            return GeneratedInterviewResult(
                result=result,
                input_tokens=completion.input_tokens,
                output_tokens=completion.output_tokens,
            )
        except ValidationError as exc:
            last_error = AIServiceError(
                "AI_RESPONSE_INVALID",
                "DeepSeek response did not match the interview schema",
                retryable=True,
            )
            last_error.__cause__ = exc
        except ValueError as exc:
            last_error = AIServiceError("AI_RESPONSE_UNSAFE", str(exc), retryable=True)
        except AIServiceError as exc:
            last_error = exc

        if last_error is not None and (not last_error.retryable or attempt + 1 >= settings.deepseek_max_attempts):
            raise last_error
        await asyncio.sleep(0.35 * (attempt + 1))
    raise last_error or AIServiceError("AI_RESPONSE_INVALID", "Unable to generate interview content")


async def generate_interview_questions(
    resume_text: str,
    profile: dict[str, Any],
    job_title: str,
    company_name: str | None,
    job_requirements: str | None,
    *,
    client: DeepSeekClient | None = None,
    settings: Settings | None = None,
) -> GeneratedInterviewResult:
    active_settings = settings or get_settings()
    if len(resume_text) > active_settings.ai_resume_max_chars or len(job_requirements or "") > 20_000:
        raise AIServiceError("AI_INPUT_TOO_LONG", "Interview input is too long")
    active_client = client or DeepSeekClient(active_settings)
    return await _complete_validated(
        GeneratedInterviewQuestions,
        QUESTIONS_SYSTEM_PROMPT,
        build_questions_prompt(profile, resume_text, job_title, company_name, job_requirements),
        client=active_client,
        settings=active_settings,
        post_validate=lambda result: validate_generated_questions(
            result, resume_text, job_title, job_requirements
        ),
    )


async def evaluate_interview_answer(
    job_title: str,
    company_name: str | None,
    job_requirements: str | None,
    question_text: str,
    answer_text: str,
    *,
    client: DeepSeekClient | None = None,
    settings: Settings | None = None,
) -> GeneratedInterviewResult:
    active_settings = settings or get_settings()
    active_client = client or DeepSeekClient(active_settings)
    return await _complete_validated(
        InterviewQuestionFeedback,
        FEEDBACK_SYSTEM_PROMPT,
        build_feedback_prompt(
            job_title,
            company_name,
            job_requirements,
            question_text,
            answer_text,
        ),
        client=active_client,
        settings=active_settings,
        post_validate=lambda result: validate_question_feedback(
            result,
            "\n".join(
                part
                for part in [job_title, company_name, job_requirements, question_text, answer_text]
                if part
            ),
        ),
    )


async def generate_interview_report(
    job_title: str,
    company_name: str | None,
    job_requirements: str | None,
    answered_questions: list[dict[str, Any]],
    *,
    client: DeepSeekClient | None = None,
    settings: Settings | None = None,
) -> GeneratedInterviewResult:
    active_settings = settings or get_settings()
    active_client = client or DeepSeekClient(active_settings)
    return await _complete_validated(
        InterviewFinalReport,
        REPORT_SYSTEM_PROMPT,
        build_report_prompt(job_title, company_name, job_requirements, answered_questions),
        client=active_client,
        settings=active_settings,
        post_validate=validate_final_report,
    )
