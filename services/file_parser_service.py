# services/file_parser_service.py
import fitz  # PyMuPDF
import pandas as pd

def parse_file(file) -> str:
    """Detect file type and route to correct parser."""
    content_type = file.type

    if content_type == "application/pdf":
        return _parse_pdf(file)
    elif content_type == "text/plain":
        return _parse_txt(file)
    elif content_type == "text/csv":
        return _parse_csv(file)
    elif content_type in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel"
    ):
        return _parse_xlsx(file)
    return ""

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
