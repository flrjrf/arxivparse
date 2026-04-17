"""Tests for arxivparse.convert — LaTeXML conversion."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arxivparse.convert import _find_latexml, tex_to_xml
from arxivparse.errors import ConversionError


class TestFindLatexml:
    @patch("arxivparse.convert.shutil.which")
    def test_on_path(self, mock_which):
        mock_which.return_value = "/usr/local/bin/latexml"
        assert _find_latexml() == "/usr/local/bin/latexml"

    @patch("arxivparse.convert.shutil.which")
    def test_not_found_raises(self, mock_which):
        mock_which.return_value = None
        with pytest.raises(ConversionError, match="latexml not found"):
            _find_latexml()


class TestTexToXml:
    @patch("arxivparse.convert.subprocess.run")
    @patch("arxivparse.convert._find_latexml")
    def test_success(self, mock_find, mock_run, tmp_path):
        mock_find.return_value = "/usr/bin/latexml"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        tex_path = tmp_path / "main.tex"
        tex_path.write_text("\\documentclass{article}")
        work_dir = tmp_path / "build"

        result = tex_to_xml(tex_path, work_dir)
        assert result == work_dir / "output.xml"

    @patch("arxivparse.convert.subprocess.run")
    @patch("arxivparse.convert._find_latexml")
    def test_creates_work_dir(self, mock_find, mock_run, tmp_path):
        mock_find.return_value = "/usr/bin/latexml"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        tex_path = tmp_path / "main.tex"
        tex_path.write_text("\\documentclass{article}")
        work_dir = tmp_path / "nonexistent" / "build"

        tex_to_xml(tex_path, work_dir)
        assert work_dir.exists()

    @patch("arxivparse.convert.subprocess.run")
    @patch("arxivparse.convert._find_latexml")
    def test_command_arguments(self, mock_find, mock_run, tmp_path):
        mock_find.return_value = "/usr/bin/latexml"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        tex_path = tmp_path / "main.tex"
        tex_path.write_text("\\documentclass{article}")
        work_dir = tmp_path / "build"

        tex_to_xml(tex_path, work_dir)
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "/usr/bin/latexml"
        assert str(tex_path) in cmd
        assert f"--path={tex_path.parent}" in cmd
        assert f"--destination={work_dir / 'output.xml'}" in cmd
        assert "--quiet" in cmd

    @patch("arxivparse.convert.subprocess.run")
    @patch("arxivparse.convert._find_latexml")
    def test_nonzero_exit_raises(self, mock_find, mock_run, tmp_path):
        mock_find.return_value = "/usr/bin/latexml"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="syntax error"
        )
        tex_path = tmp_path / "main.tex"
        tex_path.write_text("\\documentclass{article}")

        with pytest.raises(ConversionError, match="exit code 1"):
            tex_to_xml(tex_path, tmp_path / "build")

    @patch("arxivparse.convert.subprocess.run")
    @patch("arxivparse.convert._find_latexml")
    def test_nonzero_exit_no_stderr(self, mock_find, mock_run, tmp_path):
        mock_find.return_value = "/usr/bin/latexml"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr=""
        )
        tex_path = tmp_path / "main.tex"
        tex_path.write_text("\\documentclass{article}")

        with pytest.raises(ConversionError) as exc_info:
            tex_to_xml(tex_path, tmp_path / "build")
        assert ": " not in str(exc_info.value) or "exit code 2" in str(exc_info.value)

    @patch("arxivparse.convert.subprocess.run")
    @patch("arxivparse.convert._find_latexml")
    def test_timeout_raises(self, mock_find, mock_run, tmp_path):
        mock_find.return_value = "/usr/bin/latexml"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="latexml", timeout=120)
        tex_path = tmp_path / "main.tex"
        tex_path.write_text("\\documentclass{article}")

        with pytest.raises(ConversionError, match="timed out"):
            tex_to_xml(tex_path, tmp_path / "build")

    @patch("arxivparse.convert.subprocess.run")
    @patch("arxivparse.convert._find_latexml")
    def test_file_not_found_raises(self, mock_find, mock_run, tmp_path):
        mock_find.return_value = "/usr/bin/latexml"
        mock_run.side_effect = FileNotFoundError("not found")
        tex_path = tmp_path / "main.tex"
        tex_path.write_text("\\documentclass{article}")

        with pytest.raises(ConversionError):
            tex_to_xml(tex_path, tmp_path / "build")
