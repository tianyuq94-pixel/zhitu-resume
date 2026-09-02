from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import get_settings
from app.models.ai import CustomResume
from app.services.custom_resume_photo import get_custom_resume_photo_storage


def _register_chinese_fonts() -> tuple[str, str]:
    regular_name = "CareerResumeSans"
    bold_name = "CareerResumeSansBold"
    if regular_name in pdfmetrics.getRegisteredFontNames():
        return regular_name, bold_name

    settings = get_settings()
    pairs = [
        (settings.pdf_font_path, settings.pdf_font_path),
        (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/msyhbd.ttc")),
        (Path("C:/Windows/Fonts/simsun.ttc"), Path("C:/Windows/Fonts/simhei.ttf")),
        (
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        ),
    ]
    for regular_path, bold_path in pairs:
        if regular_path is None or bold_path is None or not regular_path.is_file() or not bold_path.is_file():
            continue
        try:
            pdfmetrics.registerFont(TTFont(regular_name, str(regular_path)))
            pdfmetrics.registerFont(TTFont(bold_name, str(bold_path)))
            pdfmetrics.registerFontFamily(
                regular_name,
                normal=regular_name,
                bold=bold_name,
                italic=regular_name,
                boldItalic=bold_name,
            )
            return regular_name, bold_name
        except (OSError, ValueError):
            continue

    fallback = "STSong-Light"
    if fallback not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(fallback))
    return fallback, fallback


def _header_story(custom_resume: CustomResume, styles: dict[str, ParagraphStyle]) -> list:
    content = custom_resume.content or {}
    header = content.get("header") or {}
    name = str(header.get("name") or "").strip()
    political_status = str(header.get("political_status") or "").strip()
    name_line = escape(name or "姓名")
    if political_status:
        name_line += f' <font size="11">（{escape(political_status)}）</font>'

    left: list = [Paragraph(name_line, styles["name"]), Spacer(1, 3.5 * mm)]
    contact_items = [
        ("联系电话", header.get("phone")),
        ("电子邮箱", header.get("email")),
        ("所在地", header.get("location")),
        ("出生年月", header.get("birth_date")),
    ]
    cells = [
        Paragraph(f"<b>{label}：</b>{escape(str(value).strip())}", styles["contact"])
        for label, value in contact_items
        if str(value or "").strip()
    ]
    if cells:
        rows = [cells[index : index + 2] for index in range(0, len(cells), 2)]
        if len(rows[-1]) == 1:
            rows[-1].append("")
        contact_table = Table(rows, colWidths=[77 * mm, 77 * mm], hAlign="LEFT")
        contact_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.4 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4 * mm),
                ]
            )
        )
        left.append(contact_table)

    photo_key = header.get("_photo_storage_key")
    photo_path = get_custom_resume_photo_storage().path_for(photo_key) if photo_key else None
    if photo_path is not None and photo_path.is_file():
        photo = Image(str(photo_path), width=25 * mm, height=34 * mm, kind="proportional")
        top_table = Table([[left, photo]], colWidths=[156 * mm, 25 * mm], hAlign="LEFT")
        top_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return [top_table, Spacer(1, 3 * mm)]
    return [*left, Spacer(1, 2 * mm)]


def build_custom_resume_pdf(custom_resume: CustomResume) -> bytes:
    regular_font, bold_font = _register_chinese_fonts()
    buffer = BytesIO()
    content = custom_resume.content or {}
    header = content.get("header") or {}
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=f"{str(header.get('name') or '').strip()}简历",
        author="职途简历",
        subject="个人简历",
    )

    base = getSampleStyleSheet()
    styles = {
        "name": ParagraphStyle(
            "ResumeName", parent=base["Title"], fontName=bold_font, fontSize=21, leading=27,
            textColor=colors.black, alignment=TA_LEFT, spaceAfter=0,
        ),
        "contact": ParagraphStyle(
            "ResumeContact", parent=base["Normal"], fontName=regular_font, fontSize=9.4,
            leading=14, textColor=colors.HexColor("#171717"),
        ),
        "section": ParagraphStyle(
            "ResumeSection", parent=base["Heading2"], fontName=bold_font, fontSize=13,
            leading=17, textColor=colors.black, spaceBefore=3 * mm, spaceAfter=1.1 * mm,
        ),
        "heading": ParagraphStyle(
            "ResumeEntryHeading", parent=base["BodyText"], fontName=bold_font, fontSize=10.2,
            leading=15.5, textColor=colors.black, spaceBefore=1.8 * mm, spaceAfter=0.8 * mm,
        ),
        "bullet": ParagraphStyle(
            "ResumeBullet", parent=base["BodyText"], fontName=regular_font, fontSize=9.6,
            leading=15.2, textColor=colors.HexColor("#151515"), leftIndent=4.2 * mm,
            firstLineIndent=-3.3 * mm, spaceAfter=1.15 * mm,
        ),
        "footer": ParagraphStyle(
            "ResumeFooter", parent=base["Normal"], fontName=regular_font, fontSize=7.5,
            leading=9, alignment=TA_CENTER, textColor=colors.HexColor("#777777"),
        ),
    }

    def item_flowable(item: dict) -> Paragraph:
        final_text = escape(str(item.get("final_text") or "").strip())
        if item.get("item_type") == "heading":
            return Paragraph(final_text, styles["heading"])
        return Paragraph("▪&nbsp;&nbsp;" + final_text, styles["bullet"])

    story = _header_story(custom_resume, styles)
    for section in content.get("sections", []):
        section_title = str(section.get("title") or "").strip()
        visible_items = [item for item in section.get("items", []) if str(item.get("final_text") or "").strip()]
        if not section_title or not visible_items:
            continue
        item_groups: list[list[Paragraph]] = []
        current_group: list[Paragraph] = []
        for item in visible_items:
            if item.get("item_type") == "heading" and current_group:
                item_groups.append(current_group)
                current_group = []
            current_group.append(item_flowable(item))
        if current_group:
            item_groups.append(current_group)

        section_lead = [
            Paragraph(escape(section_title), styles["section"]),
            HRFlowable(width="100%", thickness=0.8, color=colors.black, spaceBefore=0, spaceAfter=1.7 * mm),
            *item_groups[0],
        ]
        story.append(KeepTogether(section_lead))
        story.extend(KeepTogether(group) for group in item_groups[1:])

    def draw_footer(canvas, doc) -> None:
        canvas.saveState()
        footer = Paragraph(f"第 {doc.page} 页", styles["footer"])
        footer.wrapOn(canvas, A4[0] - 30 * mm, 6 * mm)
        footer.drawOn(canvas, 15 * mm, 6.5 * mm)
        canvas.restoreState()

    document.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return buffer.getvalue()
