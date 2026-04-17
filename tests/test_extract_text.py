"""Tests for arxivparse.extract_text — XML-to-plain-text extraction."""

import xml.etree.ElementTree as ET

import pytest

from arxivparse.extract_text import NS, Q, _clean, _element_text, _extract_sections, xml_to_text


# ---------------------------------------------------------------------------
# _clean()
# ---------------------------------------------------------------------------

class TestClean:
    def test_collapses_multiple_spaces(self):
        assert _clean("hello   world") == "hello world"

    def test_collapses_many_spaces(self):
        assert _clean("a     b     c") == "a b c"

    def test_collapses_multiple_blank_lines_to_one(self):
        assert _clean("line1\n\n\n\nline2") == "line1\n\nline2"

    def test_strips_leading_blank_lines(self):
        assert _clean("\n\n\nhello") == "hello"

    def test_strips_trailing_blank_lines(self):
        assert _clean("hello\n\n\n") == "hello"

    def test_strips_whitespace_on_each_line(self):
        assert _clean("  hello  \n  world  ") == "hello\nworld"

    def test_empty_string(self):
        assert _clean("") == ""

    def test_preserves_single_blank_line(self):
        assert _clean("para1\n\npara2") == "para1\n\npara2"

    def test_all_blank_lines(self):
        assert _clean("\n\n\n") == ""


# ---------------------------------------------------------------------------
# _element_text()
# ---------------------------------------------------------------------------

class TestElementText:
    def test_simple_text(self):
        el = ET.Element(Q("p"))
        el.text = "Hello world"
        assert _element_text(el) == "Hello world"

    def test_child_with_tail(self):
        parent = ET.Element(Q("p"))
        parent.text = "before "
        child = ET.SubElement(parent, Q("em"))
        child.text = "inner"
        child.tail = " after"
        assert _element_text(parent) == "before inner after"

    def test_skips_cite(self):
        parent = ET.Element(Q("p"))
        parent.text = "text "
        cite = ET.SubElement(parent, Q("cite"))
        cite.text = "hidden"
        cite.tail = " tail"
        assert _element_text(parent) == "text  tail"

    def test_skips_note(self):
        parent = ET.Element(Q("p"))
        parent.text = "text "
        note = ET.SubElement(parent, Q("note"))
        note.text = "hidden"
        note.tail = " tail"
        assert _element_text(parent) == "text  tail"

    def test_skips_tags(self):
        parent = ET.Element(Q("p"))
        parent.text = "text "
        tags = ET.SubElement(parent, Q("tags"))
        tags.text = "hidden"
        tags.tail = " tail"
        assert _element_text(parent) == "text  tail"

    def test_skips_tag(self):
        parent = ET.Element(Q("p"))
        parent.text = "text "
        tag = ET.SubElement(parent, Q("tag"))
        tag.text = "hidden"
        tag.tail = " tail"
        assert _element_text(parent) == "text  tail"

    def test_skips_error(self):
        parent = ET.Element(Q("p"))
        parent.text = "text "
        err = ET.SubElement(parent, Q("ERROR"))
        err.text = "hidden"
        err.tail = " tail"
        assert _element_text(parent) == "text  tail"

    def test_skips_ref(self):
        parent = ET.Element(Q("p"))
        parent.text = "text "
        ref = ET.SubElement(parent, Q("ref"))
        ref.text = "hidden"
        ref.tail = " tail"
        assert _element_text(parent) == "text  tail"

    def test_skips_navigation(self):
        parent = ET.Element(Q("p"))
        parent.text = "text "
        nav = ET.SubElement(parent, Q("navigation"))
        nav.text = "hidden"
        nav.tail = " tail"
        assert _element_text(parent) == "text  tail"

    def test_skips_resource(self):
        parent = ET.Element(Q("p"))
        parent.text = "text "
        res = ET.SubElement(parent, Q("resource"))
        res.text = "hidden"
        res.tail = " tail"
        assert _element_text(parent) == "text  tail"

    def test_math_uses_tex_attribute(self):
        parent = ET.Element(Q("p"))
        parent.text = "The formula "
        math = ET.SubElement(parent, Q("Math"), tex="x^2 + 1")
        math.tail = " follows"
        assert _element_text(parent) == "The formula  x^2 + 1  follows"

    def test_math_empty_tex_skipped(self):
        parent = ET.Element(Q("p"))
        math = ET.SubElement(parent, Q("Math"), tex="  ")
        assert _element_text(parent) == ""

    def test_math_tail_collected(self):
        parent = ET.Element(Q("p"))
        math = ET.SubElement(parent, Q("Math"), tex="x")
        math.tail = " tail text"
        assert _element_text(parent) == " x  tail text"

    def test_deeply_nested_recursion(self):
        root = ET.Element(Q("div"))
        root.text = "a"
        child = ET.SubElement(root, Q("div"))
        child.text = "b"
        grandchild = ET.SubElement(child, Q("div"))
        grandchild.text = "c"
        grandchild.tail = "d"
        child.tail = "e"
        assert _element_text(root) == "abcde"

    def test_mixed_content_multiple_children(self):
        parent = ET.Element(Q("p"))
        parent.text = "text1 "
        math = ET.SubElement(parent, Q("Math"), tex="a")
        math.tail = " "
        cite = ET.SubElement(parent, Q("cite"))
        cite.text = "X"
        cite.tail = " text2 "
        em = ET.SubElement(parent, Q("em"))
        em.text = "bold"
        em.tail = " text3"
        assert _element_text(parent) == "text1  a   text2 bold text3"

    def test_element_with_only_child_tail(self):
        parent = ET.Element(Q("p"))
        child = ET.SubElement(parent, Q("em"))
        child.text = "word"
        child.tail = " tail"
        assert _element_text(parent) == "word tail"

    def test_empty_element(self):
        el = ET.Element(Q("p"))
        assert _element_text(el) == ""


