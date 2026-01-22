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
    # --------- Always start clean ----------
    job_id = str(uuid.uuid4())
    job_dir = BASE_DIR / job_id

    # If somehow exists, delete it (prevents the “already exists and not empty” error)
    if job_dir.exists():
        shutil.rmtree(job_dir)

    job_dir.mkdir(parents=True, exist_ok=False)

    # --------- Copy input ----------
    genome = job_dir / "genome.fna"
    shutil.copyfile(fasta_path, genome)

    proteins = job_dir / "proteins.faa"

    # --------- Prodigal ----------
    run_cmd([
        "prodigal",
        "-i", str(genome),
        "-a", str(proteins),
        "-p", "single",
    ])

    # --------- MacSyFinder output dir MUST be brand new ----------
    out_dir = job_dir / "macsy_out"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)

    # --------- Models dir selection ----------
    preferred_models_dir = os.environ.get("MACSY_MODELS_DIR", "/usr/local/share/macsyfinder/models")
    if Path(preferred_models_dir).exists() and any(Path(preferred_models_dir).iterdir()):
        models_dir = preferred_models_dir
    else:
        models_dir = "/opt/casfinder-models"

    # --------- Run MacSyFinder (try both model names) ----------
   Toggle = False
    last_error = None
    for model_name in ("CasFinder", "casfinder"):
        try:
            run_cmd([
                "macsyfinder",
                "--models", model_name,
                "--models-dir", models_dir,
                "--sequence-db", str(proteins),
                "--out-dir", str(out_dir),
                "--db-type", "gembase",
            ])
            files = [str(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file()]
            return {
                "job_id": job_id,
                "output_files": files,
                "models_dir_used": models_dir,
                "model_used": model_name,
            }
        except Exception as e:
            last_error = e

    raise RuntimeError(f"MacSyFinder failed. Last error:\n{last_error}")


