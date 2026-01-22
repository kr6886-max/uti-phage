import subprocess
import uuid
import shutil
from pathlib import Path


BASE_DIR = Path("/tmp/casfinder_jobs")


def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(cmd)
            + "\n\nSTDERR:\n"
            + result.stderr
            + "\n\nSTDOUT:\n"
            + result.stdout
        )


def run_casfinder(fasta_path: str):
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

    # 2) MacSyFinder CasFinder (NO "run" subcommand)
    out_dir = job_dir / "macsyfinder_out"
    out_dir.mkdir(exist_ok=True)

    run_cmd([
        "macsyfinder",
        "--models", "/opt/casfinder-models",
        "--sequence-db", str(proteins),
        "--out-dir", str(out_dir),
        "--db-type", "gembase",
    ])

    files = [str(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file()]
    return {"job_id": job_id, "output_files": files}
