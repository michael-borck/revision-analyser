"""End-to-end tests for RevisionAnalyser aggregation + flags."""
from pathlib import Path

import pytest

from revision_analyser import RevisionAnalyser, RevisionAnalyserError, RevisionAnalysis


class TestNoRevisions:
    def test_track_changes_disabled_is_signalled(self, docx_no_revisions: Path):
        r = RevisionAnalyser().analyse(docx_no_revisions)
        assert isinstance(r, RevisionAnalysis)
        assert r.track_changes_enabled is False
        assert r.total_insertions == 0
        assert r.total_deletions == 0
        assert "no_revisions_recorded" in r.flags
        # When track_changes_enabled is False, no other flags should fire.
        assert all(f == "no_revisions_recorded" for f in r.flags)


class TestSimple:
    def test_counts(self, docx_simple_revisions: Path):
        r = RevisionAnalyser().analyse(docx_simple_revisions)
        assert r.track_changes_enabled
        assert r.total_insertions == 2
        assert r.total_deletions == 1
        assert r.insertion_word_count == 4   # "Added word. " (2) + "second insertion" (2)
        assert r.deletion_word_count == 2    # "old phrase"

    def test_single_author_flag(self, docx_simple_revisions: Path):
        r = RevisionAnalyser().analyse(docx_simple_revisions)
        assert "single_author" in r.flags
        assert "multiple_authors" not in r.flags
        assert len(r.authors) == 1
        assert r.authors[0].name == "Jane Student"
        assert r.authors[0].insertion_count == 2
        assert r.authors[0].deletion_count == 1

    def test_timeline_minutes(self, docx_simple_revisions: Path):
        r = RevisionAnalyser().analyse(docx_simple_revisions)
        # 10:00 to 10:30 = 30 minutes.
        assert r.timeline_minutes == 30.0


class TestPasteBurst:
    def test_burst_detected(self, docx_paste_burst: Path):
        r = RevisionAnalyser().analyse(docx_paste_burst)
        assert r.paste_burst_count == 1
        assert "paste_burst_present" in r.flags
        assert r.paste_bursts[0].word_count == 40
        assert r.paste_burst_threshold_words == 25


class TestMultiAuthor:
    def test_multiple_authors_flag(self, docx_multi_author: Path):
        r = RevisionAnalyser().analyse(docx_multi_author)
        assert "multiple_authors" in r.flags
        assert "single_author" not in r.flags
        assert len(r.authors) == 2


class TestShortTimeline:
    def test_short_timeline_flag(self, docx_short_timeline: Path):
        r = RevisionAnalyser().analyse(docx_short_timeline)
        # Edits span 5 minutes (10:00 → 10:05).
        assert r.timeline_minutes == 5.0
        assert "short_timeline" in r.flags


class TestDispatch:
    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(RevisionAnalyserError, match="not found"):
            RevisionAnalyser().analyse(tmp_path / "nope.docx")

    def test_unsupported_extension_raises(self, tmp_path: Path):
        p = tmp_path / "x.txt"
        p.write_text("hi")
        with pytest.raises(RevisionAnalyserError, match="Unsupported"):
            RevisionAnalyser().analyse(p)

    def test_corrupt_docx_raises(self, tmp_path: Path):
        p = tmp_path / "not-a-zip.docx"
        p.write_bytes(b"not a zip at all")
        with pytest.raises(RevisionAnalyserError, match="Not a valid .docx"):
            RevisionAnalyser().analyse(p)
