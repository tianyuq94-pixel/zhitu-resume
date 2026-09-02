from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import desc, select, update

from app.ai.errors import AIServiceError
from app.ai.interview import (
    evaluate_interview_answer,
    generate_interview_questions,
    generate_interview_report,
)
from app.ai.prompts.interview import (
    FEEDBACK_PROMPT_VERSION,
    QUESTIONS_PROMPT_VERSION,
    REPORT_PROMPT_VERSION,
)
from app.api.ai_support import profile_payload, public_ai_error
from app.api.dependencies.auth import CurrentUser, DatabaseSession, require_csrf, require_trusted_origin
from app.core.config import get_settings
from app.models.ai import AIRequestLog, InterviewQuestion, InterviewSession, JobMatch
from app.models.resume import Resume
from app.schemas.interview import (
    GeneratedInterviewQuestions,
    InterviewAnswerRequest,
    InterviewCreateRequest,
    InterviewFinalReport,
    InterviewQuestionFeedback,
    InterviewQuestionView,
    InterviewSessionView,
)
from app.services.rate_limit import auth_rate_limiter

router = APIRouter()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _primary_resume(database: DatabaseSession, user_id: int) -> Resume | None:
    return database.scalar(select(Resume).where(Resume.user_id == user_id))


def _questions(database: DatabaseSession, session_id: int) -> list[InterviewQuestion]:
    return list(
        database.scalars(
            select(InterviewQuestion)
            .where(InterviewQuestion.session_id == session_id)
            .order_by(InterviewQuestion.sequence_no)
        ).all()
    )


