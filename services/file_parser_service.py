# services/file_parser_service.py
import fitz  # PyMuPDF
import pandas as pd
from services.token_truncation import truncate_to_model_context

def parse_file(file, model_key="default") -> tuple[str, bool]:
    """Detect file type and parse with token limit awareness."""
    content_type = file.type
    file_name = file.name.lower()

    if content_type == "application/pdf":
        raw = _parse_pdf(file)
    elif content_type == "text/plain" or file_name.endswith((".txt", ".py", ".md")):
        raw = _parse_txt(file)
    elif content_type == "text/csv":
        raw = _parse_csv(file)
    elif content_type in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel"
    ):
        raw = _parse_xlsx(file)
    else:
        raw = ""

    truncated = truncate_to_model_context(raw, model_key)
    was_truncated = len(truncated) < len(raw)

    return truncated, was_truncated


def _parse_pdf(file) -> str:
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

def _parse_txt(file) -> str:
    return file.read().decode("utf-8", errors="ignore")

def _parse_csv(file) -> str:
    df = pd.read_csv(file)
    return df.to_string(index=False)

def _parse_xlsx(file) -> str:
    df = pd.read_excel(file)
    return df.to_string(index=False)
