from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime

app = FastAPI(
    title="UTI Phage Finder (Demo Mode)",
    version="1.0.0",
    description="Mock backend for CasFinder, Lifestyle, and AMR tools"
)

# ---------------------------
# CORS (allow everything for demo)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Home
# ---------------------------
@app.get("/")
def home():
    return {
        "status": "ok",
        "mode": "mock",
        "message": "UTI Phage Finder backend running (DEMO MODE)",
        "docs": "/docs"
    }

# ---------------------------
# Fake CasFinder
# ---------------------------
@app.post("/api/casfinder")
async def casfinder_api(file: UploadFile = File(...)):
    return {
        "mode": "mock",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_filename": file.filename,
        "job_id": "demo-casfinder-001",
        "predicted_systems": [
            {"type": "Type I-E", "confidence": 0.87},
            {"type": "Type I-F", "confidence": 0.62}
        ],
        "cas_genes": [
            "cas1", "cas2", "cas3", "cse1", "cse2"
        ],
        "summary": "CRISPR-Cas systems detected (demo output)",
        "output_files": [
            "casfinder_summary.json",
            "systems.tsv",
            "macsyfinder.report"
        ]
    }

# ---------------------------
# Fake Lifestyle Prediction
# ---------------------------
@app.post("/api/lifestyle")
async def lifestyle_api(file: UploadFile = File(...)):
    return {
        "mode": "mock",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_filename": file.filename,
        "job_id": "demo-lifestyle-001",
        "prediction": "Lytic",
        "confidence": 0.91,
        "notes": [
            "No integrase detected",
            "No repressor genes found"
        ]
    }

# ---------------------------
# Fake AMR Screening
# ---------------------------
@app.post("/api/amr_screen")
async def amr_screen_api(file: UploadFile = File(...)):
    return {
        "mode": "mock",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_filename": file.filename,
        "job_id": "demo-amr-001",
        "amr_genes_found": [],
        "summary": "No AMR genes detected (demo result)"
    }

# ---------------------------
# UI
# ---------------------------
@app.get("/ui")
def ui():
    return FileResponse("frontend/index.html")

# ---------------------------
# Static frontend (optional)
# ---------------------------
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

