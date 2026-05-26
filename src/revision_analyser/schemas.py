"""Pydantic schemas for revision-analyser output."""
from __future__ import annotations

from pydantic import BaseModel, Field


class RevisionEvent(BaseModel):
    """A single tracked-change event (insertion / deletion / move) from document.xml."""

    type: str = Field(description="'insertion' | 'deletion' | 'move-from' | 'move-to'")
    author: str | None = None
    timestamp: str | None = Field(None, description="ISO 8601 from the w:date attribute, or None.")
    text: str = Field(description="The inserted or deleted text content.")
    word_count: int = 0


class Author(BaseModel):
    """Rollup of one author's contribution."""

    name: str
    insertion_count: int = 0
    deletion_count: int = 0
    move_count: int = 0
    insertion_word_count: int = 0
    deletion_word_count: int = 0


class RevisionAnalysis(BaseModel):
    """Top-level result returned by RevisionAnalyser.analyse()."""

    file_path: str
    file_size: int
    file_format: str = "docx"

    track_changes_enabled: bool = Field(
        description="True iff any tracked-change elements were found in document.xml.",
    )

    # Totals
    total_insertions: int = 0
    total_deletions: int = 0
    total_moves: int = 0
    insertion_word_count: int = 0
    deletion_word_count: int = 0

    # Paste-burst signals
    paste_burst_threshold_words: int = Field(
        25,
        description="Insertions whose contiguous text is at least this long count as a paste-burst.",
    )
    paste_burst_count: int = 0
    paste_bursts: list[RevisionEvent] = Field(
        default_factory=list,
        description="The actual paste-burst events for transparency.",
    )

    # Authors
    authors: list[Author] = Field(default_factory=list)

    # Timeline
    timeline_first: str | None = None
    timeline_last: str | None = None
    timeline_minutes: float | None = Field(
        None,
        description="Span between first and last tracked change, in minutes.",
    )

    # Events sample (ordered by timestamp; capped to avoid huge responses)
    events: list[RevisionEvent] = Field(
        default_factory=list,
        description="Up to N tracked-change events for inspection (newest first).",
    )

    # Heuristic flags
    flags: list[str] = Field(
        default_factory=list,
        description=(
            "Composite tags: no_revisions_recorded, paste_burst_present, "
            "single_author, multiple_authors, short_timeline."
        ),
    )
