"""
services/text_extractor.py — Shared text extraction service.

Extracts plain text from PDF (PyMuPDF), DOCX (python-docx) and TXT files.
Used by both the JD module (Phase 1) and the resume parser (Phase 2).

Public API:
    extract_text(file_bytes: bytes, filename: str) -> str
"""

import re
import unicodedata
from pathlib import PurePosixPath

try:
    import pymupdf as fitz     # Modern PyMuPDF API
except ImportError:
    import fitz                # Fallback
from docx import Document      # python-docx

from app.core.exceptions import (
    UnsupportedFileTypeError,
    EmptyFileError,
    ScannedPDFError,
    CorruptFileError,
)


# File extensions this service can handle
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------

def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from a file given its raw bytes and filename.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename:   Original filename (used to detect format via extension).

    Returns:
        Cleaned plain text string.

    Raises:
        EmptyFileError:          file_bytes is empty.
        UnsupportedFileTypeError: extension not in SUPPORTED_EXTENSIONS.
        ScannedPDFError:         PDF has no extractable text (image-only).
        CorruptFileError:        File could not be parsed.
    """
    if not file_bytes:
        raise EmptyFileError(filename)

    ext = _get_extension(filename)

    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(filename, list(SUPPORTED_EXTENSIONS))

    # Dispatch to the right extractor
    if ext == ".pdf":
        raw = _extract_pdf(file_bytes, filename)
    elif ext == ".docx":
        raw = _extract_docx(file_bytes, filename)
    else:  # .txt
        raw = _extract_txt(file_bytes, filename)

    # Clean and normalize the text
    cleaned = _clean_text(raw)

    if not cleaned.strip():
        raise ScannedPDFError(filename) if ext == ".pdf" else EmptyFileError(filename)

    return cleaned


# ------------------------------------------------------------------
# Private extractors
# ------------------------------------------------------------------

def _get_extension(filename: str) -> str:
    """Return the lowercase file extension, e.g. '.pdf'."""
    return PurePosixPath(filename).suffix.lower()


def _extract_pdf(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from a PDF using PyMuPDF (fitz).

    Iterates over every page and concatenates the text blocks.
    Raises CorruptFileError if fitz cannot open the file.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise CorruptFileError(filename, str(exc))

    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()

    return "\n".join(pages)


def _extract_docx(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from a DOCX file using python-docx.

    Extracts from both paragraphs and table cells so that
    tabular content (common in resumes) is not lost.
    """
    import io

    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise CorruptFileError(filename, str(exc))

    parts: list[str] = []

    # 1. Paragraphs
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)

    # 2. Tables (row by row, cell by cell)
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(
                cell.text.strip() for cell in row.cells if cell.text.strip()
            )
            if row_text:
                parts.append(row_text)

    return "\n".join(parts)


def _extract_txt(file_bytes: bytes, filename: str) -> str:
    """
    Decode a plain-text file (UTF-8 with latin-1 fallback).
    """
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return file_bytes.decode("latin-1")
        except UnicodeDecodeError:
            raise CorruptFileError(filename, "Unable to decode text file.")


# ------------------------------------------------------------------
# Text cleaning / normalization
# ------------------------------------------------------------------

def _clean_text(text: str) -> str:
    """
    Normalize extracted text so downstream parsers get consistent input.

    Steps:
      1. Unicode normalization (NFC).
      2. Replace common bullet characters with a standard dash.
      3. Fix soft-hyphenation (re-join split words).
      4. Collapse multiple blank lines into one.
      5. Collapse runs of whitespace within a line.
      6. Strip leading/trailing whitespace.
    """
    # 1. Unicode normalize
    text = unicodedata.normalize("NFC", text)

    # 2. Standardise bullets:  •, ●, ○, ◦, ▪, ▸, ▹, ►, ➤, ★, ✓, ✔, ➢, ■ → "- "
    text = re.sub(r"[•●○◦▪▸▹►➤★✓✔➢■]", "- ", text)

    # 3. Re-join soft-hyphenated words (e.g. "pro-\ngramming" → "programming")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # 4. Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 5. Collapse runs of spaces/tabs within a line (keep newlines)
    text = re.sub(r"[^\S\n]+", " ", text)

    # 6. Strip each line, then strip the whole string
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    return text.strip()
