"""Capability manifest for the lens family (consumed by auto-analyser)."""
from __future__ import annotations

from lens_contract import make_manifest

# Explicit-only — .docx auto-routes to document-analyser for text. This is a
# different interpretation of the same bytes (revision *history*, not content).
MANIFEST = make_manifest(
    name="revision-analyser",
    accepts=["revision-history", "tracked-changes"],
    extensions=[".docx"],
    auto_routable=False,
    produces="RevisionAnalysis",
)
