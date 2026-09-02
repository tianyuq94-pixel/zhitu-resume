import re


SECTION_TITLES = {
    "教育经历",
    "教育背景",
    "科研成果",
    "参军经历",
    "实习经历",
    "项目经历",
    "实践经历",
    "比赛经历",
    "竞赛经历",
    "作品合集",
    "获奖情况",
    "技能证书",
    "爱好特长",
    "自我评价",
    "其他信息",
}


def _labeled_value(text: str, labels: tuple[str, ...], max_length: int = 100) -> str:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(rf"(?:{label_pattern})\s*[：:]\s*([^\n]{{1,{max_length}}})", text)
    return match.group(1).strip() if match else ""


def extract_resume_header(resume_text: str) -> dict[str, str]:
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    name = _labeled_value(resume_text, ("姓名",), 40)
    political_status = _labeled_value(resume_text, ("政治面貌",), 40)

    if not name:
        for line in lines[:15]:
            compact = re.sub(r"\s+", "", line)
            if len(compact) > 30 or any(marker in line for marker in ("@", "：", ":")):
                continue
            plain_title = re.sub(r"[（(].*?[）)]", "", compact)
            if plain_title in SECTION_TITLES:
                continue
            match = re.fullmatch(r"([\u3400-\u9fff·]{2,10})(?:[（(]([^）)]+)[）)])?", compact)
            if match:
                name = match.group(1)
                if not political_status and match.group(2):
                    political_status = match.group(2).strip()
                break

    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", resume_text)
    phone_match = re.search(r"(?<!\d)(?:\+?86[\s-]?)?1[3-9]\d(?:[\s-]?\d){8}(?!\d)", resume_text)

    return {
        "name": name,
        "political_status": political_status,
        "phone": re.sub(r"\s+", " ", phone_match.group(0)).strip() if phone_match else "",
        "email": email_match.group(0) if email_match else "",
        "location": _labeled_value(resume_text, ("家庭住址", "现居地", "所在地", "户籍所在地")),
        "birth_date": _labeled_value(resume_text, ("出生年月", "出生日期"), 40),
    }
