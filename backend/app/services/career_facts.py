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
        ("Personal supplement", data.about), ("Add skills", data.skills), ("Add experience", data.experiences)
    ] if value)


def factual_resume(user, resume_text: str) -> str:
    extra = facts_text(user)
    return resume_text + ("\n\n[User-confirmed non-CV material: select only what is relevant to the role; not everything needs to go into the CV]\n" + extra if extra else "")
