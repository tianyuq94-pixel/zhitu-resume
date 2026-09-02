import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePath
from zipfile import BadZipFile, ZipFile, is_zipfile

import pymupdf
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.ns import qn
from lxml.etree import XMLSyntaxError

from app.core.config import get_settings

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
GENERIC_MIME_TYPES = {"", "application/octet-stream"}


class ResumeParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedResume:
    text: str
    mime_type: str
    extension: str


def _normalize_text(value: str) -> str:
    value = value.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in value.splitlines()]
    normalized = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", normalized)


def _validate_text(text: str) -> str:
    settings = get_settings()
    normalized = _normalize_text(text)
    visible_text = re.sub(r"\s+", "", normalized)
    if len(visible_text) < settings.resume_min_text_chars:
        raise ResumeParseError("未识别到足够文字，请上传带有正常文字层的简历")
    if len(normalized) > settings.resume_max_text_chars:
        raise ResumeParseError("简历文字过长，请精简后重新上传")
    return normalized


def _parse_pdf(content: bytes) -> str:
    settings = get_settings()
    if not content.startswith(b"%PDF-"):
        raise ResumeParseError("文件内容不是有效的 PDF")
    try:
        with pymupdf.open(stream=content, filetype="pdf") as document:
            if document.needs_pass:
                raise ResumeParseError("暂不支持带密码的 PDF")
            if document.page_count > settings.resume_max_pdf_pages:
                raise ResumeParseError(f"PDF 页数不能超过 {settings.resume_max_pdf_pages} 页")
            return "\n\n".join(page.get_text("text") for page in document)
    except ResumeParseError:
        raise
    except (pymupdf.FileDataError, RuntimeError, ValueError) as exc:
        raise ResumeParseError("PDF 文件损坏或无法读取") from exc


def _validate_docx_package(content: bytes) -> None:
    settings = get_settings()
    stream = BytesIO(content)
    if not is_zipfile(stream):
        raise ResumeParseError("文件内容不是有效的 DOCX")
    stream.seek(0)
    try:
        with ZipFile(stream) as archive:
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ResumeParseError("文件内容不是有效的 DOCX")
            if any(name.lower().endswith("vbaproject.bin") for name in names):
                raise ResumeParseError("不支持包含宏的 Word 文件")
            if len(names) > 5000:
                raise ResumeParseError("DOCX 文件结构过于复杂")
            total_uncompressed = sum(item.file_size for item in archive.infolist())
            if total_uncompressed > settings.docx_max_uncompressed_bytes:
                raise ResumeParseError("DOCX 解压后内容过大")
            if archive.testzip() is not None:
                raise ResumeParseError("DOCX 文件损坏或无法读取")
    except BadZipFile as exc:
        raise ResumeParseError("DOCX 文件损坏或无法读取") from exc


def _parse_docx(content: bytes) -> str:
    _validate_docx_package(content)
    try:
        document = Document(BytesIO(content))
        paragraphs: list[str] = []
        for paragraph in document.element.body.iter(qn("w:p")):
            text = "".join(node.text or "" for node in paragraph.iter(qn("w:t"))).strip()
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs)
    except (BadZipFile, KeyError, ValueError, PackageNotFoundError, XMLSyntaxError) as exc:
        raise ResumeParseError("DOCX 文件损坏或无法读取") from exc


def parse_resume(content: bytes, original_name: str, declared_mime_type: str | None) -> ParsedResume:
    extension = PurePath(original_name.replace("\\", "/")).suffix.lower()
    declared_mime = (declared_mime_type or "").lower().split(";", maxsplit=1)[0].strip()

    if extension == ".pdf":
        if declared_mime not in GENERIC_MIME_TYPES | {PDF_MIME}:
            raise ResumeParseError("文件类型与 PDF 扩展名不一致")
        text = _parse_pdf(content)
        mime_type = PDF_MIME
    elif extension == ".docx":
        if declared_mime not in GENERIC_MIME_TYPES | {DOCX_MIME, "application/zip"}:
            raise ResumeParseError("文件类型与 DOCX 扩展名不一致")
        text = _parse_docx(content)
        mime_type = DOCX_MIME
    else:
        raise ResumeParseError("只支持 PDF 和 DOCX 文件")

    return ParsedResume(text=_validate_text(text), mime_type=mime_type, extension=extension)
