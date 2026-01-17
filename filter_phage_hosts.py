import pandas as pd

# Load Virus–Host DB
vh = pd.read_csv("external_data/virushostdb.tsv", sep="\t", low_memory=False)

# Normalize column names
vh.columns = [c.strip().lower().replace(" ", "_") for c in vh.columns]

# Load UTI bacteria list
with open("bacteria_list.txt") as f:
    uti_bacteria = [line.strip().lower() for line in f if line.strip()]

uti_set = set(uti_bacteria)

# Filter: viruses infecting UTI bacteria
vh_uti = vh[vh["host_name"].astype(str).str.lower().isin(uti_set)]

# Select useful columns
out = vh_uti[[
    "virus_name",
    "refseq_id",
    "host_name",
    "virus_lineage",
    "evidence"
]].drop_duplicates()

# Save result
out.to_csv("data/uti_phage_host_interactions.csv", index=False)

print("DONE ✅")
print("Total interactions:", len(out))
print("Unique phages:", out["virus_name"].nunique())
print("Unique bacteria:", out["host_name"].nunique())