def _owned_session(database: DatabaseSession, user_id: int, session_id: int) -> InterviewSession:
    session = database.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
    )
    if session is None or session.status in {"preparing", "failed"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到这次模拟面试")
    return session


def _to_view(database: DatabaseSession, session: InterviewSession) -> InterviewSessionView:
    question_views = []
    for question in _questions(database, session.id):
        feedback = (
            InterviewQuestionFeedback.model_validate(question.feedback)
            if question.feedback is not None
            else None
        )
        question_views.append(
            InterviewQuestionView(
                id=question.id,
                sequence_no=question.sequence_no,
                question_text=question.question_text,
                focus_area=question.focus_area,
                answer_text=question.answer_text,
                feedback=feedback,
                answered_at=question.answered_at,
            )
        )
    final_feedback = (
        InterviewFinalReport.model_validate(session.final_feedback)
        if session.final_feedback is not None
        else None
    )
    return InterviewSessionView(
        id=session.id,
        resume_version=session.resume_version,
        job_match_id=session.job_match_id,
        job_title=session.job_title,
        company_name=session.company_name,
        job_requirements=session.job_requirements,
        status=session.status,
        current_question_index=session.current_question_index,
        questions=question_views,
        final_feedback=final_feedback,
        started_at=session.started_at,
        completed_at=session.completed_at,
        created_at=session.created_at,
    )


def _add_ai_log(
    database: DatabaseSession,
    *,
    user_id: int,
    feature: str,
    request_id: str,
    prompt_version: str,
    started_at: float,
    status_value: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    error_code: str | None = None,
) -> None:
    database.add(
        AIRequestLog(
            user_id=user_id,
            feature=feature,
            request_id=request_id,
            model_name=get_settings().deepseek_model,
            prompt_version=prompt_version,
            status=status_value,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=round((perf_counter() - started_at) * 1000),
            error_code=error_code,
        )
    )


def _answered_payload(questions: list[InterviewQuestion]) -> list[dict]:
    return [
        {
            "sequence_no": question.sequence_no,
            "question_text": question.question_text,
            "answer_text": question.answer_text,
            "feedback": question.feedback,
        }
        for question in questions
        if question.answer_text is not None and question.feedback is not None
    ]


async def _complete_report(
    session: InterviewSession,
    questions: list[InterviewQuestion],
    response: Response,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> None:
    request_id = str(uuid4())
    response.headers["X-Request-ID"] = request_id
    started_at = perf_counter()
    try:
        generated = await generate_interview_report(
            session.job_title,
            session.company_name,
            session.job_requirements,
            _answered_payload(questions),
        )
        report = InterviewFinalReport.model_validate(generated.result)
        session.final_feedback = report.model_dump()
        session.status = "completed"
        session.completed_at = _utc_now()
        session.error_code = None
        _add_ai_log(
            database,
            user_id=current_user.id,
            feature="interview_report",
            request_id=request_id,
            prompt_version=REPORT_PROMPT_VERSION,
            started_at=started_at,
            status_value="success",
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
        )
        database.commit()
        database.refresh(session)
    except AIServiceError as exc:
        session.status = "reporting"
        session.error_code = exc.code
        _add_ai_log(
            database,
            user_id=current_user.id,
            feature="interview_report",
            request_id=request_id,
            prompt_version=REPORT_PROMPT_VERSION,
            started_at=started_at,
            status_value="timeout" if exc.code == "AI_TIMEOUT" else "failed",
            error_code=exc.code,
        )
        database.commit()
        status_code, message = public_ai_error(
            exc,
            "五道回答已保存，但综合报告暂时生成失败，请点击重试",
        )
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/current", response_model=InterviewSessionView | None)
def get_current_interview(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> InterviewSessionView | None:
    session = database.scalar(
        select(InterviewSession)
        .where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status.in_(["answering", "reporting", "completed"]),
        )
        .order_by(desc(InterviewSession.created_at), desc(InterviewSession.id))
        .limit(1)
    )
    return _to_view(database, session) if session is not None else None


@router.post(
    "",
    response_model=InterviewSessionView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
async def create_interview(
    payload: InterviewCreateRequest,
    response: Response,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> InterviewSessionView:
    resume = _primary_resume(database, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请先上传主简历")
    if resume.confirmed_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请先检查并确认简历文字")

    job_match_id = None
    if payload.job_match_id is not None:
        job_match = database.scalar(
            select(JobMatch).where(
                JobMatch.id == payload.job_match_id,
                JobMatch.user_id == current_user.id,
                JobMatch.status == "completed",
            )
        )
        if job_match is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到对应的岗位匹配结果")
        job_match_id = job_match.id

    auth_rate_limiter.check(f"interview-create:{current_user.id}", limit=5, window_seconds=3600)
    database.execute(
        update(InterviewSession)
        .where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status.in_(["answering", "reporting"]),
        )
        .values(status="abandoned")
    )
    settings = get_settings()
    session = InterviewSession(
        user_id=current_user.id,
        resume_id=resume.id,
        resume_version=resume.content_version,
        job_match_id=job_match_id,
        job_title=payload.job_title,
        company_name=payload.company_name,
        job_requirements=payload.job_requirements,
        status="preparing",
        current_question_index=0,
        model_name=settings.deepseek_model,
        prompt_version=QUESTIONS_PROMPT_VERSION,
    )
    database.add(session)
    database.commit()
    database.refresh(session)

    request_id = str(uuid4())
    response.headers["X-Request-ID"] = request_id
    started_at = perf_counter()
    try:
        generated = await generate_interview_questions(
            resume.parsed_text,
            profile_payload(current_user),
            payload.job_title,
            payload.company_name,
            payload.job_requirements,
        )
        result = GeneratedInterviewQuestions.model_validate(generated.result)
        for item in result.questions:
            database.add(
                InterviewQuestion(
                    session_id=session.id,
                    sequence_no=item.sequence_no,
                    question_text=item.question_text,
                    focus_area=item.focus_area,
                )
            )
        session.status = "answering"
        session.started_at = _utc_now()
        _add_ai_log(
            database,
            user_id=current_user.id,
            feature="interview_questions",
            request_id=request_id,
            prompt_version=QUESTIONS_PROMPT_VERSION,
            started_at=started_at,
            status_value="success",
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
        )
        database.commit()
        database.refresh(session)
        return _to_view(database, session)
    except AIServiceError as exc:
        session.status = "failed"
        session.error_code = exc.code
        _add_ai_log(
            database,
            user_id=current_user.id,
            feature="interview_questions",
            request_id=request_id,
            prompt_version=QUESTIONS_PROMPT_VERSION,
            started_at=started_at,
            status_value="timeout" if exc.code == "AI_TIMEOUT" else "failed",
            error_code=exc.code,
        )
        database.commit()
        status_code, message = public_ai_error(exc, "AI 暂时无法生成面试题，请稍后重试")
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/{session_id}", response_model=InterviewSessionView)
def get_interview(
    session_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> InterviewSessionView:
    return _to_view(database, _owned_session(database, current_user.id, session_id))


@router.post(
    "/{session_id}/answers",
    response_model=InterviewSessionView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
async def submit_interview_answer(
    session_id: int,
    payload: InterviewAnswerRequest,
    response: Response,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> InterviewSessionView:
    session = _owned_session(database, current_user.id, session_id)
    if session.status != "answering":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="这次面试当前不能继续作答")
    questions = _questions(database, session.id)
    if session.current_question_index >= len(questions):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="五道题已经全部作答")
    question = questions[session.current_question_index]
    if question.id != payload.question_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前题目已变化，请刷新页面")
    if question.answer_text is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="这道题已经提交过")

    auth_rate_limiter.check(f"interview-answer:{current_user.id}", limit=30, window_seconds=3600)
    request_id = str(uuid4())
    response.headers["X-Request-ID"] = request_id
    started_at = perf_counter()
    try:
        generated = await evaluate_interview_answer(
            session.job_title,
            session.company_name,
            session.job_requirements,
            question.question_text,
            payload.answer_text,
        )
        feedback = InterviewQuestionFeedback.model_validate(generated.result)
        question.answer_text = payload.answer_text
        question.feedback = feedback.model_dump()
        question.answered_at = _utc_now()
        session.current_question_index += 1
        if session.current_question_index == 5:
            session.status = "reporting"
        _add_ai_log(
            database,
            user_id=current_user.id,
            feature="interview_feedback",
            request_id=request_id,
            prompt_version=FEEDBACK_PROMPT_VERSION,
            started_at=started_at,
            status_value="success",
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
        )
        database.commit()
        database.refresh(session)
    except AIServiceError as exc:
        _add_ai_log(
            database,
            user_id=current_user.id,
            feature="interview_feedback",
            request_id=request_id,
            prompt_version=FEEDBACK_PROMPT_VERSION,
            started_at=started_at,
            status_value="timeout" if exc.code == "AI_TIMEOUT" else "failed",
            error_code=exc.code,
        )
        database.commit()
        status_code, message = public_ai_error(exc, "AI 暂时无法点评这次回答，请稍后重试")
        raise HTTPException(status_code=status_code, detail=message) from exc

    if session.current_question_index == 5:
        questions = _questions(database, session.id)
        await _complete_report(session, questions, response, current_user, database)
    return _to_view(database, session)


@router.post(
    "/{session_id}/report",
    response_model=InterviewSessionView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
async def retry_interview_report(
    session_id: int,
    response: Response,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> InterviewSessionView:
    session = _owned_session(database, current_user.id, session_id)
    if session.status != "reporting" or session.current_question_index != 5:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前不需要重新生成综合报告")
    auth_rate_limiter.check(f"interview-report:{current_user.id}", limit=5, window_seconds=3600)
    questions = _questions(database, session.id)
    await _complete_report(session, questions, response, current_user, database)
    return _to_view(database, session)


@router.get("/{session_id}/report", response_model=InterviewFinalReport)
def get_interview_report(
    session_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> InterviewFinalReport:
    session = _owned_session(database, current_user.id, session_id)
    if session.status != "completed" or session.final_feedback is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="完成五道题后才能查看综合报告")
    return InterviewFinalReport.model_validate(session.final_feedback)


@router.post(
    "/{session_id}/abandon",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def abandon_interview(
    session_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> Response:
    session = _owned_session(database, current_user.id, session_id)
    if session.status == "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已完成的面试无需结束")
    session.status = "abandoned"
    database.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
