#!/usr/bin/env bash
set -euo pipefail

ROOT="/mnt/c/Users/Admin/OneDrive/Desktop/uti-phage"
CCF="$ROOT/tools/CRISPRCasFinder/CRISPRCasFinder.pl"
OUTDIR="$ROOT/ccf_out"
CACHEDIR="$ROOT/data/crispr_cache"

mkdir -p "$OUTDIR" "$CACHEDIR"

if [ ! -f "$CCF" ]; then
  echo "ERROR: CRISPRCasFinder.pl not found at $CCF"
  exit 1
fi

if [ ! -f "$ROOT/extract_spacers_ccf.py" ]; then
  echo "ERROR: extract_spacers_ccf.py not found at $ROOT/extract_spacers_ccf.py"
  exit 1
fi

echo "=== Running CRISPRCasFinder for all bacteria ==="
echo "Output:  $OUTDIR"
echo "Cache:   $CACHEDIR"
echo

while IFS= read -r b; do
  [ -z "$b" ] && continue
  folder="${b// /_}"

  in_fna=$(find "$ROOT/genomes/$folder" -name "*.fna" 2>/dev/null | head -n 1 || true)
  if [ -z "$in_fna" ]; then
    echo "[SKIP] $folder : genome .fna not found"
    echo
    continue
  fi

  # IMPORTANT: create output folder BEFORE logging
  mkdir -p "$OUTDIR/$folder"

  log="$OUTDIR/$folder/run.log"
  echo "[RUN ] $folder" | tee "$log"
  echo "      genome: $in_fna" | tee -a "$log"

  # Run CRISPRCasFinder (NO -cas)
  perl "$CCF" \
    -in "$in_fna" \
    -out "$OUTDIR/$folder" \
    -def General \
    >> "$log" 2>&1 || true

  # Extract spacers if result.json exists
  if [ -f "$OUTDIR/$folder/result.json" ]; then
    python3 "$ROOT/extract_spacers_ccf.py" \
      "$OUTDIR/$folder/result.json" \
      "$folder" \
      "$CACHEDIR" \
      >> "$log" 2>&1 || true
  else
    echo "[WARN] $folder : result.json not produced (see $log)" | tee -a "$log"
  fi

  # Spacer count
  if [ -f "$CACHEDIR/$folder.txt" ]; then
    n=$(wc -l < "$CACHEDIR/$folder.txt" | tr -d ' ')
    echo "      spacers: $n" | tee -a "$log"
  else
    echo "      spacers: (no cache file)" | tee -a "$log"
  fi

  echo
done < "$ROOT/bacteria_list.txt"

echo "=== DONE ==="
echo "Spacer cache files are in: $CACHEDIR"
