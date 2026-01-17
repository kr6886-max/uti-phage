import os
from Bio import SeqIO
import pandas as pd
from collections import Counter

K = 4

def gc_percent(seq):
    seq = seq.upper()
    if len(seq) == 0:
        return 0.0
    return (seq.count("G") + seq.count("C")) / len(seq) * 100

def kmer_freqs(seq, k):
    counts = Counter()
    total = 0
    for i in range(len(seq) - k + 1):
        kmer = seq[i:i+k]
        if "N" in kmer:
            continue
        counts[kmer] += 1
        total += 1
    if total == 0:
        return {}
    return {f"kmer_{kmer}": c / total for kmer, c in counts.items()}

rows = []

fasta_path = "phage_genomes/phages_200/ncbi_dataset/data/genomic.fna"

for record in SeqIO.parse(fasta_path, "fasta"):
    seq = str(record.seq)
    row = {
        "phage_id": record.id,
        "genome_length": len(seq),
        "gc_percent": gc_percent(seq),
    }
    row.update(kmer_freqs(seq, K))
    rows.append(row)

df = pd.DataFrame(rows).fillna(0)

os.makedirs("data", exist_ok=True)
df.to_csv("data/phage_genome_features.csv", index=False)

print("DONE ✅")
print("Phage genomes processed:", len(df))
