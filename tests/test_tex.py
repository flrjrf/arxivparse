"""Tests for arxivparser.tex — main .tex file discovery."""

import pytest

from arxivparser.errors import MainTexNotFoundError
from arxivparser.tex import KNOWN_MAIN_NAMES, _has_documentclass, _parse_makefile, find_main_tex


# ---------------------------------------------------------------------------
# _parse_makefile()
# ---------------------------------------------------------------------------

class TestParseMakefile:
    def test_pdflatex_target(self, tmp_path):
        mf = tmp_path / "Makefile"
        mf.write_text("all:\n\tpdflatex main.tex\n")
        assert _parse_makefile(mf) == "main.tex"

    def test_xelatex_target(self, tmp_path):
        mf = tmp_path / "Makefile"
        mf.write_text("all:\n\txelatex paper.tex\n")
        assert _parse_makefile(mf) == "paper.tex"

    def test_lualatex_target(self, tmp_path):
        mf = tmp_path / "Makefile"
        mf.write_text("all:\n\tlualatex paper.tex\n")
        assert _parse_makefile(mf) == "paper.tex"

    def test_latex_target(self, tmp_path):
        mf = tmp_path / "Makefile"
        mf.write_text("all:\n\tlatex paper.tex\n")
        assert _parse_makefile(mf) == "paper.tex"

    def test_no_tex_target(self, tmp_path):
        mf = tmp_path / "Makefile"
        mf.write_text("all:\n\techo hello\n")
        assert _parse_makefile(mf) is None

    def test_empty_file(self, tmp_path):
        mf = tmp_path / "Makefile"
        mf.write_text("")
        assert _parse_makefile(mf) is None

    def test_unreadable(self):
        from pathlib import Path
        assert _parse_makefile(Path("/nonexistent/path/Makefile")) is None

    def test_multiple_targets_returns_first(self, tmp_path):
        mf = tmp_path / "Makefile"
        mf.write_text("all:\n\tpdflatex first.tex\n\tlatex second.tex\n")
        assert _parse_makefile(mf) == "first.tex"

    def test_target_with_path(self, tmp_path):
        mf = tmp_path / "Makefile"
        mf.write_text("all:\n\tpdflatex subdir/main.tex\n")
        assert _parse_makefile(mf) == "subdir/main.tex"


# ---------------------------------------------------------------------------
# _has_documentclass()
# ---------------------------------------------------------------------------

class TestHasDocumentclass:
    def test_on_first_line(self, tmp_path):
        f = tmp_path / "file.tex"
        f.write_text("\\documentclass{article}\n")
        assert _has_documentclass(f) is True

    def test_on_line_50(self, tmp_path):
        f = tmp_path / "file.tex"
        lines = ["\n"] * 49 + ["\\documentclass{article}\n"]
        f.write_text("".join(lines))
        assert _has_documentclass(f) is True

    def test_beyond_max_lines(self, tmp_path):
        f = tmp_path / "file.tex"
        lines = ["\n"] * 50 + ["\\documentclass{article}\n"]
        f.write_text("".join(lines))
        assert _has_documentclass(f) is False

    def test_custom_max_lines(self, tmp_path):
        f = tmp_path / "file.tex"
        f.write_text("\n\n\\documentclass{article}\n")
        assert _has_documentclass(f, max_lines=2) is False
        assert _has_documentclass(f, max_lines=5) is True

    def test_no_documentclass(self, tmp_path):
        f = tmp_path / "file.tex"
        f.write_text("\\input{preamble}\n")
        assert _has_documentclass(f) is False

    def test_commented_out_documentclass(self, tmp_path):
        """Documents that substring match does not distinguish comments."""
        f = tmp_path / "file.tex"
        f.write_text("% \\documentclass{article}\n")
        assert _has_documentclass(f) is True

    def test_unreadable_file(self):
        assert _has_documentclass("/nonexistent/path/file.tex") is False


# ---------------------------------------------------------------------------
# find_main_tex()
# ---------------------------------------------------------------------------

class TestFindMainTex:
    def test_known_name_main_tex(self, tmp_path):
        (tmp_path / "main.tex").write_text("\\documentclass{article}")
        (tmp_path / "other.tex").write_text("\\input{preamble}")
        assert find_main_tex(tmp_path) == tmp_path / "main.tex"

    def test_known_name_priority_main_over_paper(self, tmp_path):
        (tmp_path / "main.tex").write_text("a")
        (tmp_path / "paper.tex").write_text("b")
        assert find_main_tex(tmp_path) == tmp_path / "main.tex"

    def test_known_name_paper_tex(self, tmp_path):
        (tmp_path / "paper.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path) == tmp_path / "paper.tex"

    def test_known_name_article_tex(self, tmp_path):
        (tmp_path / "article.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path) == tmp_path / "article.tex"

    def test_known_name_ms_tex(self, tmp_path):
        (tmp_path / "ms.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path) == tmp_path / "ms.tex"

    def test_arxiv_id_match(self, tmp_path):
        (tmp_path / "2301.07041.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path, arxiv_id="2301.07041") == tmp_path / "2301.07041.tex"

    def test_arxiv_id_slash_replaced(self, tmp_path):
        (tmp_path / "hep-th_9901001.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path, arxiv_id="hep-th/9901001") == tmp_path / "hep-th_9901001.tex"

    def test_makefile_target(self, tmp_path):
        (tmp_path / "Makefile").write_text("all:\n\tpdflatex custom.tex\n")
        (tmp_path / "custom.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path) == tmp_path / "custom.tex"

    def test_makefile_target_nonexistent_falls_through(self, tmp_path):
        (tmp_path / "Makefile").write_text("all:\n\tpdflatex nonexistent.tex\n")
        (tmp_path / "real.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path) == tmp_path / "real.tex"

    def test_single_documentclass_file(self, tmp_path):
        (tmp_path / "a.tex").write_text("\\documentclass{article}")
        (tmp_path / "b.tex").write_text("\\input{preamble}")
        assert find_main_tex(tmp_path) == tmp_path / "a.tex"

    def test_multiple_documentclass_files_falls_to_alphabetical(self, tmp_path):
        (tmp_path / "z.tex").write_text("\\documentclass{article}")
        (tmp_path / "a.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path) == tmp_path / "a.tex"

    def test_fallback_alphabetical(self, tmp_path):
        (tmp_path / "z_final.tex").write_text("\\input{a}")
        (tmp_path / "m_middle.tex").write_text("\\input{b}")
        (tmp_path / "a_first.tex").write_text("\\input{c}")
        assert find_main_tex(tmp_path) == tmp_path / "a_first.tex"

    def test_no_tex_files_raises(self, tmp_path):
        with pytest.raises(MainTexNotFoundError):
            find_main_tex(tmp_path)

    def test_subdirectory_files_included_in_rglob(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "chapter.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path) == sub / "chapter.tex"

    def test_known_name_in_subdir_not_matched(self, tmp_path):
        """Known name check is source_dir / name (flat), not rglob."""
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "main.tex").write_text("\\documentclass{article}")
        # main.tex is in subdir, not directly in source_dir
        # Should fall through to documentclass or alphabetical, not match known name
        assert find_main_tex(tmp_path) == sub / "main.tex"

    def test_known_name_priority_over_subdir_documentclass(self, tmp_path):
        """Direct child main.tex takes priority over subdir file with documentclass."""
        (tmp_path / "main.tex").write_text("\\input{a}")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "other.tex").write_text("\\documentclass{article}")
        assert find_main_tex(tmp_path) == tmp_path / "main.tex"
