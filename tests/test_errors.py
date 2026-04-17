"""Tests for arxivparse.errors exception hierarchy."""

import pytest

from arxivparse.errors import (
    Arxiv2TextError,
    ConversionError,
    DownloadError,
    MainTexNotFoundError,
    NoLatexSourceError,
)


class TestErrorHierarchy:
    def test_arxiv2text_error_is_exception(self):
        assert issubclass(Arxiv2TextError, Exception)

    def test_download_error_is_arxiv2text_error(self):
        assert issubclass(DownloadError, Arxiv2TextError)

    def test_no_latex_source_error_is_arxiv2text_error(self):
        assert issubclass(NoLatexSourceError, Arxiv2TextError)

    def test_conversion_error_is_arxiv2text_error(self):
        assert issubclass(ConversionError, Arxiv2TextError)

    def test_main_tex_not_found_error_is_arxiv2text_error(self):
        assert issubclass(MainTexNotFoundError, Arxiv2TextError)

    def test_catch_base_catches_all(self):
        for exc_cls in [DownloadError, NoLatexSourceError, ConversionError, MainTexNotFoundError]:
            with pytest.raises(Arxiv2TextError):
                raise exc_cls("test")


class TestErrorMessages:
    def test_message_preserved(self):
        for exc_cls in [Arxiv2TextError, DownloadError, NoLatexSourceError, ConversionError, MainTexNotFoundError]:
            err = exc_cls("custom message")
            assert str(err) == "custom message"

    def test_error_chaining(self):
        original = ValueError("original")
        try:
            raise DownloadError("wrapped") from original
        except DownloadError as err:
            assert err.__cause__ is original
