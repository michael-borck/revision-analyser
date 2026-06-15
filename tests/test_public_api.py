"""Canonical public surface — uniform across the -analyser family."""
import revision_analyser
from revision_analyser import (
    MANIFEST,
    Author,
    RevisionAnalyser,
    RevisionAnalyserError,
    RevisionAnalysis,
    RevisionEvent,
    __version__,
    analyse,
)


def test_canonical_names_import():
    assert RevisionAnalyser is not None
    assert RevisionAnalysis is not None
    assert RevisionEvent is not None
    assert Author is not None
    assert RevisionAnalyserError is not None


def test_analyse_is_callable():
    assert callable(analyse)


def test_manifest_name():
    assert MANIFEST["name"] == "revision-analyser"


def test_version_is_str():
    assert isinstance(__version__, str)


def test_names_in_all():
    for name in (
        "RevisionAnalyser",
        "RevisionAnalysis",
        "analyse",
        "MANIFEST",
        "__version__",
        "RevisionAnalyserError",
        "RevisionEvent",
        "Author",
    ):
        assert name in revision_analyser.__all__
