import os
import shutil
import subprocess
import uuid
from pathlib import Path

BASE_DIR = Path("/tmp/casfinder_jobs")


def run_cmd(cmd: list[str]) -> tuple[str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(cmd)
            + "\n\nSTDOUT:\n"
            + (p.stdout or "")
            + "\n\nSTDERR:\n"
            + (p.stderr or "")
        )
    return p.stdout, p.stderr


def run_casfinder(fasta_path: str) -> dict:
    job_id = str(uuid.uuid4())
    job_dir = BASE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    genome = job_dir / "genome.fna"
    shutil.copyfile(fasta_path, genome)

    proteins = job_dir / "proteins.faa"

    # 1) Prodigal: genome -> proteins
    run_cmd([
        "prodigal",
        "-i", str(genome),
        "-a", str(proteins),
        "-p", "single",
    ])

    # 2) MacSyFinder: CasFinder models
    out_dir = job_dir / "macsyfinder_out"
    out_dir.mkdir(exist_ok=True)

    # Preferred models dir (what we aimed to create in Dockerfile)
    preferred_models_dir = os.environ.get("MACSY_MODELS_DIR", "/usr/local/share/macsyfinder/models")
    Path(preferred_models_dir).mkdir(parents=True, exist_ok=True)  # prevents FileNotFoundError

    # We will try these model directories in order:
    # 1) preferred_models_dir (copied models)
    # 2) /opt/casfinder-models (git clone location)
    model_dirs_to_try = [
        preferred_models_dir,
        "/opt/casfinder-models",
    ]

    # Model name sometimes appears as CasFinder or casfinder depending on install
    model_names_to_try = ["CasFinder", "casfinder"]

    last_error = None
    for mdir in model_dirs_to_try:
        for mname in model_names_to_try:
            try:
                run_cmd([
                    "macsyfinder",
                    "--models", mname,
                    "--models-dir", mdir,
                    "--sequence-db", str(proteins),
                    "--out-dir", str(out_dir),
                    "--db-type", "gembase",
                ])
                # success -> return outputs
                files = [str(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file()]
                return {"job_id": job_id, "output_files": files, "models_dir_used": mdir, "model_used": mname}
            except Exception as e:
                last_error = e

    # If all attempts failed, raise the last error (shows real message in Swagger because app.py uses HTTPException(detail=...))
    raise RuntimeError(f"MacSyFinder failed for all model options. Last error:\n{last_error}")

