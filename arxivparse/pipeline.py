"""Orchestrate the full arXiv-to-text pipeline."""

import logging
import shutil
import tempfile
from pathlib import Path

from .convert import tex_to_xml
from .download import download_arxiv_source
from .errors import Arxiv2TextError
from .extract_text import xml_to_text
from .tex import find_main_tex

logger = logging.getLogger(__name__)


def convert_arxiv_to_text(
    arxiv_id: str,
    output_path: Path | None = None,
    work_dir: Path | None = None,
    keep_temp: bool = False,
) -> Path:
    """Convert a single arXiv paper to plain text.

    Args:
        arxiv_id: arXiv identifier (e.g. "2301.07041").
        output_path: Where to write the .txt file. Defaults to <arxiv_id>.txt.
        work_dir: Temp working directory. Defaults to system temp.
        keep_temp: If True, don't delete temp dir after completion.

    Returns:
        Path to the generated .txt file.

    Raises:
        Arxiv2TextError: On any pipeline failure.
    """
    if work_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="arxivparse_"))
    else:
        work_dir.mkdir(parents=True, exist_ok=True)

    source_dir = work_dir / "source"
    build_dir = work_dir / "build"

    try:
        logger.info("Downloading source for %s", arxiv_id)
        download_arxiv_source(arxiv_id, source_dir)

        logger.info("Finding main .tex file for %s", arxiv_id)
        main_tex = find_main_tex(source_dir, arxiv_id)
        logger.info("Using %s", main_tex)

        logger.info("Converting %s to XML", main_tex.name)
        xml_path = tex_to_xml(main_tex, build_dir)

        logger.info("Extracting text from XML")
        text = xml_to_text(str(xml_path))

        if output_path is None:
            output_path = Path(f"{arxiv_id.replace('/', '_')}.txt")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        logger.info("Wrote %s (%d chars)", output_path, len(text))

        return output_path
    finally:
        if not keep_temp and work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)
