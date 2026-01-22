import subprocess
import uuid
import shutil
from pathlib import Path
import os

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

    # 2) MacSyFinder: run CasFinder models
    out_dir = job_dir / "macsyfinder_out"
    out_dir.mkdir(exist_ok=True)

    models_dir = os.environ.get("MACSY_MODELS_DIR", "/usr/local/share/macsyfinder/models")

    # We set models_dir in Dockerfile and copied CasFinder models there.
    # Use model NAME, not path.
    run_cmd([
        "macsyfinder",
        "--models", "CasFinder",
        "--models-dir", models_dir,
        "--sequence-db", str(proteins),
        "--out-dir", str(out_dir),
        "--db-type", "gembase",
    ])

    files = [str(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file()]
    return {"job_id": job_id, "output_files": files}

