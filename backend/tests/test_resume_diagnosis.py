import asyncio

import pytest

from app.ai.client import AICompletion, DeepSeekClient
from app.ai.errors import AIServiceError
from app.ai.resume_diagnosis import generate_resume_diagnosis
from app.core.config import Settings
from app.schemas.diagnosis import ResumeDiagnosisResult, validate_diagnosis_facts


RESUME_TEXT = """项目经历
AI 求职助手网站：使用 Vue、TypeScript、FastAPI 和 MySQL 完成主简历上传与解析。
负责接口设计和页面开发，文件解析成功率达到 98%。
"""

VALID_RESULT = {
    "overall_score": 78,
    "dimension_scores": {
        "information_completeness": 75,
        "content_quality": 82,
        "achievement_quantification": 80,
        "professional_expression": 78,
        "career_direction_fit": 76,
    },
    "strengths": ["技术栈表达明确", "项目职责清晰", "包含量化结果"],
    "issues": ["教育信息未体现", "缺少项目周期", "求职方向不够明确"],
    "suggestions": [
        {
            "source_text": "负责接口设计和页面开发，文件解析成功率达到 98%。",
            "suggested_text": "负责接口设计与页面开发，文件解析成功率达到 98%。",
            "reason": "用词更加紧凑专业。",
        }
    ],
}


class FakeClient:
    def __init__(self, results: list[dict]) -> None:
        self.results = results
        self.calls = 0

    async def complete_json(self, system_prompt: str, user_prompt: str) -> AICompletion:
        assert "JSON" in system_prompt
        assert '"resume_text"' in user_prompt
        result = self.results[min(self.calls, len(self.results) - 1)]
        self.calls += 1
        return AICompletion(data=result, input_tokens=120, output_tokens=80)


def test_valid_diagnosis_references_original_resume() -> None:
    result = ResumeDiagnosisResult.model_validate(VALID_RESULT)
    validate_diagnosis_facts(result, RESUME_TEXT)


def test_diagnosis_rejects_new_numbers() -> None:
    payload = {**VALID_RESULT, "suggestions": [{**VALID_RESULT["suggestions"][0], "suggested_text": "将成功率提升至 100%。"}]}
    result = ResumeDiagnosisResult.model_validate(payload)
    with pytest.raises(ValueError, match="数字"):
        validate_diagnosis_facts(result, RESUME_TEXT)


def test_generation_retries_invalid_schema_then_succeeds() -> None:
    client = FakeClient([{"overall_score": 80}, VALID_RESULT])
    settings = Settings(
        auth_secret="test-only-auth-secret-with-more-than-32-characters",
        deepseek_api_key=None,
        deepseek_max_attempts=3,
    )
    generated = asyncio.run(
        generate_resume_diagnosis(
            RESUME_TEXT,
            {"career_direction": "前端开发"},
            client=client,
            settings=settings,
        )
    )
    assert generated.result.overall_score == 78
    assert client.calls == 2


def test_missing_api_key_returns_configuration_error() -> None:
    settings = Settings(
        auth_secret="test-only-auth-secret-with-more-than-32-characters",
        deepseek_api_key=None,
    )
    client = DeepSeekClient(settings)
    with pytest.raises(AIServiceError) as error:
        asyncio.run(client.complete_json("output JSON", "test"))
    assert error.value.code == "AI_NOT_CONFIGURED"
