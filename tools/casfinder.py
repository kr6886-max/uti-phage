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

    # 2) MacSyFinder output folder MUST be empty/new
    out_dir = job_dir / f"macsyfinder_out_{uuid.uuid4().hex}"
    out_dir.mkdir(parents=True, exist_ok=False)  # must be new/empty

    # Models directory (try preferred, else fallback to clone)
    preferred_models_dir = os.environ.get("MACSY_MODELS_DIR", "/usr/local/share/macsyfinder/models")
    preferred = Path(preferred_models_dir)
    if preferred.exists() and any(preferred.iterdir()):
        models_dir = str(preferred)
    else:
        models_dir = "/opt/casfinder-models"

    # Try common model names
    model_names = ["CasFinder", "casfinder"]

    last_error = None
    for model_name in model_names:
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
                "output_dir": str(out_dir),
                "output_files": files,
                "models_dir_used": models_dir,
                "model_used": model_name,
            }
        except Exception as e:
            last_error = e

    raise RuntimeError(f"MacSyFinder failed. Last error:\n{last_error}")
