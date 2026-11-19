"""
generate_sample_files.py — Generate PDF and DOCX versions of sample JDs.

Run from the backend directory:
    python -m scripts.generate_sample_files

Creates:
    sample_data/jds/react_frontend_jd.docx
    sample_data/jds/aiml_engineer_jd.pdf
"""

import sys
from pathlib import Path

# Add backend to path so we can import app modules
BACKEND_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BACKEND_DIR.parent / "sample_data" / "jds"


def generate_docx(text: str, output_path: Path) -> None:
    """Generate a DOCX file from plain text."""
    from docx import Document

    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(str(output_path))
    print(f"  Created: {output_path}")


def generate_pdf(text: str, output_path: Path) -> None:
    """Generate a PDF file from plain text using PyMuPDF (fitz)."""
    import fitz

    doc = fitz.open()  # New empty PDF
    # Split text into pages (~50 lines per page)
    lines = text.split("\n")
    lines_per_page = 50

    for page_start in range(0, len(lines), lines_per_page):
        page = doc.new_page(width=612, height=792)  # Letter size
        page_lines = lines[page_start:page_start + lines_per_page]
        page_text = "\n".join(page_lines)

        # Insert text at the top of the page
        rect = fitz.Rect(50, 50, 562, 742)  # Margins
        page.insert_textbox(
            rect,
            page_text,
            fontsize=11,
            fontname="helv",
        )

    doc.save(str(output_path))
    doc.close()
    print(f"  Created: {output_path}")


def main():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    # Read the React frontend JD (will become .docx)
    react_txt = SAMPLE_DIR / "react_frontend_jd.txt"
    if react_txt.exists():
        text = react_txt.read_text(encoding="utf-8")
        generate_docx(text, SAMPLE_DIR / "react_frontend_jd.docx")
    else:
        print(f"  WARNING: {react_txt} not found, skipping DOCX generation")

    # Read the AI/ML engineer JD (will become .pdf)
    aiml_txt = SAMPLE_DIR / "aiml_engineer_jd.txt"
    if aiml_txt.exists():
        text = aiml_txt.read_text(encoding="utf-8")
        generate_pdf(text, SAMPLE_DIR / "aiml_engineer_jd.pdf")
    else:
        print(f"  WARNING: {aiml_txt} not found, skipping PDF generation")

    print("\nDone! Sample files generated.")


if __name__ == "__main__":
    main()
