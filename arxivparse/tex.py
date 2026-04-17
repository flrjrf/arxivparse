"""Find the main .tex file in an extracted arXiv source bundle."""

import re
from pathlib import Path

from .errors import MainTexNotFoundError

# Common main file names in arXiv papers, in priority order
KNOWN_MAIN_NAMES = ["main.tex", "paper.tex", "article.tex", "ms.tex"]

# Regex to find the .tex target in a Makefile
MAKEFILE_TEX_PATTERN = re.compile(
    r"(?:pdflatex|latex|xelatex|lualatex)\s+(\S+\.tex)", re.MULTILINE
)


def find_main_tex(source_dir: Path, arxiv_id: str | None = None) -> Path:
    """Find the main .tex file in the extracted arXiv source directory.

    Strategy (in priority order):
    1. Known file names (main.tex, paper.tex, etc.)
    2. Makefile target
    3. File containing \\documentclass
    4. First .tex file alphabetically

    Raises:
        MainTexNotFoundError: No .tex files found.
    """
    tex_files = list(source_dir.rglob("*.tex"))
    if not tex_files:
        raise MainTexNotFoundError(f"No .tex files found in {source_dir}")

    # 1. Check known names
    for name in KNOWN_MAIN_NAMES:
        candidate = source_dir / name
        if candidate.exists():
            return candidate

    # Also check for <arxiv_id>.tex
    if arxiv_id:
        candidate = source_dir / f"{arxiv_id.replace('/', '_')}.tex"
        if candidate.exists():
            return candidate

    # 2. Check Makefile
    makefile = source_dir / "Makefile"
    if makefile.exists():
        tex_target = _parse_makefile(makefile)
        if tex_target:
            candidate = source_dir / tex_target
            if candidate.exists():
                return candidate

    # 3. Find files with \documentclass
    files_with_docclass = [f for f in tex_files if _has_documentclass(f)]
    if len(files_with_docclass) == 1:
        return files_with_docclass[0]

    # 4. Fallback: first .tex alphabetically
    return sorted(tex_files)[0]


def _parse_makefile(makefile: Path) -> str | None:
    """Parse Makefile for the main .tex target."""
    try:
        content = makefile.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = MAKEFILE_TEX_PATTERN.search(content)
    return match.group(1) if match else None


def _has_documentclass(tex_path: Path, max_lines: int = 50) -> bool:
    """Check if a .tex file contains \\documentclass in the first max_lines lines."""
    try:
        with open(tex_path, encoding="utf-8", errors="replace") as f:
            for _ in range(max_lines):
                line = f.readline()
                if "\\documentclass" in line:
                    return True
    except OSError:
        pass
    return False
