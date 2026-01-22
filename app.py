"""
Clean app.py for your UTI-phage FastAPI service (includes CasFinder endpoint)

✅ Keeps your existing endpoints:
- GET /
- GET /ui
- GET /bacteria
- GET /predict
- GET /crispr_check_batch

✅ Adds:
- POST /api/casfinder (file upload)

✅ IMPORTANT:
- This file assumes these exist in your repo:
  - crispr_utils.py  (with the 3 functions imported below)
  - tools/casfinder.py (with run_casfinder)
  - frontend/index.html (for /ui)
  - bacteria_list.txt (for /bacteria)

If your old /predict or /crispr_check_batch had custom logic, paste that logic
inside the placeholders in those functions.
"""

from __future__ import annotations

import os
import tempfile
from typing import List

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ---- your existing utilities (already in your repo) ----
from crispr_utils import (  # type: ignore
    crispr_match_count_from_spacers,
    load_phage_sequence_by_id,
    load_spacers_from_cache,
)

# ---- CasFinder runner ----
from tools.casfinder import run_casfinder  # type: ignore

app = FastAPI(title="UTI Bacteria → Best Phage Finder", version="1.0.0")

# CORS (keep permissive for your demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# BASIC ROUTES
# -------------------------

@app.get("/")
def home():
    return {"status": "ok", "message": "UTI-phage API is running"}


@app.get("/ui")
def ui():
    # UI entrypoint
    return FileResponse("frontend/index.html")


# -------------------------
# EXISTING ENDPOINTS
# -------------------------

@app.get("/bacteria")
def list_bacteria():
    """
    Reads bacteria_list.txt and returns a list.
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
    PLACEHOLDER (clean).
    If your old app.py had real prediction logic, paste it here.
    """
    # TODO: paste your existing prediction logic here
    return {"bacteria": bacteria, "top_k": top_k, "results": []}


@app.get("/crispr_check_batch")
def crispr_check_batch(
    bacteria: str = Query(..., description="Bacteria name"),
    phage_ids: str = Query(..., description="Comma-separated phage IDs"),
):
    """
    PLACEHOLDER (clean).
    If your old app.py had real CRISPR batch logic, paste it here.

    Below is a simple example using your crispr_utils helpers.
    """
    ids: List[str] = [x.strip() for x in phage_ids.split(",") if x.strip()]

    # Example logic (safe + minimal):
    # - loads spacers for bacteria from cache
    # - counts matches per phage
    try:
        spacers = load_spacers_from_cache(bacteria)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load spacers: {e}")

    results = []
    for pid in ids:
        try:
            phage_seq = load_phage_sequence_by_id(pid)
            matches = crispr_match_count_from_spacers(spacers, phage_seq)
            results.append({"phage_id": pid, "matches": matches})
        except Exception as e:
            results.append({"phage_id": pid, "error": str(e)})

    return {"bacteria": bacteria, "results": results}


# -------------------------
# ✅ CASFINDER ENDPOINT
# -------------------------

@app.post("/api/casfinder")
async def casfinder_api(file: UploadFile = File(...)):
    """
    Upload a bacterial genome FASTA (.fna/.fa/.fasta).
    Runs Prodigal -> MacSyFinder (CasFinder models).
    Returns job_id + list of output files.
    """
    suffix = os.path.splitext(file.filename or "")[1] or ".fna"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        return run_casfinder(tmp_path)
    except Exception as e:
        # show real error in Swagger instead of just "Internal Server Error"
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# STATIC FILES (ALWAYS LAST)
# -------------------------

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
