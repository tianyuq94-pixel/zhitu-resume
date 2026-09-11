from pydantic import BaseModel, ConfigDict, Field


class CareerFacts(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    about: str = Field(default="", max_length=1500)
    skills: str = Field(default="", max_length=3500)
    experiences: str = Field(default="", max_length=10000)
    revision: int = Field(default=0, ge=0)


def facts_view(user) -> CareerFacts:
    profile = user.profile
    return CareerFacts(**(profile.extra_facts or {}), revision=profile.facts_revision or 0)


def facts_text(user) -> str:
    data = facts_view(user)
    return "\n\n".join(f"{label}\n{value}" for label, value in [
        ("个人补充", data.about), ("补充技能", data.skills), ("补充经历", data.experiences)
    ] if value)


def factual_resume(user, resume_text: str) -> str:
    extra = facts_text(user)
    return resume_text + ("\n\n【用户确认的简历外资料：只按岗位相关性选用，不必全部写入简历】\n" + extra if extra else "")
