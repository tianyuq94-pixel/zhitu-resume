import asyncio

import pytest

from app.ai.client import AICompletion
from app.ai.job_match import generate_job_match
from app.core.config import Settings
from app.schemas.job_match import JobMatchResult, validate_job_match_facts


RESUME_TEXT = """项目经历：AI 求职助手网站。
使用 Vue 和 TypeScript 开发响应式页面，使用 FastAPI 开发后端接口。
负责简历上传校验、文字解析和页面交互。
"""

JOB_DESCRIPTION = """岗位职责：使用 Vue 和 TypeScript 开发前端业务页面。
岗位要求：熟悉 Linux 常用命令，掌握 MySQL 数据库基础，具备团队协作能力。
"""

VALID_RESULT = {
    "match_score": 60,
    "key_requirements": [
        {"requirement": "Vue 和 TypeScript 开发", "jd_evidence": "使用 Vue 和 TypeScript 开发前端业务页面"},
        {"requirement": "Linux 常用命令", "jd_evidence": "熟悉 Linux 常用命令"},
        {"requirement": "MySQL 数据库基础", "jd_evidence": "掌握 MySQL 数据库基础"},
    ],
    "matched_items": [
        {"requirement": "Vue 和 TypeScript 开发", "resume_evidence": "使用 Vue 和 TypeScript 开发响应式页面"}
    ],
    "missing_items": [
        {"requirement": "Linux 常用命令", "explanation": "简历中未体现 Linux 相关实践"},
        {"requirement": "MySQL 数据库基础", "explanation": "简历中未明确体现 MySQL 项目经验"},
    ],
    "verdict": "consider",
    "verdict_reason": "前端技术栈已有直接证据，但部分基础能力在简历中尚未体现。",
    "improvements": ["强化前端项目中的具体职责", "如有真实经历，补充数据库或 Linux 实践"],
}


class FakeClient:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls = 0

    async def complete_json(self, system_prompt: str, user_prompt: str) -> AICompletion:
        assert "JSON" in system_prompt
        assert '"job_description"' in user_prompt
        self.calls += 1
        return AICompletion(data=self.result, input_tokens=150, output_tokens=100)


def test_valid_job_match_references_jd_and_resume() -> None:
    result = JobMatchResult.model_validate(VALID_RESULT)
    validate_job_match_facts(result, RESUME_TEXT, JOB_DESCRIPTION)


def test_job_match_rejects_invented_resume_evidence() -> None:
    payload = {
        **VALID_RESULT,
        "matched_items": [{"requirement": "Vue 和 TypeScript 开发", "resume_evidence": "熟练使用 React"}],
    }
    result = JobMatchResult.model_validate(payload)
    with pytest.raises(ValueError, match="不在简历中"):
        validate_job_match_facts(result, RESUME_TEXT, JOB_DESCRIPTION)


def test_job_match_generation_returns_validated_result() -> None:
    client = FakeClient(VALID_RESULT)
    settings = Settings(
        auth_secret="test-only-auth-secret-with-more-than-32-characters",
        deepseek_api_key=None,
        deepseek_max_attempts=3,
    )
    generated = asyncio.run(
        generate_job_match(
            RESUME_TEXT,
            {"career_direction": "前端开发"},
            "前端开发工程师",
            "示例科技",
            JOB_DESCRIPTION,
            client=client,
            settings=settings,
        )
    )
    assert generated.result.verdict == "consider"
    assert client.calls == 1
