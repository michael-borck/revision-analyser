"""FastAPI service — revision-analyser."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from lens_contract import add_contract_routes, add_cors, upload_tempfile

from .analyser import RevisionAnalyser
from .exceptions import RevisionAnalyserError
from .manifest import MANIFEST
from .schemas import RevisionAnalysis

_lens = RevisionAnalyser()

app = FastAPI(
    title="revision-analyser",
    description=".docx tracked-changes analysis — drafting trajectory, paste-burst detection, authorship",
    version=MANIFEST["version"],
    docs_url="/docs",
    redoc_url="/redoc",
)

add_contract_routes(app, MANIFEST)
add_cors(app, env_prefix="REVISION_ANALYSER")


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": "revision-analyser",
        "version": MANIFEST["version"],
        "status": "running",
        "endpoints": {"health": "/health", "manifest": "/manifest", "analyse": "/analyse"},
    }


@app.post("/analyse", response_model=RevisionAnalysis)
async def analyse(
    file: UploadFile = File(..., description=".docx file (with Track Changes)"),
) -> RevisionAnalysis:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Empty file")
    with upload_tempfile(content, file.filename) as tmp_path:
        try:
            return _lens.analyse(tmp_path)
        except RevisionAnalyserError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
