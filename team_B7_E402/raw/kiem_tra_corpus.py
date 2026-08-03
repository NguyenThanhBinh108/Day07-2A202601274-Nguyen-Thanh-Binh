"""
Kiá»m tra corpus cá»§a NHÃM theo checklist docs/DATA_COLLECTION.md má»¥c 6 + yÃªu cáº§u riÃªng K4.

CÃ´ng cá»¥ dÃ¹ng chung cho cáº£ nhÃ³m â cháº¡y trÆ°á»c khi cháº¡y benchmark Äá» cháº¯c cháº¯n khÃ´ng máº¥t
Äiá»m oan á» má»¥c "Cháº¥t lÆ°á»£ng Bá» TÃ i liá»u" (10 Äiá»m).

Cháº¡y:
    python scripts/kiem_tra_corpus.py                      # máº·c Äá»nh data/k4_ecommerce
    python scripts/kiem_tra_corpus.py <thu-muc-khac>

MÃ£ thoÃ¡t: 0 náº¿u khÃ´ng cÃ²n lá»i cháº·n, 1 náº¿u cÃ²n.
"""
from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ingest import parse_front_matter  # noqa: E402

BAT_BUOC = ["doc_id", "title", "source_url", "retrieved_at", "document_version", "customer_role"]
VAI_TRO_HOP_LE = {"buyer", "seller", "both"}
NGAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_GIA = re.compile(r"example\.(com|org|edu)", re.I)
DAU_HIEU_TEMPLATE = ["template máº«u", "NhÃ³m pháº£i bá» sung", "NhÃ³m cáº§n bá» sung", "dá»¯ liá»u khá»i Äá»ng"]

loi: list[str] = []
canh_bao: list[str] = []


def kiem_tra(dieu_kien: bool, thong_diep: str, chan: bool = True) -> None:
    if not dieu_kien:
        (loi if chan else canh_bao).append(thong_diep)


