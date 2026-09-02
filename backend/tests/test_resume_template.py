from io import BytesIO
from types import SimpleNamespace

import pymupdf
import pytest
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Mm

from app.schemas.custom_resume import CustomResumeView
from app.schemas.diagnosis import ResumeDiagnosisView
from app.schemas.interview import InterviewSessionView
from app.schemas.job_match import JobMatchView
from app.services.custom_resume_docx import build_custom_resume_docx
from app.services.custom_resume_pdf import build_custom_resume_pdf
from app.services.custom_resume_photo import ResumePhotoError, validate_resume_photo
from app.services.resume_header import extract_resume_header


def test_resume_header_is_extracted_from_common_labels() -> None:
    header = extract_resume_header(
        "高小吉（中共预备党员）\n"
        "联系电话：（+86）13612345678\n"
        "电子邮箱：example@hotmail.com\n"
        "家庭住址：福建省福州市\n"
        "出生年月：2001年6月\n"
        "教育经历\n"
    )
    assert header == {
        "name": "高小吉",
        "political_status": "中共预备党员",
        "phone": "13612345678",
        "email": "example@hotmail.com",
        "location": "福建省福州市",
        "birth_date": "2001年6月",
    }


def test_resume_photo_accepts_real_png_and_rejects_fake_image() -> None:
    document = pymupdf.open()
    page = document.new_page(width=120, height=160)
    page.draw_rect(page.rect, color=(0, 0, 0), fill=(1, 1, 1))
    image_bytes = page.get_pixmap().tobytes("png")
    assert validate_resume_photo(image_bytes, "image/png") == ("image/png", ".png")
    with pytest.raises(ResumePhotoError, match="只支持"):
        validate_resume_photo(b"not-an-image", "image/png")


def test_finished_resume_pdf_contains_template_content() -> None:
    custom_resume = SimpleNamespace(
        content={
            "header": {
                "name": "高小吉",
                "political_status": "中共预备党员",
                "phone": "13612345678",
                "email": "example@hotmail.com",
                "location": "福建福州",
                "birth_date": "2001年6月",
            },
            "sections": [
                {
                    "title": "教育经历",
                    "items": [
                        {"item_type": "heading", "final_text": "2020.09-2024.06 高顿大学 金融学 本科"},
                        {"item_type": "bullet", "final_text": "主修证券投资学、金融工程与统计学。"},
                    ],
                }
            ],
        }
    )
    pdf_bytes = build_custom_resume_pdf(custom_resume)
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
        text = "\n".join(page.get_text() for page in document)
        assert document.page_count == 1
        assert document.metadata["author"] == "职途简历"
    assert "高小吉" in text
    assert "教育经历" in text
    assert "高顿大学" in text
    assert "岗位定制简历" not in text


def test_finished_resume_word_is_editable_and_uses_template_structure() -> None:
    custom_resume = SimpleNamespace(
        content={
            "header": {
                "name": "高小吉",
                "political_status": "中共预备党员",
                "phone": "13612345678",
                "email": "example@hotmail.com",
                "location": "福建福州",
                "birth_date": "2001年6月",
            },
            "sections": [
                {
                    "title": "教育经历",
                    "items": [
                        {"item_type": "heading", "final_text": "2020.09-2024.06 高顿大学 金融学 本科"},
                        {"item_type": "bullet", "final_text": "主修证券投资学、金融工程与统计学。"},
                    ],
                }
            ],
        }
    )
    docx_bytes = build_custom_resume_docx(custom_resume)
    document = Document(BytesIO(docx_bytes))
    text = "\n".join(node.text for node in document.element.body.iter() if node.tag == qn("w:t"))
    bullet = next(paragraph for paragraph in document.paragraphs if paragraph.style.name == "ResumeBullet")

    assert document.core_properties.author == "职途简历"
    assert abs(document.sections[0].page_width - Mm(210)) < 1_000
    assert abs(document.sections[0].page_height - Mm(297)) < 1_000
    assert bullet._p.pPr.numPr is not None
    assert "高小吉" in text
    assert "教育经历" in text
    assert "高顿大学" in text
    assert "岗位定制简历" not in text
    assert "PAGE" in document.sections[0].footer._element.xml


def test_public_ai_responses_do_not_expose_provider_metadata() -> None:
    for schema in (ResumeDiagnosisView, JobMatchView, CustomResumeView, InterviewSessionView):
        assert "model_name" not in schema.model_fields
        assert "prompt_version" not in schema.model_fields
