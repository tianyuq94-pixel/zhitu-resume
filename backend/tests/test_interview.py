import asyncio

import pytest

from app.ai.client import AICompletion
from app.ai.interview import (
    evaluate_interview_answer,
    generate_interview_questions,
    generate_interview_report,
)
from app.core.config import Settings
from app.schemas.interview import (
    GeneratedInterviewQuestions,
    InterviewQuestionFeedback,
    validate_generated_questions,
    validate_question_feedback,
)


RESUME_TEXT = """项目经历：AI 求职助手网站。
使用 Vue 和 TypeScript 开发响应式页面，使用 FastAPI 开发后端接口。
负责简历上传校验、文字解析和页面交互。
使用 MySQL 设计用户、简历与岗位匹配数据表。
"""
JOB_REQUIREMENTS = """使用 Vue 和 TypeScript 开发前端页面，了解 MySQL，具备团队协作能力。"""

QUESTIONS_RESULT = {
    "questions": [
        {
            "sequence_no": 1,
            "question_text": "请介绍 AI 求职助手网站中最能体现前端开发能力的一项工作。",
            "focus_area": "项目深挖",
            "resume_evidence": "AI 求职助手网站",
            "job_evidence": "使用 Vue 和 TypeScript 开发前端页面",
        },
        {
            "sequence_no": 2,
            "question_text": "你如何使用 Vue 和 TypeScript 设计响应式页面并保证可维护性？",
            "focus_area": "前端能力",
            "resume_evidence": "使用 Vue 和 TypeScript 开发响应式页面",
            "job_evidence": "Vue 和 TypeScript",
        },
        {
            "sequence_no": 3,
            "question_text": "如果前端接口联调出现数据异常，你会怎样定位并解决问题？",
            "focus_area": "问题处理",
            "resume_evidence": None,
            "job_evidence": "前端页面",
        },
        {
            "sequence_no": 4,
            "question_text": "请说明你在团队协作中如何同步进度并处理意见分歧。",
            "focus_area": "团队协作",
            "resume_evidence": None,
            "job_evidence": "团队协作能力",
        },
        {
            "sequence_no": 5,
            "question_text": "你为什么选择前端开发工程师岗位，接下来最想提升什么？",
            "focus_area": "求职动机",
            "resume_evidence": None,
            "job_evidence": "前端开发工程师",
        },
    ]
}

FEEDBACK_RESULT = {
    "score": 72,
    "dimension_scores": {"relevance": 80, "specificity": 62, "structure": 70, "communication": 76},
    "strengths": ["回答直接说明了使用的前端技术栈。"],
    "issues": ["缺少具体问题、行动和结果，经历证明不够完整。"],
    "suggestions": ["补充一个真实的开发难点。", "按情境、行动和真实结果组织回答。"],
    "answer_outline": ["概括项目目标", "说明真实任务", "描述真实行动", "总结真实结果与复盘"],
}

REPORT_RESULT = {
    "overall_score": 72,
    "summary": "五道回答能够围绕前端岗位展开，但经历证明和回答结构仍需进一步加强。",
    "dimension_scores": {
        "expression": 76,
        "role_understanding": 74,
        "experience_evidence": 65,
        "answer_structure": 72,
    },
    "strengths": ["能够围绕岗位问题作答。", "技术方向表达较清楚。"],
    "improvements": ["增加真实经历中的行动细节。", "用固定结构组织复杂回答。"],
    "practice_focus": ["练习项目深挖题", "练习情境题结构", "整理真实成果和复盘"],
}


class QueueClient:
    def __init__(self, results: list[dict]) -> None:
        self.results = results
        self.calls = 0

    async def complete_json(self, system_prompt: str, user_prompt: str) -> AICompletion:
        result = self.results[self.calls]
        self.calls += 1
        return AICompletion(data=result, input_tokens=180, output_tokens=140)


def settings() -> Settings:
    return Settings(
        auth_secret="test-only-auth-secret-with-more-than-32-characters",
        deepseek_api_key=None,
        deepseek_max_attempts=3,
    )


def test_interview_questions_require_job_and_resume_evidence() -> None:
    result = GeneratedInterviewQuestions.model_validate(QUESTIONS_RESULT)
    validate_generated_questions(result, RESUME_TEXT, "前端开发工程师", JOB_REQUIREMENTS)


def test_interview_questions_reject_invented_resume_evidence() -> None:
    payload = {"questions": [dict(item) for item in QUESTIONS_RESULT["questions"]]}
    payload["questions"][0]["resume_evidence"] = "独立带领五人团队"
    result = GeneratedInterviewQuestions.model_validate(payload)
    with pytest.raises(ValueError, match="不在主简历"):
        validate_generated_questions(result, RESUME_TEXT, "前端开发工程师", JOB_REQUIREMENTS)


def test_generate_interview_questions() -> None:
    client = QueueClient([QUESTIONS_RESULT])
    generated = asyncio.run(
        generate_interview_questions(
            RESUME_TEXT,
            {"career_direction": "前端开发"},
            "前端开发工程师",
            "示例科技",
            JOB_REQUIREMENTS,
            client=client,
            settings=settings(),
        )
    )
    assert len(generated.result.questions) == 5
    assert client.calls == 1


def test_feedback_rejects_new_factual_number() -> None:
    feedback = InterviewQuestionFeedback.model_validate(
        {**FEEDBACK_RESULT, "suggestions": ["补充真实的文件大小限制，例如 10MB。", "说明处理流程。"]}
    )
    with pytest.raises(ValueError, match="事实性数字"):
        validate_question_feedback(feedback, "用户回答没有提供具体大小限制。")


def test_feedback_rejects_new_technical_term() -> None:
    feedback = InterviewQuestionFeedback.model_validate(
        {**FEEDBACK_RESULT, "strengths": ["回答体现了 React 开发能力。"]}
    )
    with pytest.raises(ValueError, match="英文技术"):
        validate_question_feedback(feedback, "岗位与回答只提到了 Vue 和 TypeScript。")


def test_evaluate_answer_and_generate_report() -> None:
    feedback_client = QueueClient([FEEDBACK_RESULT])
    feedback = asyncio.run(
        evaluate_interview_answer(
            "前端开发工程师",
            "示例科技",
            JOB_REQUIREMENTS,
            QUESTIONS_RESULT["questions"][0]["question_text"],
            "我使用 Vue 和 TypeScript 完成页面开发，并负责接口联调。",
            client=feedback_client,
            settings=settings(),
        )
    )
    assert feedback.result.score == 72

    report_client = QueueClient([REPORT_RESULT])
    report = asyncio.run(
        generate_interview_report(
            "前端开发工程师",
            "示例科技",
            JOB_REQUIREMENTS,
            [{"question_text": "问题", "answer_text": "回答", "feedback": FEEDBACK_RESULT}] * 5,
            client=report_client,
            settings=settings(),
        )
    )
    assert report.result.overall_score == 72
