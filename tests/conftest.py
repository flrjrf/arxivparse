"""Shared fixtures for arxivparser tests."""

import xml.etree.ElementTree as ET

import pytest

NS = "http://dlmf.nist.gov/LaTeXML"


@pytest.fixture
def Q():
    """Namespace-qualify a tag name."""
    return lambda tag: f"{{{NS}}}{tag}"
