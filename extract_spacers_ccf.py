import json
import re
import sys
from pathlib import Path

DNA = re.compile(r"^[ACGT]+$", re.I)

def walk(obj, spacers):
    if isinstance(obj, dict):
        # capture spacer entries
        if obj.get("Type") == "Spacer" and isinstance(obj.get("Sequence"), str):
            s = obj["Sequence"].strip().upper()
            if 20 <= len(s) <= 80 and DNA.match(s):
                spacers.add(s)
        # recurse
        for v in obj.values():
            walk(v, spacers)
    elif isinstance(obj, list):
        for it in obj:
            walk(it, spacers)

def main():
    if len(sys.argv) != 4:
        print("Usage: python extract_spacers_ccf.py <result.json> <bacteria_name> <out_dir>")
        sys.exit(1)

    result_json = Path(sys.argv[1])
    bacteria = sys.argv[2]
    out_dir = Path(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(result_json.read_text(encoding="utf-8"))
    spacers = set()
    walk(data, spacers)

    out_path = out_dir / f"{bacteria}.txt"
    out_path.write_text("\n".join(sorted(spacers)) + ("\n" if spacers else ""), encoding="utf-8")

    print(f"OK: {bacteria} spacers={len(spacers)} -> {out_path}")

if __name__ == "__main__":
    main()
