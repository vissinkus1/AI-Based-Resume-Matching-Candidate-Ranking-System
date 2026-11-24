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
    Extract text from a PDF using PyMuPDF (fitz) with column-aware reading order.

    Handles standard 1-column layouts, top headers, and 2-column sidebar layouts
    by sorting text blocks geometrically:
      1. Top header blocks spanning across columns (e.g. name, contact info)
      2. Left column blocks sorted by y
      3. Right column blocks sorted by y
      4. Single column fallback sorted by y
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise CorruptFileError(filename, str(exc))

    pages: list[str] = []
    for page in doc:
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height

        # Get text blocks: (x0, y0, x1, y1, text, block_no, block_type)
        raw_blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
        if not raw_blocks:
            continue

        # Check if the page displays a multi-column layout
        # A 2-column layout typically has blocks clearly separated across mid_x
        mid_x = page_width / 2.0
        left_blocks = []
        right_blocks = []
        header_blocks = []
        full_width_blocks = []

        # Find potential 2-column separation
        has_left = any(b[2] < mid_x + 20 and b[0] < mid_x * 0.7 for b in raw_blocks)
        has_right = any(b[0] > mid_x - 20 and b[2] > mid_x * 1.3 for b in raw_blocks)
        is_two_column = has_left and has_right

        if is_two_column:
            for b in raw_blocks:
                x0, y0, x1, y1, text, bno, btype = b
                # Top header (name, contact info spanning near top)
                if y0 < page_height * 0.25 and (x1 - x0 > page_width * 0.5 or (x0 < mid_x and x1 > mid_x)):
                    header_blocks.append(b)
                elif x1 <= mid_x + 30:
                    left_blocks.append(b)
                elif x0 >= mid_x - 30:
                    right_blocks.append(b)
                else:
                    full_width_blocks.append(b)

            # Sort each group top-to-bottom
            header_blocks.sort(key=lambda b: (b[1], b[0]))
            left_blocks.sort(key=lambda b: (b[1], b[0]))
            right_blocks.sort(key=lambda b: (b[1], b[0]))
            full_width_blocks.sort(key=lambda b: (b[1], b[0]))

            # Reading order: header -> left column -> right column -> full width
            ordered_blocks = header_blocks + left_blocks + right_blocks + full_width_blocks
        else:
            # Standard single-column: top-to-bottom reading order
            ordered_blocks = sorted(raw_blocks, key=lambda b: (b[1], b[0]))

        page_text = "\n".join(b[4].strip() for b in ordered_blocks if b[4].strip())
        if page_text:
            pages.append(page_text)

    doc.close()
    return "\n\n".join(pages)


def _extract_docx(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from a DOCX file using python-docx.

    Extracts from headers, paragraphs, and table cells so that
    all resume content (including contact tables and sidebars) is captured.
    """
    import io

    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise CorruptFileError(filename, str(exc))

    parts: list[str] = []

    # 1. Section headers (some resumes place contact info in headers)
    for section in doc.sections:
        if section.header:
            for para in section.header.paragraphs:
                text = para.text.strip()
                if text and text not in parts:
                    parts.append(text)

    # 2. Main paragraphs
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            parts.append(text)

    # 3. Tables (row by row, cell by cell)
    for table in doc.tables:
        for row in table.rows:
            # Extract distinct cell texts to avoid duplicates from merged cells
            seen_cells = set()
            cell_texts = []
            for cell in row.cells:
                t = cell.text.strip()
                if t and t not in seen_cells:
                    seen_cells.add(t)
                    cell_texts.append(t)
            if cell_texts:
                parts.append(" | ".join(cell_texts))

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

    # 1b. Normalize ligatures
    text = (
        text.replace("ﬁ", "fi")
        .replace("ﬂ", "fl")
        .replace("ﬀ", "ff")
        .replace("ﬃ", "ffi")
        .replace("ﬄ", "ffl")
    )

    # 2. Standardise bullets:  •, ●, ○, ◦, ▪, ▸, ▹, ►, ➤, ★, ✓, ✔, ➢, ■ → "- "
    text = re.sub(r"[•●○◦▪▸▹►➤★✓✔➢■]", "- ", text)

    # 2b. Standardise PDF question-mark bullet artifacts at line starts
    text = re.sub(r"(?m)^\s*\?\s+", "- ", text)

    # 2c. Fix PDF font en-dash extraction artifacts in date ranges: e.g. "2020 ? Present" or "Jan 2020 ? Mar 2022"
    text = re.sub(
        r"(\b(?:19|20)\d{2}|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)\s*[\?\ufffd]\s*(\b(?:19|20)\d{2}|present|current)",
        r"\1 - \2",
        text,
        flags=re.IGNORECASE,
    )

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
