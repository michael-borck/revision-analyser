"""HTTP smoke tests — the family contract surface."""
from pathlib import Path

from fastapi.testclient import TestClient

from revision_analyser.api import app
from revision_analyser.manifest import MANIFEST


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"] == MANIFEST["version"]


def test_manifest():
    r = client.get("/manifest")
    assert r.status_code == 200
    m = r.json()
    assert m["name"] == "revision-analyser"
    assert m["auto_routable"] is False
    assert ".docx" in m["extensions"]


def test_analyse_empty_returns_422():
    r = client.post("/analyse", files={"file": ("x.docx", b"", "application/octet-stream")})
    assert r.status_code == 422


def test_analyse_paste_burst(docx_paste_burst: Path):
    r = client.post(
        "/analyse",
        files={"file": (docx_paste_burst.name, docx_paste_burst.read_bytes(),
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["track_changes_enabled"] is True
    assert body["paste_burst_count"] == 1
    assert "paste_burst_present" in body["flags"]


def test_analyse_unsupported_returns_400(tmp_path: Path):
    p = tmp_path / "x.txt"
    p.write_bytes(b"plain text")
    r = client.post("/analyse", files={"file": ("x.txt", p.read_bytes(), "text/plain")})
    assert r.status_code == 400
