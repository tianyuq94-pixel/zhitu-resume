import asyncio

import pytest

from app.ai.client import AICompletion
from app.ai.custom_resume import generate_custom_resume
from app.core.config import Settings
from app.schemas.custom_resume import (
    GeneratedCustomResumeResult,
    build_editable_sections,
    validate_generated_custom_resume,
)


RESUME_TEXT = """项目经历：AI 求职助手网站。
使用 Vue 和 TypeScript 开发响应式页面，使用 FastAPI 开发后端接口。
负责简历上传校验、文字解析和页面交互。
"""

JOB_DESCRIPTION = """岗位职责：使用 Vue 和 TypeScript 开发前端业务页面。
岗位要求：熟悉 Linux 常用命令，掌握 MySQL 数据库基础。
"""

VALID_RESULT = {
    "sections": [
        {
            "title": "项目经历",
            "items": [
                {
                    "source_text": "使用 Vue 和 TypeScript 开发响应式页面，使用 FastAPI 开发后端接口。",
                    "suggested_text": "使用 Vue 和 TypeScript 开发响应式页面，并通过 FastAPI 完成后端接口开发。",
                    "reason": "突出与目标岗位直接相关的前端技术栈。",
                },
                {
                    "source_text": "负责简历上传校验、文字解析和页面交互。",
                    "suggested_text": "负责页面交互，并完成简历上传校验与文字解析。",
                    "reason": "把页面交互职责提前以匹配前端岗位。",
                },
            ],
        }
    ],
    "missing_information_warnings": ["主简历中未体现 Linux 常用命令，不能直接添加。"],
}


class FakeClient:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls = 0

    async def complete_json(self, system_prompt: str, user_prompt: str) -> AICompletion:
        assert "不得编造" in system_prompt
        assert '"job_title"' in user_prompt
        self.calls += 1
        return AICompletion(data=self.result, input_tokens=160, output_tokens=120)


def test_custom_resume_accepts_only_source_based_changes() -> None:
    result = GeneratedCustomResumeResult.model_validate(VALID_RESULT)
    validate_generated_custom_resume(result, RESUME_TEXT)
    sections = build_editable_sections(result)
    assert sections[0]["items"][0]["decision"] == "pending"
    assert sections[0]["items"][0]["final_text"] == sections[0]["items"][0]["source_text"]


def test_custom_resume_rejects_new_number() -> None:
    payload = {
        **VALID_RESULT,
        "sections": [
            {
                **VALID_RESULT["sections"][0],
                "items": [
                    {
                        **VALID_RESULT["sections"][0]["items"][0],
                        "suggested_text": "独立完成 3 个 Vue 页面开发。",
                    },
                    VALID_RESULT["sections"][0]["items"][1],
                ],
            }
        ],
    }
    result = GeneratedCustomResumeResult.model_validate(payload)
    with pytest.raises(ValueError, match="不存在的数字"):
        validate_generated_custom_resume(result, RESUME_TEXT)


def test_custom_resume_rejects_new_factual_phrase() -> None:
    payload = {
        **VALID_RESULT,
        "sections": [
            {
                **VALID_RESULT["sections"][0],
                "items": [
                    {
                        **VALID_RESULT["sections"][0]["items"][0],
                        "suggested_text": "使用 Vue 和 TypeScript 开发响应式页面，承担团队管理工作。",
                    },
                    VALID_RESULT["sections"][0]["items"][1],
                ],
            }
        ],
    }
    result = GeneratedCustomResumeResult.model_validate(payload)
    with pytest.raises(ValueError, match="事实性中文词语"):
        validate_generated_custom_resume(result, RESUME_TEXT)


def test_custom_resume_generation_returns_validated_result() -> None:
    client = FakeClient(VALID_RESULT)
    settings = Settings(
        auth_secret="test-only-auth-secret-with-more-than-32-characters",
        deepseek_api_key=None,
        deepseek_max_attempts=3,
    )
    generated = asyncio.run(
        generate_custom_resume(
            RESUME_TEXT,
            {"career_direction": "前端开发"},
            "前端开发工程师",
            "示例科技",
            JOB_DESCRIPTION,
            client=client,
            settings=settings,
        )
    )
    assert generated.result.sections[0].title == "项目经历"
    assert client.calls == 1
