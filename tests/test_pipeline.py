"""Tests for arxivparser.pipeline — full pipeline orchestration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arxivparser.errors import (
    ConversionError,
    DownloadError,
    MainTexNotFoundError,
    NoLatexSourceError,
)
from arxivparser.pipeline import convert_arxiv_to_text


@patch("arxivparser.pipeline.xml_to_text", return_value="Hello world")
@patch("arxivparser.pipeline.tex_to_xml")
@patch("arxivparser.pipeline.find_main_tex")
@patch("arxivparser.pipeline.download_arxiv_source")
class TestPipeline:
    def test_success_end_to_end(self, mock_dl, mock_find, mock_conv, mock_extract, tmp_path):
        tex_path = tmp_path / "source" / "main.tex"
        tex_path.parent.mkdir(parents=True)
        tex_path.write_text("\\documentclass{article}")
        mock_find.return_value = tex_path
        mock_conv.return_value = tmp_path / "build" / "output.xml"

        output = tmp_path / "output.txt"
        result = convert_arxiv_to_text("2301.07041", output_path=output)
        assert result == output
        assert output.read_text() == "Hello world"

    def test_download_error_propagates(self, mock_dl, mock_find, mock_conv, mock_extract):
        mock_dl.side_effect = DownloadError("fail")
        with pytest.raises(DownloadError, match="fail"):
            convert_arxiv_to_text("2301.07041")

    def test_no_latex_source_error_propagates(self, mock_dl, mock_find, mock_conv, mock_extract):
        mock_dl.side_effect = NoLatexSourceError("pdf only")
        with pytest.raises(NoLatexSourceError, match="pdf only"):
            convert_arxiv_to_text("2301.07041")

    def test_main_tex_not_found_error_propagates(self, mock_dl, mock_find, mock_conv, mock_extract):
        mock_find.side_effect = MainTexNotFoundError("no tex")
        with pytest.raises(MainTexNotFoundError, match="no tex"):
            convert_arxiv_to_text("2301.07041")

    def test_conversion_error_propagates(self, mock_dl, mock_find, mock_conv, mock_extract):
        mock_conv.side_effect = ConversionError("latexml failed")
        with pytest.raises(ConversionError, match="latexml failed"):
            convert_arxiv_to_text("2301.07041")

    def test_temp_dir_cleanup_on_success(self, mock_dl, mock_find, mock_conv, mock_extract, tmp_path):
        work_dir = tmp_path / "work"
        mock_find.return_value = tmp_path / "main.tex"
        mock_conv.return_value = tmp_path / "output.xml"

        convert_arxiv_to_text("2301.07041", work_dir=work_dir)
        assert not work_dir.exists()

    def test_temp_dir_cleanup_on_error(self, mock_dl, mock_find, mock_conv, mock_extract, tmp_path):
        work_dir = tmp_path / "work"
        mock_dl.side_effect = DownloadError("fail")

        with pytest.raises(DownloadError):
            convert_arxiv_to_text("2301.07041", work_dir=work_dir)
        assert not work_dir.exists()

    def test_keep_temp(self, mock_dl, mock_find, mock_conv, mock_extract, tmp_path):
        work_dir = tmp_path / "work"
        mock_find.return_value = tmp_path / "main.tex"
        mock_conv.return_value = tmp_path / "output.xml"

        convert_arxiv_to_text("2301.07041", work_dir=work_dir, keep_temp=True)
        assert work_dir.exists()

    def test_default_output_path(self, mock_dl, mock_find, mock_conv, mock_extract, tmp_path):
        mock_find.return_value = tmp_path / "main.tex"
        mock_conv.return_value = tmp_path / "output.xml"

        result = convert_arxiv_to_text("2301.07041")
        assert result == Path("2301.07041.txt")
        # Clean up
        result.unlink(missing_ok=True)

    def test_arxiv_id_with_slash_output_path(self, mock_dl, mock_find, mock_conv, mock_extract, tmp_path):
        mock_find.return_value = tmp_path / "main.tex"
        mock_conv.return_value = tmp_path / "output.xml"

        result = convert_arxiv_to_text("hep-th/9901001")
        assert result == Path("hep-th_9901001.txt")
        result.unlink(missing_ok=True)

    def test_creates_output_parent_dirs(self, mock_dl, mock_find, mock_conv, mock_extract, tmp_path):
        mock_find.return_value = tmp_path / "main.tex"
        mock_conv.return_value = tmp_path / "output.xml"
        output = tmp_path / "deep" / "nested" / "output.txt"

        result = convert_arxiv_to_text("2301.07041", output_path=output)
        assert result == output
        assert output.exists()
