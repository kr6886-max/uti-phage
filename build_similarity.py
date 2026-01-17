import pandas as pd
import numpy as np

# ---------- Load data ----------
bac_path = "data/bacteria_genome_features.csv"
phage_path = "data/phage_genome_features.csv"
links_path = "data/uti_phage_host_interactions.csv"

bdf = pd.read_csv(bac_path)
pdf = pd.read_csv(phage_path)
ldf = pd.read_csv(links_path)

# Normalize column names for safety
bdf.columns = [c.strip().lower() for c in bdf.columns]
pdf.columns = [c.strip().lower() for c in pdf.columns]
ldf.columns = [c.strip().lower() for c in ldf.columns]

# Expected columns
# bacteria features: species, genome_length, gc_percent, kmer_*
# phage features: phage_id, genome_length, gc_percent, kmer_*
# links: virus_name, refseq_id, host_name, virus_lineage, evidence

# ---------- Prepare feature matrices ----------
# Use only kmer_ columns (most informative for sequence similarity)
b_kmer_cols = [c for c in bdf.columns if c.startswith("kmer_")]
p_kmer_cols = [c for c in pdf.columns if c.startswith("kmer_")]

# Use common k-mers between both tables
common = sorted(set(b_kmer_cols).intersection(set(p_kmer_cols)))
if len(common) == 0:
    raise SystemExit("No common kmer_ columns found between bacteria and phage feature files.")

# Build numpy matrices
B = bdf[common].to_numpy(dtype=np.float64)
P = pdf[common].to_numpy(dtype=np.float64)

# Cosine similarity helper
def cosine_sim_matrix(A, B):
    # returns (nA x nB)
    A_norm = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-12)
    B_norm = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-12)
    return A_norm @ B_norm.T

# ---------- Compute similarity ----------
sim = cosine_sim_matrix(B, P)

# Map indices to names
bacteria_names = bdf["species"].astype(str).tolist()
phage_ids = pdf["phage_id"].astype(str).tolist()

# ---------- Build lookup: host_name -> candidate phage names ----------
# VirusHostDB gives virus_name and host_name. We'll match candidate phages by virus_name appearing in phage_id.
# (phage_id is FASTA record id; often contains accession/name text)
host_to_viruses = (
    ldf.groupby("host_name")["virus_name"]
    .apply(lambda s: sorted(set(s.dropna().astype(str))))
    .to_dict()
)

# ---------- For each bacterium, rank phages ----------
rows = []
TOPK = 10

for i, host in enumerate(bacteria_names):
    # candidate virus names known to infect this bacterium
    candidates = host_to_viruses.get(host.replace("_", " "), [])  # handle folder-style names
    if not candidates:
        # try exact match as stored in links file
        candidates = host_to_viruses.get(host, [])

    # similarity scores for this bacterium vs all phages
    scores = sim[i, :]

    # If we have known candidate virus names, filter phages that match any candidate string
    if candidates:
        mask = np.zeros(len(phage_ids), dtype=bool)
        for v in candidates:
            v_low = v.lower()
            mask |= np.array([v_low in pid.lower() for pid in phage_ids], dtype=bool)

        # If mask is empty (no matches), fall back to all phages
        if mask.any():
            idxs = np.where(mask)[0]
        else:
            idxs = np.arange(len(phage_ids))
    else:
        idxs = np.arange(len(phage_ids))

    # rank
    top = idxs[np.argsort(scores[idxs])[::-1][:TOPK]]

    for rank, j in enumerate(top, start=1):
        rows.append({
            "bacteria": host,
            "rank": rank,
            "phage_id": phage_ids[j],
            "similarity": float(scores[j])
        })

out = pd.DataFrame(rows)
out.to_csv("data/bacteria_phage_top10.csv", index=False)

print("DONE ✅")
print("Saved: data/bacteria_phage_top10.csv")
print("Example (first 15 rows):")
print(out.head(15).to_string(index=False))
