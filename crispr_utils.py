import os
from Bio import SeqIO

# --------- Loaders ---------

def load_phage_sequence_by_id(phage_id: str, phage_multi_fna: str):
    for rec in SeqIO.parse(phage_multi_fna, "fasta"):
        if rec.id == phage_id:
            return str(rec.seq).upper()
    return None

def load_spacers_from_cache(bacteria: str):
    """
    Loads real CRISPRCasFinder spacers from:
      data/crispr_cache/<bacteria>.txt

    Returns:
      - None if file missing
      - [] if file exists but empty
      - [spacers...] if present
    """
    path = os.path.join("data", "crispr_cache", f"{bacteria}.txt")
    if not os.path.exists(path):
        return None

    spacers = []
    with open(path, "r") as f:
        for line in f:
            s = line.strip().upper()
            if s:
                spacers.append(s)
    return spacers

# --------- Approx matching (mismatches allowed) ---------

def _hamming(a: str, b: str) -> int:
    return sum(1 for x, y in zip(a, b) if x != y)

def _approx_match_exists(spacer: str, phage_seq: str, max_mm: int = 2, seed_len: int = 12) -> bool:
    """
    Fast approximate match:
    - Find exact occurrences of a seed (prefix) in phage genome
    - Verify full spacer with <= max_mm mismatches (Hamming)
    """
    L = len(spacer)
    if L <= 0:
        return False

    if seed_len > L:
        seed_len = max(8, L // 2)

    seed = spacer[:seed_len]
    start = 0
    while True:
        pos = phage_seq.find(seed, start)
        if pos == -1:
            return False
        if pos + L <= len(phage_seq):
            window = phage_seq[pos:pos+L]
            if _hamming(spacer, window) <= max_mm:
                return True
        start = pos + 1

def crispr_match_count_from_spacers(spacers, phage_seq: str, max_mm: int = 2):
    """
    Returns (num_spacers, matches_found) allowing mismatches.
    """
    hits = 0
    for sp in spacers:
        if _approx_match_exists(sp, phage_seq, max_mm=max_mm, seed_len=12):
            hits += 1
    return len(spacers), hits
