"""Core revision analyser — parse + aggregate + compute flags."""
from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path

from .exceptions import RevisionAnalyserError
from .parser import ParsedEvent, parse_docx
from .schemas import Author, RevisionAnalysis, RevisionEvent

# Heuristic thresholds — surfaced in the schema so callers can see what we used.
_PASTE_BURST_THRESHOLD_WORDS = 25
_SHORT_TIMELINE_MINUTES = 10  # whole edit history compressed into <10 minutes is suspicious
_EVENTS_SAMPLE_CAP = 50


class RevisionAnalyser:
    """Read tracked changes from a .docx and produce per-author + aggregate signals."""

    def analyse(self, path: str | Path) -> RevisionAnalysis:
        path = Path(path)
        if not path.exists():
            raise RevisionAnalyserError(f"File not found: {path}")
        if path.suffix.lower() != ".docx":
            raise RevisionAnalyserError(
                f"Unsupported format: {path.suffix} (revision-analyser v1 supports .docx only)"
            )

        try:
            parsed = parse_docx(path)
        except (zipfile.BadZipFile, KeyError) as e:
            raise RevisionAnalyserError(
                f"Not a valid .docx (missing word/document.xml or corrupt zip): {e}"
            ) from e
        except Exception as e:
            raise RevisionAnalyserError(f"Failed to parse tracked changes: {e}") from e

        # Per-author rollup.
        authors: dict[str, Author] = {}
        events: list[RevisionEvent] = []
        paste_bursts: list[RevisionEvent] = []
        timestamps: list[datetime] = []
        ins_total = 0
        del_total = 0
        move_total = 0
        ins_words = 0
        del_words = 0

        for ev in parsed:
            rev_event = RevisionEvent(
                type=ev.type,
                author=ev.author,
                timestamp=ev.timestamp,
                text=ev.text,
                word_count=ev.word_count,
            )
            events.append(rev_event)

            # Per-type totals.
            if ev.type == "insertion":
                ins_total += 1
                ins_words += ev.word_count
                if ev.word_count >= _PASTE_BURST_THRESHOLD_WORDS:
                    paste_bursts.append(rev_event)
            elif ev.type == "deletion":
                del_total += 1
                del_words += ev.word_count
            else:  # move-from / move-to
                move_total += 1

            # Per-author rollup.
            if ev.author:
                a = authors.setdefault(ev.author, Author(name=ev.author))
                if ev.type == "insertion":
                    a.insertion_count += 1
                    a.insertion_word_count += ev.word_count
                elif ev.type == "deletion":
                    a.deletion_count += 1
                    a.deletion_word_count += ev.word_count
                else:
                    a.move_count += 1

            # Timeline.
            ts = _parse_iso(ev.timestamp)
            if ts is not None:
                timestamps.append(ts)

        # Timeline aggregation.
        first_dt = min(timestamps) if timestamps else None
        last_dt = max(timestamps) if timestamps else None
        span_minutes = None
        if first_dt and last_dt:
            span_minutes = round((last_dt - first_dt).total_seconds() / 60.0, 2)

        # Capped event sample — newest first so the most recent activity is first.
        events_sorted = sorted(
            events,
            key=lambda e: e.timestamp or "",
            reverse=True,
        )[:_EVENTS_SAMPLE_CAP]

        flags = _compute_flags(
            track_changes_enabled=bool(parsed),
            paste_burst_count=len(paste_bursts),
            author_count=len(authors),
            timeline_minutes=span_minutes,
        )

        return RevisionAnalysis(
            file_path=str(path),
            file_size=path.stat().st_size,
            file_format="docx",
            track_changes_enabled=bool(parsed),
            total_insertions=ins_total,
            total_deletions=del_total,
            total_moves=move_total,
            insertion_word_count=ins_words,
            deletion_word_count=del_words,
            paste_burst_threshold_words=_PASTE_BURST_THRESHOLD_WORDS,
            paste_burst_count=len(paste_bursts),
            paste_bursts=paste_bursts,
            authors=sorted(authors.values(), key=lambda a: a.name),
            timeline_first=first_dt.isoformat(timespec="seconds") if first_dt else None,
            timeline_last=last_dt.isoformat(timespec="seconds") if last_dt else None,
            timeline_minutes=span_minutes,
            events=events_sorted,
            flags=flags,
        )


def _parse_iso(s: str | None) -> datetime | None:
    """Parse a w:date attribute (`YYYY-MM-DDThh:mm:ssZ` or with offset)."""
    if not s:
        return None
    try:
        # Python accepts +00:00 but not bare 'Z' before 3.11; we're 3.11+ so this is fine.
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _compute_flags(
    *,
    track_changes_enabled: bool,
    paste_burst_count: int,
    author_count: int,
    timeline_minutes: float | None,
) -> list[str]:
    flags: list[str] = []
    if not track_changes_enabled:
        flags.append("no_revisions_recorded")
        # No further flags meaningful when there's nothing to flag.
        return flags
    if paste_burst_count > 0:
        flags.append("paste_burst_present")
    if author_count == 1:
        flags.append("single_author")
    elif author_count >= 2:
        flags.append("multiple_authors")
    if timeline_minutes is not None and timeline_minutes < _SHORT_TIMELINE_MINUTES:
        flags.append("short_timeline")
    return flags
