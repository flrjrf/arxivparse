# arxivparse

Convert arXiv papers to clean plain text using LaTeXML. Downloads LaTeX source from arXiv, converts to XML, and extracts body text (title, abstract, sections, math, captions) — no HTML intermediary, no bibliography, no footnotes.

## Prerequisites

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) (or pip)
- [LaTeXML](https://dlmf.nist.gov/LaTeXML/) (v0.8.x) — install via Homebrew:

```bash
brew install latexml
```

Verify it's on your PATH:

```bash
latexml --VERSION
```

## Install

```bash
# From PyPI
pip install arxivparse

# Or from source
git clone <repo-url> arxivparse
cd arxivparse
uv sync
```

## Quick Start

```python
from arxivparse import arxiv_to_text

text = arxiv_to_text("1706.03762")
print(text[:200])
```

## CLI Usage

```bash
# Single paper
arxivparse 1706.03762

# Multiple papers (sequential)
arxivparse 1706.03762 2301.07041

# Custom output path
arxivparse -o output.txt 1706.03762

# Custom output directory
arxivparse -d ./papers 1706.03762 2301.07041

# Verbose output (download, convert, extract steps)
arxivparse -v 1706.03762

# Keep temp files for debugging
arxivparse --keep-temp 1706.03762
```

Each paper produces a `<arxiv_id>.txt` file.

## Library Usage

### Simple: get text as a string

```python
from arxivparse import arxiv_to_text

text = arxiv_to_text("1706.03762")
```

### Full pipeline control

```python
from arxivparse.pipeline import convert_arxiv_to_text
from arxivparse.errors import Arxiv2TextError

try:
    output_path = convert_arxiv_to_text("1706.03762")
    text = output_path.read_text(encoding="utf-8")
except Arxiv2TextError as e:
    print(f"Failed: {e}")
```

### Call the CLI from code

```python
from main import main

main(["1706.03762", "2301.07041"])
main(["-o", "output.txt", "1706.03762"])
```

## Arguments

| Param | Type | Default | Description |
|---|---|---|---|
| `arxiv_id` | `str` | — | arXiv ID (e.g. `"1706.03762"`) |
| `output_path` | `Path` | `<arxiv_id>.txt` | Where to write the output |
| `keep_temp` | `bool` | `False` | Keep temp files after conversion |

## Error Handling

```python
from arxivparse.errors import (
    DownloadError,         # network/HTTP failure
    NoLatexSourceError,    # paper is PDF-only
    ConversionError,       # latexml failed
    MainTexNotFoundError,  # no .tex file found in bundle
)
```

## Build / Publish

```bash
# Build a wheel
uv build

# Publish to PyPI
uv publish

# Or with twine
twine upload dist/*
```

## Output Format

QASPER-style plain text: title, abstract, section headings, body paragraphs, inline math (LaTeX notation like `h_{t}`), and figure/table captions. No bibliography entries, footnotes, author affiliations, or citation numbers.
