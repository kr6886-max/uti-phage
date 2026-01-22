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

    # 2) IMPORTANT: always use a NEW empty output folder
    out_dir = job_dir / f"macsy_out_{uuid.uuid4().hex}"
    out_dir.mkdir(parents=True, exist_ok=False)

    # Models dir (use copied dir if present, otherwise fallback to clone)
    preferred_models_dir = os.environ.get("MACSY_MODELS_DIR", "/usr/local/share/macsyfinder/models")
    if Path(preferred_models_dir).exists() and any(Path(preferred_models_dir).iterdir()):
        models_dir = preferred_models_dir
    else:
        models_dir = "/opt/casfinder-models"

    # Try common model names
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

