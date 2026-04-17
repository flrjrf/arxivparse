"""Extract plain text from LaTeXML XML output.

Targets QASPER-style output: clean body text (title, abstract, sections,
paragraphs, figure/table captions, math) without bibliography, footnotes,
author metadata, or references.
"""

import xml.etree.ElementTree as ET

NS = "http://dlmf.nist.gov/LaTeXML"
Q = lambda tag: f"{{{NS}}}{tag}"


def xml_to_text(xml_path: str) -> str:
    """Extract plain text from a LaTeXML XML file.

    Returns clean text suitable for downstream NLP/ML use.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    parts = []

    # Document title
    for title in root.findall(Q("title")):
        text = _element_text(title).strip()
        if text:
            parts.append(text)
            parts.append("")

    # Abstract
    for abstract in root.findall(Q("abstract")):
        for title in abstract.findall(Q("title")):
            text = _element_text(title).strip()
            if text:
                parts.append(text)
                parts.append("")
        for p in abstract.iter(Q("p")):
            text = _element_text(p).strip()
            if text:
                parts.append(text)
                parts.append("")

    # Sections (recursive)
    _extract_sections(root, parts)

    return _clean("\n".join(parts))


def _extract_sections(parent: ET.Element, parts: list[str]) -> None:
    """Extract sections in document order, recursing into subsections."""
    for section in parent.findall(Q("section")):
        # Skip bibliography
        if section.get("class") == "ltx_bibliography":
            continue

        # Section title
        for title in section.findall(Q("title")):
            text = _element_text(title).strip()
            if text:
                parts.append(text)
                parts.append("")

        # Paragraphs direct under this section (not in subsections)
        for para in section.findall(Q("para")):
            for p in para.findall(Q("p")):
                text = _element_text(p).strip()
                if text:
                    parts.append(text)
                    parts.append("")

        # Display math / equations
        for eq in section.iter(Q("equation")):
            tex = eq.get("tex", "")
            if tex.strip():
                parts.append(tex)
                parts.append("")

        # Figure/table captions
        for caption in section.iter(Q("caption")):
            text = _element_text(caption).strip()
            if text:
                parts.append(text)
                parts.append("")

        # Recurse into subsections
        _extract_sections(section, parts)


def _element_text(element: ET.Element) -> str:
    """Recursively extract text, handling math via tex attr and skipping noise.

    Properly handles ElementTree's .text and .tail model.
    """
    parts = []

    # .text = text before first child
    if element.text:
        parts.append(element.text)

    for child in element:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag

        # Math → use tex attribute
        if local == "Math":
            tex = child.get("tex", "")
            if tex.strip():
                parts.append(f" {tex} ")
            # Don't add tail here (handled below)
        # Skip noise
        elif local in ("cite", "note", "tags", "tag", "ERROR", "ref",
                       "navigation", "resource"):
            pass
        # Recurse
        elif len(child) > 0:
            parts.append(_element_text(child))
        elif child.text:
            parts.append(child.text)

        # .tail = text after this child's closing tag
        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


def _clean(text: str) -> str:
    """Normalize whitespace and remove artifacts."""
    # Collapse multiple spaces (from stripped elements like citations)
    import re
    text = re.sub(r"  +", " ", text)

    lines = text.splitlines()
    cleaned = []
    blank_count = 0

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(stripped)

    # Strip leading/trailing blank lines
    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return "\n".join(cleaned)
