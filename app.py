"""
Clean app.py (organized + CasFinder route included)

Notes:
- Put ALL API routes before StaticFiles mount.
- Make sure you have this file too (can be empty): tools/__init__.py
- Your CasFinder file should be: tools/casfinder.py with run_casfinder()
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ✅ Your existing utilities (already in your repo)
from crispr_utils import (  # type: ignore
    load_phage_sequence_by_id,
    load_spacers_from_cache,
    crispr_match_count_from_spacers,
)

# ✅ New: CasFinder runner
from tools.casfinder import run_casfinder  # type: ignore


app = FastAPI(title="UTI Bacteria → Best Phage Finder", version="1.0.0")

# CORS (keep permissive unless you want to lock it down)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Basic routes
# ---------------------------

@app.get("/")
def home():
    return {"status": "ok", "message": "UTI-phage API is running"}


@app.get("/ui")
def ui():
    # Your frontend entrypoint
    return FileResponse("frontend/index.html")


# ---------------------------
# Existing API endpoints (keep these)
# ---------------------------

@app.get("/bacteria")
def list_bacteria():
    """
    Returns bacteria list from bacteria_list.txt (adjust if your logic differs)
    """
    path = "bacteria_list.txt"
    if not os.path.exists(path):
        return {"bacteria": [], "warning": "bacteria_list.txt not found"}
    with open(path, "r", encoding="utf-8") as f:
        items = [line.strip() for line in f if line.strip()]
    return {"bacteria": items}


@app.get("/predict")
def predict(
    bacteria: str = Query(..., description="Bacteria name"),
    top_k: int = Query(10, ge=1, le=100, description="Number of top phages"),
):
    """
    Keep your current logic here. This is a CLEAN placeholder.

    If you already have working code for /predict in your current app.py,
    copy that logic into this function body.
    """
    # TODO: paste your existing /predict logic here
    return {"bacteria": bacteria, "top_k": top_k, "results": []}


@app.get("/crispr_check_batch")
def crispr_check_batch(
    bacteria: str = Query(..., description="Bacteria name"),
    phage_ids: str = Query(..., description="Comma-separated phage IDs"),
):
    """
    Keep your current logic here. This is a CLEAN placeholder.

    If you already have working code for /crispr_check_batch in your current app.py,
    copy that logic into this function body.
    """
    ids = [x.strip() for x in phage_ids.split(",") if x.strip()]
    # TODO: paste your existing CRISPR batch logic here
    return {"bacteria": bacteria, "phage_ids": ids, "results": []}


# ---------------------------
# ✅ NEW: CasFinder API endpoint
# ---------------------------

@app.post("/api/casfinder")
async def casfinder_api(file: UploadFile = File(...)):
    """
    Upload a bacterial genome FASTA (.fna/.fa/.fasta).
    Runs: Prodigal -> MacSyFinder (CasFinder models)
    Returns job_id + list of output files.
    """
    suffix = os.path.splitext(file.filename or "")[1] or ".fna"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    return run_casfinder(tmp_path)


# ---------------------------
# Static frontend mount (ALWAYS LAST)
# ---------------------------

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
