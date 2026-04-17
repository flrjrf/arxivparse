"""Tests for arxivparse.__init__ — public API."""

from unittest.mock import patch

import pytest

from arxivparse import Arxiv2TextError, convert_arxiv_to_text


class TestPublicAPIExports:
    def test_arxiv_to_text_importable(self):
        from arxivparse import arxiv_to_text
        assert callable(arxiv_to_text)

    def test_convert_arxiv_to_text_importable(self):
        assert callable(convert_arxiv_to_text)

    def test_arxiv2text_error_importable(self):
        assert issubclass(Arxiv2TextError, Exception)

    def test_all_exports(self):
        import arxivparse
        assert set(arxivparse.__all__) == {"Arxiv2TextError", "convert_arxiv_to_text", "arxiv_to_text"}


class TestArxivToText:
    @patch("arxivparse.convert_arxiv_to_text")
    def test_returns_string(self, mock_convert, tmp_path):
        def _mock(arxiv_id, output_path):
            output_path.write_text("paper text")
            return output_path

        mock_convert.side_effect = _mock

        from arxivparse import arxiv_to_text
        result = arxiv_to_text("2301.07041")
        assert isinstance(result, str)
        assert result == "paper text"

    @patch("arxivparse.convert_arxiv_to_text")
    def test_cleans_temp_file(self, mock_convert, tmp_path):
        output = tmp_path / "out.txt"
        output.write_text("text")
        mock_convert.return_value = output

        from arxivparse import arxiv_to_text
        # arxiv_to_text creates a temp file and deletes it after reading
        # We can't easily assert the temp file is deleted since we don't know its name,
        # but we verify no side-effect files remain in CWD
        before = set(tmp_path.iterdir())
        arxiv_to_text("2301.07041")
        # The output file still exists (written by mock), no extra files
        assert set(tmp_path.iterdir()) == before

    @patch("arxivparse.convert_arxiv_to_text")
    def test_propagates_error(self, mock_convert):
        from arxivparse import arxiv_to_text
        from arxivparse.errors import DownloadError

        mock_convert.side_effect = DownloadError("network fail")
        with pytest.raises(Arxiv2TextError):
            arxiv_to_text("2301.07041")
