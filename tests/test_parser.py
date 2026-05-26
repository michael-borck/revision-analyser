"""Unit tests for the OOXML parser."""
from pathlib import Path

from revision_analyser.parser import parse_docx


def test_no_revisions(docx_no_revisions: Path):
    events = parse_docx(docx_no_revisions)
    assert events == []


def test_simple_revisions(docx_simple_revisions: Path):
    events = parse_docx(docx_simple_revisions)
    types = [e.type for e in events]
    assert types == ["insertion", "deletion", "insertion"]
    # First insertion's text is captured.
    assert events[0].text == "Added word. "
    # Author + timestamp parsed off the attribute.
    assert events[0].author == "Jane Student"
    assert events[0].timestamp == "2026-05-26T10:00:00Z"
    # Word counts on the dataclass property.
    assert events[0].word_count == 2  # "Added word."


def test_paste_burst_text_captured(docx_paste_burst: Path):
    events = parse_docx(docx_paste_burst)
    assert len(events) == 1
    assert events[0].word_count == 40


def test_multi_author(docx_multi_author: Path):
    events = parse_docx(docx_multi_author)
    authors = {e.author for e in events}
    assert authors == {"Jane Student", "Reviewer"}