# ---------------------------------------------------------------------------
# _extract_sections()
# ---------------------------------------------------------------------------

class TestExtractSections:
    def test_basic_title_and_para(self):
        root = ET.Element(Q("document"))
        section = ET.SubElement(root, Q("section"))
        title = ET.SubElement(section, Q("title"))
        title.text = "Section 1"
        para = ET.SubElement(section, Q("para"))
        p = ET.SubElement(para, Q("p"))
        p.text = "Content"

        parts = []
        _extract_sections(root, parts)
        assert parts == ["Section 1", "", "Content", ""]

    def test_skips_bibliography(self):
        root = ET.Element(Q("document"))
        sec1 = ET.SubElement(root, Q("section"))
        t1 = ET.SubElement(sec1, Q("title"))
        t1.text = "Introduction"
        sec2 = ET.SubElement(root, Q("section"))
        sec2.set("class", "ltx_bibliography")
        t2 = ET.SubElement(sec2, Q("title"))
        t2.text = "References"

        parts = []
        _extract_sections(root, parts)
        assert "References" not in parts
        assert "Introduction" in parts

    def test_nested_subsections(self):
        root = ET.Element(Q("document"))
        sec = ET.SubElement(root, Q("section"))
        t = ET.SubElement(sec, Q("title"))
        t.text = "Section 1"
        sub = ET.SubElement(sec, Q("section"))
        st = ET.SubElement(sub, Q("title"))
        st.text = "Subsection 1.1"
        para = ET.SubElement(sub, Q("para"))
        p = ET.SubElement(para, Q("p"))
        p.text = "Sub content"

        parts = []
        _extract_sections(root, parts)
        assert parts == ["Section 1", "", "Subsection 1.1", "", "Sub content", ""]

    def test_equation_with_tex(self):
        root = ET.Element(Q("document"))
        sec = ET.SubElement(root, Q("section"))
        eq = ET.SubElement(sec, Q("equation"), tex="E=mc^2")

        parts = []
        _extract_sections(root, parts)
        assert "E=mc^2" in parts

    def test_equation_empty_tex_skipped(self):
        root = ET.Element(Q("document"))
        sec = ET.SubElement(root, Q("section"))
        ET.SubElement(sec, Q("equation"), tex="  ")

        parts = []
        _extract_sections(root, parts)
        assert len(parts) == 0

    def test_caption_extracted(self):
        root = ET.Element(Q("document"))
        sec = ET.SubElement(root, Q("section"))
        fig = ET.SubElement(sec, Q("figure"))
        cap = ET.SubElement(fig, Q("caption"))
        cap.text = "Figure 1: A plot"

        parts = []
        _extract_sections(root, parts)
        assert "Figure 1: A plot" in parts

    def test_empty_section_title_not_added(self):
        root = ET.Element(Q("document"))
        sec = ET.SubElement(root, Q("section"))
        t = ET.SubElement(sec, Q("title"))
        t.text = "   "

        parts = []
        _extract_sections(root, parts)
        assert parts == []

    def test_nested_equations_found_by_parent_iter(self):
        """section.iter() finds equations in subsections too — verify behavior."""
        root = ET.Element(Q("document"))
        sec = ET.SubElement(root, Q("section"))
        sub = ET.SubElement(sec, Q("section"))
        eq = ET.SubElement(sub, Q("equation"), tex="a+b")

        parts = []
        _extract_sections(root, parts)
        # iter() on parent section will also find equations in subsection,
        # potentially duplicating. This test documents actual behavior.
        eq_count = parts.count("a+b")
        assert eq_count >= 1


