"""CLI smoke tests."""
import json
import subprocess
import sys
from pathlib import Path


def _run(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "revision_analyser.cli", *map(str, args)],
        capture_output=True,
        text=True,
    )


def test_missing_file_nonzero(tmp_path: Path):
    r = _run(tmp_path / "nope.docx")
    assert r.returncode != 0


def test_no_revisions_message(docx_no_revisions: Path):
    r = _run(docx_no_revisions)
    assert r.returncode == 0, r.stderr
    assert "No tracked changes recorded" in r.stdout


def test_simple_human_summary(docx_simple_revisions: Path):
    r = _run(docx_simple_revisions)
    assert r.returncode == 0, r.stderr
    assert "Insertions:" in r.stdout
    assert "Deletions:" in r.stdout
    assert "Author:" in r.stdout


def test_paste_burst_visible(docx_paste_burst: Path):
    r = _run(docx_paste_burst)
    assert r.returncode == 0, r.stderr
    assert "Paste bursts:" in r.stdout


def test_json_output(docx_simple_revisions: Path):
    r = _run(docx_simple_revisions, "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["total_insertions"] == 2


def test_manifest_subcommand():
    r = _run("manifest")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["name"] == "revision-analyser"
