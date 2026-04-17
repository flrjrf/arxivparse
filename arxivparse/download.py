"""Download and extract arXiv LaTeX source."""

import gzip
import sys
import tarfile
from io import BytesIO
from pathlib import Path

import requests

from .errors import DownloadError, NoLatexSourceError

ARXIV_EPRINT_URL = "https://arxiv.org/e-print/{arxiv_id}"
USER_AGENT = "arxivparse/0.1 (mailto:arxivparse@example.com)"


def download_arxiv_source(
    arxiv_id: str,
    dest_dir: Path,
    timeout: int = 60,
) -> Path:
    """Download LaTeX source from arXiv and extract into dest_dir.

    Returns the path to the directory containing extracted files.

    Raises:
        DownloadError: Network or HTTP errors.
        NoLatexSourceError: Paper is PDF-only.
    """
    url = ARXIV_EPRINT_URL.format(arxiv_id=arxiv_id)
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise DownloadError(f"Failed to download {arxiv_id}: {e}") from e

    content_type = resp.headers.get("Content-Type", "")

    # PDF-only papers return HTML
    if "text/html" in content_type:
        raise NoLatexSourceError(
            f"No LaTeX source available for {arxiv_id} (paper may be PDF-only)"
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    data = resp.content

    # Try tarball extraction first (most arXiv papers)
    if is_tarball(data):
        try:
            with tarfile.open(fileobj=BytesIO(data), mode="r:gz") as tar:
                # filter="data" requires Python 3.12+ (PEP 706)
                if sys.version_info >= (3, 12):
                    tar.extractall(dest_dir, filter="data")
                else:
                    tar.extractall(dest_dir)
            return dest_dir
        except (tarfile.TarError, EOFError):
            pass  # Fall through to gzip single-file handling

    # Try single .tex.gz
    try:
        text = gzip.decompress(data).decode("utf-8", errors="replace")
        (dest_dir / "main.tex").write_text(text, encoding="utf-8")
        return dest_dir
    except gzip.BadGzipFile:
        pass

    # Raw .tex content (no compression)
    try:
        text = data.decode("utf-8", errors="replace")
        if "\\documentclass" in text or "\\input" in text:
            (dest_dir / "main.tex").write_text(text, encoding="utf-8")
            return dest_dir
    except UnicodeDecodeError:
        pass

    raise DownloadError(
        f"Could not extract source for {arxiv_id}: "
        f"unexpected content type '{content_type}'"
    )


def is_tarball(data: bytes) -> bool:
    """Check if data looks like a gzip tarball (starts with gzip magic bytes)."""
    return data[:2] == b"\x1f\x8b"
