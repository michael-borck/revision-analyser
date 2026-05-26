"""revision-analyser — .docx tracked-changes analysis for the lens family."""
from .analyser import RevisionAnalyser
from .exceptions import RevisionAnalyserError
from .schemas import Author, RevisionAnalysis, RevisionEvent

__all__ = [
    "RevisionAnalyser",
    "RevisionAnalyserError",
    "RevisionAnalysis",
    "RevisionEvent",
    "Author",
]
