"""Synthetic .docx fixtures with tracked changes.

python-docx writes valid .docx files but doesn't emit tracked-change elements
(<w:ins>, <w:del>, <w:moveFrom>, <w:moveTo>). For testing, we hand-craft a
minimal .docx (zip containing word/document.xml) with the elements we need.
The OOXML 'parts' we omit (themes, fonts, etc.) are optional — Word would
accept these files, but more importantly our parser only reads document.xml.
"""
from __future__ import annotations

import io
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# A minimal Content_Types and rels skeleton — not strictly required by our
# parser, but they're cheap and keep the file shape valid.
_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


def _build_docx(document_xml: str, tmp_path: Path, name: str = "doc.docx") -> Path:
    """Wrap a hand-written document.xml into a minimal-but-valid .docx zip."""
    path = tmp_path / name
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/document.xml", document_xml)
    return path


def _wrap(body_xml: str) -> str:
    """Wrap a body fragment in the standard w:document/w:body envelope."""
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{_W_NS}">
  <w:body>
    {body_xml}
  </w:body>
</w:document>"""


# ── fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def docx_no_revisions(tmp_path: Path) -> Path:
    body = """
    <w:p><w:r><w:t>A plain paragraph with no tracked changes at all.</w:t></w:r></w:p>
    """
    return _build_docx(_wrap(body), tmp_path, "plain.docx")


@pytest.fixture
def docx_simple_revisions(tmp_path: Path) -> Path:
    """Two insertions and one deletion by one author."""
    body = """
    <w:p>
      <w:r><w:t>Original text. </w:t></w:r>
      <w:ins w:id="1" w:author="Jane Student" w:date="2026-05-26T10:00:00Z">
        <w:r><w:t>Added word. </w:t></w:r>
      </w:ins>
      <w:del w:id="2" w:author="Jane Student" w:date="2026-05-26T10:05:00Z">
        <w:r><w:delText>old phrase</w:delText></w:r>
      </w:del>
      <w:ins w:id="3" w:author="Jane Student" w:date="2026-05-26T10:30:00Z">
        <w:r><w:t>second insertion</w:t></w:r>
      </w:ins>
    </w:p>
    """
    return _build_docx(_wrap(body), tmp_path, "simple.docx")


@pytest.fixture
def docx_paste_burst(tmp_path: Path) -> Path:
    """One insertion ≥ 25 words → paste-burst should fire."""
    burst_words = " ".join(["paragraph"] * 40)
    body = f"""
    <w:p>
      <w:ins w:id="1" w:author="Jane Student" w:date="2026-05-26T10:00:00Z">
        <w:r><w:t>{burst_words}</w:t></w:r>
      </w:ins>
    </w:p>
    """
    return _build_docx(_wrap(body), tmp_path, "burst.docx")


@pytest.fixture
def docx_multi_author(tmp_path: Path) -> Path:
    body = """
    <w:p>
      <w:ins w:id="1" w:author="Jane Student" w:date="2026-05-26T09:00:00Z">
        <w:r><w:t>by Jane</w:t></w:r>
      </w:ins>
      <w:ins w:id="2" w:author="Reviewer" w:date="2026-05-26T11:00:00Z">
        <w:r><w:t>by Reviewer</w:t></w:r>
      </w:ins>
    </w:p>
    """
    return _build_docx(_wrap(body), tmp_path, "multi.docx")


@pytest.fixture
def docx_short_timeline(tmp_path: Path) -> Path:
    """Edits clustered into <10 minutes → short_timeline flag."""
    body = """
    <w:p>
      <w:ins w:id="1" w:author="Jane" w:date="2026-05-26T10:00:00Z">
        <w:r><w:t>a</w:t></w:r>
      </w:ins>
      <w:ins w:id="2" w:author="Jane" w:date="2026-05-26T10:02:00Z">
        <w:r><w:t>b</w:t></w:r>
      </w:ins>
      <w:ins w:id="3" w:author="Jane" w:date="2026-05-26T10:05:00Z">
        <w:r><w:t>c</w:t></w:r>
      </w:ins>
    </w:p>
    """
    return _build_docx(_wrap(body), tmp_path, "short.docx")
