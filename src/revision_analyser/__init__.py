"""revision-analyser — .docx tracked-changes analysis for the lens family."""
from importlib.metadata import version as _v
from pathlib import Path

from .analyser import RevisionAnalyser
from .exceptions import RevisionAnalyserError
from .manifest import MANIFEST
from .schemas import Author, RevisionAnalysis, RevisionEvent

__version__ = _v("revision-analyser")
del _v


def analyse(path: str | Path) -> RevisionAnalysis:
    """Analyse a .docx and return its revision-history signals."""
    return RevisionAnalyser().analyse(Path(path))


__all__ = [
    "RevisionAnalyser",
    "RevisionAnalysis",
    "analyse",
    "MANIFEST",
    "__version__",
    "RevisionAnalyserError",
    "RevisionEvent",
    "Author",
]
