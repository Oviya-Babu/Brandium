"""Document text extraction for Brand History ingestion (Technology Stack
§12: PyMuPDF for PDF, python-docx for Word). Extracted text is untrusted
input (CLAUDE.md §4.4) — it is stored and later passed to the LLM only
through `shared_kernel.llm.client`'s data-boundary wrapping, never
concatenated directly into an instruction-bearing prompt.
"""
from __future__ import annotations


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import fitz  # PyMuPDF

    text_parts: list[str] = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    import io

    import docx

    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_text(file_bytes: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    if content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return extract_text_from_docx(file_bytes)
    if content_type.startswith("text/"):
        return file_bytes.decode("utf-8", errors="replace")
    raise ValueError(f"Unsupported document content type for text extraction: {content_type}")
