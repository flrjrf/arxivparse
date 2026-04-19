# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

arxivparse is a Python package that converts arXiv papers to clean plain text using LaTeXML. It follows a sequential pipeline: download → find main .tex → convert to XML → extract text.

## Commands

```bash
uv sync                    # Install dependencies
pytest                     # Run all tests
pytest tests/test_<module>.py  # Run a single test file
pytest tests/test_pipeline.py::test_<name>  # Run a single test
```

## External Dependency

LaTeXML v0.8.x must be installed (`brew install latexml`). It's invoked as a subprocess in `convert.py` — not a Python dependency.

## Architecture

The pipeline is orchestrated in `arxivparse/pipeline.py` which chains four stages:

1. **`download.py`** — Fetches LaTeX source from arXiv (handles tarball, gzip, raw .tex, detects PDF-only papers)
2. **`tex.py`** — Finds the main .tex file (Makefile parsing → `\documentclass` detection → alphabetical fallback)
3. **`convert.py`** — Runs `latexml` subprocess with timeout to produce XML
4. **`extract_text.py`** — Parses XML into QASPER-style plain text, preserving math notation and filtering noise

The public API is exposed through `arxivparse/__init__.py` via `arxiv_to_text()`. The CLI (`cli.py`) and `main.py` (backwards-compatible entry point) both call into this API.

## Error Hierarchy

Custom exceptions in `errors.py`: `Arxiv2TextError` → `DownloadError`, `NoLatexSourceError`, `ConversionError`, `MainTexNotFoundError`.

## Build & Publish

Uses `uv` with `uv_build` backend. Python >= 3.10. Publish with `uv build && uv publish`.
