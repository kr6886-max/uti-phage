import os
from Bio import SeqIO
import pandas as pd
from collections import Counter

K = 4

def gc_percent(seq):
    if not seq:
        return 0.0
    seq = seq.upper()
    gc = seq.count("G") + seq.count("C")
    return (gc / len(seq)) * 100.0

def kmer_freqs(seq, k):
    seq = seq.upper()
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
base_dir = "genomes"

for species in os.listdir(base_dir):
    species_dir = os.path.join(base_dir, species)
    if not os.path.isdir(species_dir):
        continue

    for root, _, files in os.walk(species_dir):
        for file in files:
            if file.endswith(".fna"):
                path = os.path.join(root, file)
                for record in SeqIO.parse(path, "fasta"):
                    seq = str(record.seq)
                    row = {
                        "species": species,
                        "fasta_record": record.id,
                        "genome_length": len(seq),
                        "gc_percent": gc_percent(seq),
                    }
                    row.update(kmer_freqs(seq, K))
                    rows.append(row)

df = pd.DataFrame(rows).fillna(0)

os.makedirs("data", exist_ok=True)
df.to_csv("data/bacteria_genome_features.csv", index=False)

print("DONE ✅")
print("Rows:", len(df))