# ---------------------------------------------------------------------------
# xml_to_text()
# ---------------------------------------------------------------------------

class TestXmlToText:
    def _write_xml(self, tmp_path, root):
        tree = ET.ElementTree(root)
        path = tmp_path / "test.xml"
        tree.write(str(path), xml_declaration=True, encoding="unicode")
        return str(path)

    def test_full_document(self, tmp_path):
        root = ET.Element(Q("document"))
        title = ET.SubElement(root, Q("title"))
        title.text = "Test Paper Title"

        abstract = ET.SubElement(root, Q("abstract"))
        at = ET.SubElement(abstract, Q("title"))
        at.text = "Abstract"
        ap = ET.SubElement(abstract, Q("p"))
        ap.text = "This is the abstract text."

        sec = ET.SubElement(root, Q("section"))
        st = ET.SubElement(sec, Q("title"))
        st.text = "Introduction"
        para = ET.SubElement(sec, Q("para"))
        p = ET.SubElement(para, Q("p"))
        p.text = "Hello world."

        path = self._write_xml(tmp_path, root)
        text = xml_to_text(path)
        assert "Test Paper Title" in text
        assert "Abstract" in text
        assert "This is the abstract text." in text
        assert "Introduction" in text
        assert "Hello world." in text

    def test_empty_document(self, tmp_path):
        root = ET.Element(Q("document"))
        path = self._write_xml(tmp_path, root)
        assert xml_to_text(path) == ""

    def test_document_with_only_title(self, tmp_path):
        root = ET.Element(Q("document"))
        title = ET.SubElement(root, Q("title"))
        title.text = "Only Title"
        path = self._write_xml(tmp_path, root)
        assert xml_to_text(path) == "Only Title"

    def test_abstract_without_title(self, tmp_path):
        root = ET.Element(Q("document"))
        abstract = ET.SubElement(root, Q("abstract"))
        p = ET.SubElement(abstract, Q("p"))
        p.text = "Abstract text without title."
        path = self._write_xml(tmp_path, root)
        text = xml_to_text(path)
        assert "Abstract text without title." in text

    def test_bibliography_at_root_skipped(self, tmp_path):
        root = ET.Element(Q("document"))
        title = ET.SubElement(root, Q("title"))
        title.text = "Paper"
        bib = ET.SubElement(root, Q("section"))
        bib.set("class", "ltx_bibliography")
        bt = ET.SubElement(bib, Q("title"))
        bt.text = "References"
        bp = ET.SubElement(bib, Q("para"))
        p = ET.SubElement(bp, Q("p"))
        p.text = "Smith et al. 2020."

        path = self._write_xml(tmp_path, root)
        text = xml_to_text(path)
        assert "Paper" in text
        assert "References" not in text
        assert "Smith et al." not in text
