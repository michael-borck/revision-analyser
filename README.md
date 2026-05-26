# revision-analyser

**Reads a Word document's *drafting trajectory*** — not its final text. The
[lens-family](https://github.com/michael-borck/lens-analysers) member that
surfaces how a document was written, not what it says.

Parses Word's embedded *Track Changes* (`<w:ins>`, `<w:del>`, `<w:moveFrom>`,
`<w:moveTo>` elements in `document.xml`) to produce:

- timeline of insertions/deletions/moves with author and timestamp
- **paste-burst detection** (a single insertion ≥ N words ≈ paste from AI/elsewhere)
- per-author rollups (single-author vs collaborative editing)
- thrashing patterns (many small clustered edits)

> The single strongest written-work *process* signal — but only if the student
> had Track Changes on. A `.docx` with no revisions is itself a signal:
> `track_changes_enabled: false` (often means the final version was pasted in).
> Explicit-only: `.docx` continues to auto-route to `document-analyser` for
> content; invoke `revision-analyser` deliberately for the revision history.

**Scope:** v1 reads Word `.docx` tracked changes only. Google Docs revision
history (Drive API) and draft-sequence comparison are planned for v2.

## Install

```bash
pip install revision-analyser
```

## Use

**Python:**

```python
from revision_analyser import RevisionAnalyser

result = RevisionAnalyser().analyse("essay.docx")
print(result.track_changes_enabled)        # True
print(result.total_insertions)             # 47
print(result.paste_burst_count)            # 2
print(result.authors[0].name)              # "Jane Student"
print(result.timeline_minutes)             # 184.5  (≈ 3 hours of editing)
```

**CLI:**

```bash
revision-analyser essay.docx
revision-analyser essay.docx --json
revision-analyser serve
revision-analyser manifest
```

**HTTP** (`revision-analyser serve` on port 8016):

```bash
curl -F file=@essay.docx http://localhost:8016/analyse
```

## Signals

- **`track_changes_enabled`** — whether the doc carries any tracked revisions at all.
  *Absence* is itself a signal (final-paste workflow).
- **Totals** — insertion count, deletion count, move count.
- **Word-level totals** — `insertion_word_count`, `deletion_word_count`.
- **Paste bursts** — insertions whose single contiguous text is ≥ 25 words (tuneable).
  These are the strongest paste-from-elsewhere markers.
- **Authors** — list with per-author insertion/deletion totals. One author = self-edits;
  two = collaborative or feedback cycle.
- **Timeline** — `timeline_first`, `timeline_last`, `timeline_minutes` (span of activity).
- **Events** — a capped sample of the timeline for inspection.
- **Flags** — composite tags: `paste_burst_present`, `single_author`, `no_revisions_recorded`,
  `short_timeline`, `multiple_authors`.

## The family

| What you want | Use |
|---|---|
| The document's text + readability | **document-analyser** |
| The document's *metadata* (editing time, creator app) | **provenance-analyser** |
| The document's *revision history* | **revision-analyser** (this) |
| Reflective depth on text | **reflection-analyser** |
| Any file → right engine | **auto-analyser** |

Triangulation matters here. A polished essay with **no recorded revisions** + a
**short total editing time** (provenance-analyser) + a **descriptive depth band**
(reflection-analyser) tells a much more focused story than any of the three signals
alone.

## Limits

- v1 reads tracked changes only. If the student never enabled Track Changes, the doc
  reports `track_changes_enabled: false` — the absence is informative but bears no
  detail about the actual editing process.
- Author names are whatever Word recorded (`w:author` attribute) — often an
  install-time username, sometimes "Author" if anonymous.
- Timestamps reflect *when the tracked change was made* per the authoring machine's
  clock; trustworthy on a single machine, less so across collaborators.
- Paste-burst detection is a heuristic — long literary quotes will also score. Surface
  the burst text in the response so callers can audit.

## License

MIT
