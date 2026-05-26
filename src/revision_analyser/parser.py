"""OOXML tracked-changes parser — pure stdlib (zipfile + ElementTree).

Word's Track Changes embeds revision events directly in `word/document.xml` as:

  <w:ins w:id="N" w:author="..." w:date="2026-05-26T12:34:56Z">
    <w:r><w:t>inserted text</w:t></w:r>
  </w:ins>

  <w:del w:id="N" w:author="..." w:date="...">
    <w:r><w:delText>deleted text</w:delText></w:r>
  </w:del>

  <w:moveFrom .../>  <w:moveTo .../>

python-docx doesn't expose these, so we read document.xml directly.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

# WordprocessingML namespace.
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS = {"w": _W_NS}


@dataclass
class ParsedEvent:
    """In-memory representation of one tracked-change event."""

    type: str
    author: str | None
    timestamp: str | None
    text: str

    @property
    def word_count(self) -> int:
        return len(self.text.split()) if self.text else 0


def parse_docx(path: str | Path) -> list[ParsedEvent]:
    """Return a flat list of every tracked-change event found in the .docx.

    Order is document order (depth-first). If document.xml is missing or the
    file isn't a zip, raises zipfile.BadZipFile / KeyError — callers wrap
    these for a friendlier error.
    """
    with zipfile.ZipFile(path) as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
    root = tree.getroot()

    events: list[ParsedEvent] = []
    # iter walks the tree depth-first, in document order — exactly what we want.
    for el in root.iter():
        tag = _localname(el.tag)
        if tag == "ins":
            events.append(_event_from(el, "insertion"))
        elif tag == "del":
            events.append(_event_from(el, "deletion"))
        elif tag == "moveFrom":
            events.append(_event_from(el, "move-from"))
        elif tag == "moveTo":
            events.append(_event_from(el, "move-to"))
    return events


def _localname(tag: str) -> str:
    """Strip the {namespace} prefix from an ElementTree tag."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _event_from(el: ET.Element, event_type: str) -> ParsedEvent:
    """Extract the standard fields from a w:ins/w:del/w:moveFrom/w:moveTo element."""
    author = el.attrib.get(f"{{{_W_NS}}}author")
    date = el.attrib.get(f"{{{_W_NS}}}date")
    text_parts: list[str] = []
    # w:t for insertions/moves; w:delText for deletions. Walk descendants to
    # catch nested runs (a single <w:ins> can wrap multiple <w:r><w:t> runs).
    for t in el.iter():
        tname = _localname(t.tag)
        if tname in ("t", "delText") and t.text:
            text_parts.append(t.text)
    return ParsedEvent(
        type=event_type,
        author=author or None,
        timestamp=date or None,
        text="".join(text_parts),
    )
