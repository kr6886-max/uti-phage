from fastapi import UploadFile, File
import tempfile

from tools.casfinder import run_casfinder

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import os
import pandas as pd

from crispr_utils import (
    load_phage_sequence_by_id,
    load_spacers_from_cache,
    crispr_match_count_from_spacers,
)

app = FastAPI(title="UTI Bacteria → Best Phage Finder", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/api/casfinder")
async def casfinder_api(file: UploadFile = File(...)):
    # Save upload to a temp file
    suffix = os.path.splitext(file.filename or "")[1] or ".fna"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Run CasFinder pipeline
    result = run_casfinder(tmp_path)
    return result

# Serve UI
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/ui")
def ui():
    return FileResponse("frontend/index.html")

@app.get("/")
def home():
    return {"message": "UTI Best Phage Finder running", "docs": "/docs", "ui": "/ui"}

# Data
PRED_CSV = "data/bacteria_phage_top10.csv"
if not os.path.exists(PRED_CSV):
    raise RuntimeError(f"Missing {PRED_CSV}")

pred_df = pd.read_csv(PRED_CSV)

PHAGE_MULTI_FASTA = "phage_genomes/phages_200/ncbi_dataset/data/genomic.fna"

@app.get("/bacteria")
def list_bacteria():
    bacteria = sorted(pred_df["bacteria"].unique().tolist())
    return {"count": len(bacteria), "bacteria": bacteria}

@app.get("/predict")
def predict(bacteria: str = Query(...), topk: int = Query(10, ge=1, le=50)):
    sub = pred_df[pred_df["bacteria"] == bacteria].copy()
    if sub.empty:
        return {"error": f"No phage ranking available for bacteria='{bacteria}'"}

    sub = sub.sort_values("similarity", ascending=False).head(topk)

    results = []
    for i, row in enumerate(sub.itertuples(index=False), start=1):
        results.append({
            "rank": i,
            "phage_id": str(row.phage_id),
            "similarity": float(row.similarity),
        })

    return {"bacteria": bacteria, "topk": len(results), "results": results}

@app.get("/crispr_check_batch")
def crispr_check_batch(
    bacteria: str,
    phage_ids: str,
    max_mm: int = Query(2, ge=0, le=6),
):
    """
    Uses real CRISPRCasFinder spacers from data/crispr_cache/<bacteria>.txt

    Returns overall status:
      - ok (computed)
      - no_cache (file missing)
      - no_spacers (empty file)
      - missing_phage_fasta (server file missing)
    """
    spacers = load_spacers_from_cache(bacteria)

    if spacers is None:
        return {"ok": True, "status": "no_cache", "bacteria": bacteria, "max_mm": max_mm, "results": {}}

    if len(spacers) == 0:
        return {"ok": True, "status": "no_spacers", "bacteria": bacteria, "max_mm": max_mm, "results": {}}

    if not os.path.exists(PHAGE_MULTI_FASTA):
        return {
            "ok": False,
            "status": "missing_phage_fasta",
            "error": "Phage multi-FASTA not found",
            "expected_path": PHAGE_MULTI_FASTA,
        }

    ids = [x.strip() for x in phage_ids.split(",") if x.strip()]
    out = {}

    for pid in ids:
        phage_seq = load_phage_sequence_by_id(pid, PHAGE_MULTI_FASTA)
        if not phage_seq:
            out[pid] = {"ok": False, "error": "phage_id not found in phage multi-FASTA"}
            continue

        n_sp, hits = crispr_match_count_from_spacers(spacers, phage_seq, max_mm=max_mm)
        out[pid] = {
            "ok": True,
            "spacers_found": n_sp,
            "matches_found": hits,
            "match": hits > 0,
        }

    return {"ok": True, "status": "ok", "bacteria": bacteria, "max_mm": max_mm, "results": out}
