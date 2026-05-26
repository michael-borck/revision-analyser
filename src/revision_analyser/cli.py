"""CLI entry point for revision-analyser."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    from lens_contract import run_contract_subcommands

    from .manifest import MANIFEST

    if run_contract_subcommands(
        MANIFEST,
        app_path="revision_analyser.api:app",
        default_port=8016,
        env_prefix="REVISION_ANALYSER",
    ):
        return

    parser = argparse.ArgumentParser(
        prog="revision-analyser",
        description=".docx tracked-changes analysis — drafting trajectory, paste-burst detection",
        epilog="subcommands: `serve` (HTTP API on port 8016), `manifest` (capability manifest)",
    )
    parser.add_argument("file", type=Path, help=".docx file (with Track Changes)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")
    args = parser.parse_args()

    _run(args)


def _run(args) -> None:
    from .analyser import RevisionAnalyser
    from .exceptions import RevisionAnalyserError

    try:
        result = RevisionAnalyser().analyse(args.file)
    except RevisionAnalyserError as e:
        if args.as_json:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(result.model_dump_json(indent=2))
        return

    _print_summary(result)


def _print_summary(result) -> None:
    print(f"File:           {result.file_path}")
    print(f"Format:         .{result.file_format}  ({result.file_size:,} bytes)")
    if not result.track_changes_enabled:
        print()
        print("No tracked changes recorded in this document.")
        print("(Either Track Changes wasn't enabled, or there are no revisions to show.)")
        if result.flags:
            print(f"Flags: {', '.join(result.flags)}")
        return
    print(f"Insertions:     {result.total_insertions}  ({result.insertion_word_count} words)")
    print(f"Deletions:      {result.total_deletions}  ({result.deletion_word_count} words)")
    if result.total_moves:
        print(f"Moves:          {result.total_moves}")
    if result.paste_burst_count:
        print(f"Paste bursts:   {result.paste_burst_count}  (insertions ≥ {result.paste_burst_threshold_words} words)")
        for pb in result.paste_bursts[:3]:
            snippet = pb.text.strip().replace("\n", " ")
            snippet = snippet[:80] + ("…" if len(snippet) > 80 else "")
            print(f"                - [{pb.word_count}w by {pb.author or '?'}] {snippet}")
    if result.authors:
        if len(result.authors) == 1:
            a = result.authors[0]
            print(f"Author:         {a.name}  (+{a.insertion_word_count}w, -{a.deletion_word_count}w)")
        else:
            print(f"Authors:        {len(result.authors)}")
            for a in result.authors:
                print(f"                - {a.name}  (+{a.insertion_word_count}w, -{a.deletion_word_count}w)")
    if result.timeline_minutes is not None:
        h, m = divmod(int(result.timeline_minutes), 60)
        if h:
            print(f"Timeline:       {result.timeline_minutes:.1f} min  ({h}h {m}m)")
        else:
            print(f"Timeline:       {result.timeline_minutes:.1f} min")
        if result.timeline_first:
            print(f"  first:        {result.timeline_first}")
        if result.timeline_last:
            print(f"  last:         {result.timeline_last}")
    if result.flags:
        print()
        print("Flags:")
        for f in result.flags:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
