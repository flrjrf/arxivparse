"""arxivparse - Convert arXiv papers to plain text using LaTeXML."""

__version__ = "0.2.0"

from .errors import Arxiv2TextError
from .pipeline import convert_arxiv_to_text

__all__ = ["Arxiv2TextError", "convert_arxiv_to_text", "arxiv_to_text"]


def arxiv_to_text(
    arxiv_id: str,
    download_timeout: int = 60,
    convert_timeout: int = 120,
) -> str:
    """Convert an arXiv paper to plain text and return as a string.

    Args:
        arxiv_id: arXiv identifier (e.g. "1706.03762").
        download_timeout: Timeout in seconds for downloading the arXiv source.
        convert_timeout: Timeout in seconds for the LaTeXML conversion.

    Returns:
        Full paper text as a string.

    Raises:
        Arxiv2TextError: On any pipeline failure.
    """
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        convert_arxiv_to_text(
            arxiv_id,
            output_path=tmp_path,
            download_timeout=download_timeout,
            convert_timeout=convert_timeout,
        )
        return tmp_path.read_text(encoding="utf-8")
    finally:
        tmp_path.unlink(missing_ok=True)
