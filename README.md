# arxivparse

Convert arXiv papers to clean plain text using LaTeXML. Download any arXiv paper and get structured text with title, abstract, sections, and math notation preserved.

## Install

```bash
pip install arxivparse
```

Quick verification that LaTeXML is installed:

```bash
latexml --version
```

## Usage

### Get text as a string

```python
from arxivparse import arxiv_to_text

text = arxiv_to_text("1706.03762")  # Attention is All You Need paper
print(text[:200])
```

### Save text to a file

```python
from arxivparse.pipeline import convert_arxiv_to_text
from pathlib import Path

output_path = convert_arxiv_to_text("1706.03762", output_path="paper.txt")
text = Path("paper.txt").read_text()
```

### Handle errors gracefully

```python
from arxivparse.errors import (
    Arxiv2TextError,
    DownloadError,
    NoLatexSourceError,
    ConversionError,
)

try:
    text = arxiv_to_text("1706.03762")
except NoLatexSourceError:
    print("Paper is PDF-only")
except DownloadError:
    print("Download failed")
except ConversionError:
    print("LaTeXML conversion failed")
```

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


## Configuration

Both functions accept optional timeouts:

```python
# arxiv_to_text() - returns string
text = arxiv_to_text(
    arxiv_id="1706.03762",
    download_timeout=60,    # seconds to wait for download
    convert_timeout=120,   # seconds to wait for LaTeXML
)

# convert_arxiv_to_text() - returns file path
path = convert_arxiv_to_text(
    arxiv_id="1706.03762",
    output_path="paper.txt",  # custom output file
    download_timeout=60,
    convert_timeout=120,
    keep_temp=False,         # keep intermediate files
)
```

## Error Handling

```python
from arxivparse.errors import (
    DownloadError,         # network/HTTP failure
    NoLatexSourceError,    # paper is PDF-only
    ConversionError,       # LaTeXML failed
    MainTexNotFoundError,  # no .tex file found
    Arxiv2TextError,       # any pipeline failure
)
```

## CLI Reference (Optional)

If you prefer the command line:

```bash
# Install the CLI (comes with the package)
arxivparse 1706.03762

# Multiple papers
arxivparse 1706.03762 2301.07041

# Custom output
arxivparse -o paper.txt 1706.03762

# Verbose output
arxivparse -v 1706.03762

# Keep temp files for debugging
arxivparse --keep-temp 1706.03762
```

## Output Format

QASPER-style plain text: title, abstract, section headings, body paragraphs, inline math (LaTeX notation like `h_{t}`), and figure/table captions. No bibliography entries, footnotes, author affiliations, or citation numbers.