def main() -> int:
    thu_muc = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "data" / "k4_ecommerce"
    if not thu_muc.is_absolute():
        thu_muc = REPO_ROOT / thu_muc
    print(f"Corpus: {thu_muc}\n")

    if not thu_muc.exists():
        print(f"Lá»I: khÃ´ng tÃ¬m tháº¥y thÆ° má»¥c {thu_muc}")
        return 1

    files = sorted(list(thu_muc.glob("*.md")) + list(thu_muc.glob("*.txt")))
    print(f"{'File':<42}{'customer_role':<16}{'category':<18}{'kÃ½ tá»±':<8}Thiáº¿u metadata")
    print("-" * 104)

    doc_ids: dict[str, str] = {}
    vai_tro: dict[str, int] = {}

    for path in files:
        meta, body = parse_front_matter(io.open(path, encoding="utf-8").read())
        thieu = [khoa for khoa in BAT_BUOC if not str(meta.get(khoa, "")).strip()]
        role = str(meta.get("customer_role", "â"))
        vai_tro[role] = vai_tro.get(role, 0) + 1
        print(f"{path.name:<42}{role:<16}{str(meta.get('category', 'â')):<18}{len(body):<8}{','.join(thieu) or 'Äá»§'}")

        ten = path.name
        kiem_tra(not thieu, f"{ten}: thiáº¿u metadata báº¯t buá»c {thieu}")

        doc_id = str(meta.get("doc_id", "")).strip()
        if doc_id:
            kiem_tra(doc_id not in doc_ids, f"{ten}: doc_id '{doc_id}' trÃ¹ng vá»i {doc_ids.get(doc_id)}")
            doc_ids[doc_id] = ten
            # CHECKPOINT 2 cá»§a Äá» bÃ i coi doc_id != tÃªn file lÃ  THIáº¾U METADATA -> Äá» má»©c cháº·n.
            kiem_tra(doc_id == path.stem, f"{ten}: doc_id '{doc_id}' pháº£i trÃ¹ng tÃªn file '{path.stem}' (CHECKPOINT 2)")

        kiem_tra(role in VAI_TRO_HOP_LE, f"{ten}: customer_role='{role}' khÃ´ng thuá»c {sorted(VAI_TRO_HOP_LE)}")
        kiem_tra(NGAY.match(str(meta.get("retrieved_at", ""))) is not None,
                 f"{ten}: retrieved_at pháº£i dáº¡ng YYYY-MM-DD, Äang lÃ  '{meta.get('retrieved_at')}'")
        kiem_tra(not URL_GIA.search(str(meta.get("source_url", ""))),
                 f"{ten}: source_url cÃ²n lÃ  URL máº«u example.com â pháº£i thay báº±ng nguá»n tháº­t")
        kiem_tra(len([k for k in meta if k not in BAT_BUOC and k not in {"source", "chunk_index"}]) >= 1,
                 f"{ten}: cáº§n Ã­t nháº¥t 1 trÆ°á»ng metadata há»¯u Ã­ch ngoÃ i nhÃ³m báº¯t buá»c (category/language/...)", chan=False)
        kiem_tra(len(body.strip()) >= 200, f"{ten}: ná»i dung quÃ¡ ngáº¯n ({len(body)} kÃ½ tá»±), khÃ³ táº¡o gold answer", chan=False)

        dau_hieu = [d for d in DAU_HIEU_TEMPLATE if d in body]
        kiem_tra(not dau_hieu, f"{ten}: ná»i dung cÃ²n chá»¯ template {dau_hieu} â chÆ°a thay báº±ng nguá»n tháº­t")

    print(f"\nPhÃ¢n bá» customer_role: {vai_tro}")

    # --- Kiá»m tra cáº¥p corpus ---
    kiem_tra(5 <= len(files) <= 10, f"Cáº§n 5-10 tÃ i liá»u, Äang cÃ³ {len(files)}")
    kiem_tra(vai_tro.get("seller", 0) + vai_tro.get("both", 0) >= 1,
             "K4: pháº£i cÃ³ Ã­t nháº¥t 1 tÃ i liá»u customer_role=seller (hoáº·c both) cho cÃ¢u há»i lá»c metadata")
    kiem_tra(vai_tro.get("buyer", 0) + vai_tro.get("both", 0) >= 1,
             "K4: pháº£i cÃ³ Ã­t nháº¥t 1 tÃ i liá»u customer_role=buyer (hoáº·c both)")
    kiem_tra(len([v for v in vai_tro if v in VAI_TRO_HOP_LE]) >= 2,
             f"customer_role pháº£i cÃ³ Ã­t nháº¥t 2 giÃ¡ trá» khÃ¡c nhau, Äang chá» cÃ³ {sorted(vai_tro)}")

    csv_path = thu_muc / "sources.csv"
    if not csv_path.exists():
        loi.append("Thiáº¿u sources.csv")
    else:
        with io.open(csv_path, encoding="utf-8", newline="") as fh:
            dong = list(csv.DictReader(fh))
        id_csv = {str(r.get("doc_id", "")).strip() for r in dong}
        thieu_csv = set(doc_ids) - id_csv
        thua_csv = id_csv - set(doc_ids)
        kiem_tra(not thieu_csv, f"sources.csv thiáº¿u dÃ²ng cho doc_id: {sorted(thieu_csv)}")
        kiem_tra(not thua_csv, f"sources.csv cÃ³ doc_id khÃ´ng tá»n táº¡i file: {sorted(thua_csv)}")
        kiem_tra(all(str(r.get("license_or_permission", "")).strip() for r in dong),
                 "sources.csv: cÃ³ dÃ²ng thiáº¿u license_or_permission", chan=False)

    print()
    for c in canh_bao:
        print(f"  [cáº£nh bÃ¡o] {c}")
    for e in loi:
        print(f"  [Lá»I]      {e}")

    if loi:
        print(f"\nâ CÃN {len(loi)} Lá»I CHáº¶N â sá»­a xong má»i nÃªn cháº¡y benchmark.")
        return 1
    print(f"\nâ CORPUS Äáº T CHECKLIST ({len(canh_bao)} cáº£nh bÃ¡o khÃ´ng cháº·n).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
