"""Custom exceptions for arxivparser."""


class Arxiv2TextError(Exception):
    """Base exception for arxivparser."""


class DownloadError(Arxiv2TextError):
    """Failed to download arXiv source."""


class NoLatexSourceError(Arxiv2TextError):
    """Paper is PDF-only (no LaTeX source available)."""


class ConversionError(Arxiv2TextError):
    """latexml or latexmlpost failed."""


class MainTexNotFoundError(Arxiv2TextError):
    """Could not identify the main .tex file in the bundle."""
