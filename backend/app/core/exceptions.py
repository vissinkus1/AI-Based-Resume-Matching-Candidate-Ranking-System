"""
core/exceptions.py — Custom exception classes for the application.

Centralised exception definitions so error handling is consistent
across all services.  Each exception carries a user-friendly message
that the API layer can return directly.
"""


class ResumeMatcherError(Exception):
    """Base class for all application-specific exceptions."""

    def __init__(self, message: str = "An unexpected error occurred."):
        self.message = message
        super().__init__(self.message)


# ── File processing errors ──

class UnsupportedFileTypeError(ResumeMatcherError):
    """Raised when the uploaded file has an unsupported extension."""

    def __init__(self, filename: str, supported: list[str] | None = None):
        exts = supported or [".pdf", ".docx", ".txt"]
        msg = (
            f"Unsupported file type for '{filename}'. "
            f"Supported formats: {', '.join(exts)}"
        )
        super().__init__(msg)


class EmptyFileError(ResumeMatcherError):
    """Raised when the uploaded file is empty (0 bytes)."""

    def __init__(self, filename: str):
        super().__init__(f"The file '{filename}' is empty (0 bytes).")


class ScannedPDFError(ResumeMatcherError):
    """Raised when a PDF contains only images / scanned pages (no extractable text)."""

    def __init__(self, filename: str):
        super().__init__(
            f"The PDF '{filename}' appears to be scanned or image-only. "
            "No extractable text was found. Please upload a text-based PDF."
        )


class CorruptFileError(ResumeMatcherError):
    """Raised when a file cannot be parsed (corrupt or invalid format)."""

    def __init__(self, filename: str, detail: str = ""):
        msg = f"The file '{filename}' could not be parsed — it may be corrupt."
        if detail:
            msg += f" Detail: {detail}"
        super().__init__(msg)


class ExtractionError(ResumeMatcherError):
    """Raised when text extraction succeeds but produces no usable content."""

    def __init__(self, message: str = "No usable text could be extracted."):
        super().__init__(message)
