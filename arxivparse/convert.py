"""Run the LaTeXML conversion (tex → XML)."""

import logging
import shutil
import subprocess
from pathlib import Path

from .errors import ConversionError

logger = logging.getLogger(__name__)


def _find_latexml() -> str:
    """Locate the latexml binary on PATH."""
    path = shutil.which("latexml")
    if path is None:
        raise ConversionError(
            "latexml not found on PATH. Install it via: brew install latexml"
        )
    return path


def tex_to_xml(
    tex_path: Path,
    work_dir: Path,
    timeout: int = 120,
) -> Path:
    """Convert a .tex file to XML using latexml.

    Returns the path to the generated XML file.

    Raises:
        ConversionError: If latexml fails.
    """
    latexml_path = _find_latexml()

    work_dir.mkdir(parents=True, exist_ok=True)
    xml_path = work_dir / "output.xml"
    source_dir = tex_path.parent

    cmd = [
        latexml_path,
        str(tex_path),
        f"--path={source_dir}",
        f"--destination={xml_path}",
        "--log=/dev/null",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.stderr:
            for line in result.stderr.strip().splitlines():
                logger.debug("latexml: %s", line)

        if result.returncode != 0:
            stderr = result.stderr.strip()
            msg = f"latexml failed (exit code {result.returncode})"
            if stderr:
                msg += f": {stderr}"
            raise ConversionError(msg)
    except FileNotFoundError:
        raise ConversionError(f"latexml not found at {latexml_path}")
    except subprocess.TimeoutExpired:
        raise ConversionError(f"latexml timed out after {timeout}s")

    return xml_path
