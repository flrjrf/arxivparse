"""Tests for arxivparse.download — arXiv source download."""

import gzip
import tarfile
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from arxivparse.download import ARXIV_EPRINT_URL, USER_AGENT, download_arxiv_source, is_tarball
from arxivparse.errors import DownloadError, NoLatexSourceError


# ---------------------------------------------------------------------------
# is_tarball()
# ---------------------------------------------------------------------------

class TestIsTarball:
    def test_gzip_magic_bytes(self):
        assert is_tarball(b"\x1f\x8b\x08\x00") is True

    def test_empty_data(self):
        assert is_tarball(b"") is False

    def test_single_byte(self):
        assert is_tarball(b"\x1f") is False

    def test_pdf_data(self):
        assert is_tarball(b"%PDF-1.4") is False

    def test_plain_text(self):
        assert is_tarball(b"\\documentclass{article}") is False

    def test_exactly_two_bytes_gzip(self):
        assert is_tarball(b"\x1f\x8b") is True


# ---------------------------------------------------------------------------
# Helper to build mock responses
# ---------------------------------------------------------------------------

def _mock_response(content_type="application/x-gzip", content=b""):
    resp = MagicMock()
    resp.headers = {"Content-Type": content_type}
    resp.content = content
    resp.raise_for_status = MagicMock()
    return resp


def _make_tarball(files: dict[str, str]) -> bytes:
    """Create a gzipped tarball containing the given files {name: content}."""
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, BytesIO(data))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# download_arxiv_source()
# ---------------------------------------------------------------------------

class TestDownloadArxivSource:
    @patch("arxivparse.download.requests.get")
    def test_success_tarball(self, mock_get, tmp_path):
        content = _make_tarball({"main.tex": "\\documentclass{article}"})
        mock_get.return_value = _mock_response(content=content)

        result = download_arxiv_source("2301.07041", tmp_path)
        assert result == tmp_path
        assert (tmp_path / "main.tex").exists()

    @patch("arxivparse.download.requests.get")
    def test_success_single_tex_gz(self, mock_get, tmp_path):
        tex = "\\documentclass{article}"
        gz_data = gzip.compress(tex.encode("utf-8"))
        # Not a valid tarball but starts with gzip magic bytes
        mock_get.return_value = _mock_response(content=gz_data)

        result = download_arxiv_source("2301.07041", tmp_path)
        assert result == tmp_path
        assert (tmp_path / "main.tex").read_text() == tex

    @patch("arxivparse.download.requests.get")
    def test_success_raw_tex_with_documentclass(self, mock_get, tmp_path):
        tex = "\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}"
        mock_get.return_value = _mock_response(content_type="application/octet-stream", content=tex.encode())

        result = download_arxiv_source("2301.07041", tmp_path)
        assert result == tmp_path
        assert (tmp_path / "main.tex").read_text() == tex

    @patch("arxivparse.download.requests.get")
    def test_success_raw_tex_with_input(self, mock_get, tmp_path):
        tex = "\\input{preamble}\nSome content"
        mock_get.return_value = _mock_response(content_type="application/octet-stream", content=tex.encode())

        result = download_arxiv_source("2301.07041", tmp_path)
        assert result == tmp_path
        assert (tmp_path / "main.tex").read_text() == tex

    @patch("arxivparse.download.requests.get")
    def test_pdf_only_raises_no_latex_source_error(self, mock_get, tmp_path):
        mock_get.return_value = _mock_response(content_type="text/html")

        with pytest.raises(NoLatexSourceError, match="2301.07041"):
            download_arxiv_source("2301.07041", tmp_path)

    @patch("arxivparse.download.requests.get")
    def test_network_error_raises_download_error(self, mock_get, tmp_path):
        import requests
        mock_get.side_effect = requests.ConnectionError("refused")

        with pytest.raises(DownloadError, match="Failed to download"):
            download_arxiv_source("2301.07041", tmp_path)

    @patch("arxivparse.download.requests.get")
    def test_http_error_raises_download_error(self, mock_get, tmp_path):
        import requests
        resp = MagicMock()
        resp.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = resp

        with pytest.raises(DownloadError, match="Failed to download"):
            download_arxiv_source("2301.07041", tmp_path)

    @patch("arxivparse.download.requests.get")
    def test_unrecognized_format_raises_download_error(self, mock_get, tmp_path):
        mock_get.return_value = _mock_response(content_type="application/binary", content=b"\x00\x01\x02\x03")

        with pytest.raises(DownloadError, match="unexpected content type"):
            download_arxiv_source("2301.07041", tmp_path)

    @patch("arxivparse.download.requests.get")
    def test_corrupt_tarball_falls_through_to_gzip(self, mock_get, tmp_path):
        """Data with gzip magic but not a valid tar falls through to single-file gzip."""
        tex = "\\documentclass{article}"
        gz_data = gzip.compress(tex.encode("utf-8"))
        mock_get.return_value = _mock_response(content=gz_data)

        result = download_arxiv_source("2301.07041", tmp_path)
        assert (tmp_path / "main.tex").read_text() == tex

    @patch("arxivparse.download.requests.get")
    def test_url_format(self, mock_get, tmp_path):
        mock_get.return_value = _mock_response(content=b"\\documentclass{article}")

        download_arxiv_source("2301.07041", tmp_path)
        mock_get.assert_called_once()
        url = mock_get.call_args[0][0]
        assert url == "https://arxiv.org/e-print/2301.07041"

    @patch("arxivparse.download.requests.get")
    def test_user_agent_header(self, mock_get, tmp_path):
        mock_get.return_value = _mock_response(content=b"\\documentclass{article}")

        download_arxiv_source("2301.07041", tmp_path)
        headers = mock_get.call_args[1]["headers"]
        assert headers["User-Agent"] == USER_AGENT

    @patch("arxivparse.download.requests.get")
    def test_custom_timeout(self, mock_get, tmp_path):
        mock_get.return_value = _mock_response(content=b"\\documentclass{article}")

        download_arxiv_source("2301.07041", tmp_path, timeout=30)
        assert mock_get.call_args[1]["timeout"] == 30
