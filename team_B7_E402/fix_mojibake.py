import sys
from pathlib import Path

RAW_DIR = Path(__file__).parent / "raw"
FILES_TO_FIX = [
    "bench_ca_nhom.py",
    "kiem_tra_corpus.py",
    "src_agent.py",
    "src_chunking.py",
    "src_store.py",
]

for name in FILES_TO_FIX:
    path = RAW_DIR / name
    text = path.read_text(encoding="utf-8")
    try:
        fixed = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        print(f"FAILED {name}: {e}")
        continue
    path.write_text(fixed, encoding="utf-8")
    print(f"OK {name}")
