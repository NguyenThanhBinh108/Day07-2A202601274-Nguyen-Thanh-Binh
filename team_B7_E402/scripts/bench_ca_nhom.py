"""
Cháº¡y 5 benchmark query cá»§a nhÃ³m trÃªn `src/` cá»§a Tá»ªNG thÃ nh viÃªn â dá»¯ liá»u cho
báº£ng so sÃ¡nh á» REPORT_NHOM.md má»¥c 2.

Ba biáº¿n giá»¯ NGUYÃN cho má»i ngÆ°á»i (Äiá»u kiá»n so sÃ¡nh cÃ´ng báº±ng):
    corpus   = data/k4_ecommerce   (10 tÃ i liá»u dÃ¹ng chung)
    query    = 5 cÃ¢u ÄÃ£ khoÃ¡ trong bench.py
    embedder = EMBEDDING_PROVIDER=local
Chá» khÃ¡c ÄÃºng má»t biáº¿n: chiáº¿n lÆ°á»£c chunking.

Script nÃ y KHÃNG chá»n há» chiáº¿n lÆ°á»£c â nÃ³ chá» cháº¡y cáº¥u hÃ¬nh ghi trong PHAN_CONG
Äá» nhÃ³m cÃ³ sá» liá»u Äá»i chiáº¿u. Má»i thÃ nh viÃªn tá»± xÃ¡c nháº­n hoáº·c Äá»i chiáº¿n lÆ°á»£c
cá»§a mÃ¬nh rá»i cháº¡y láº¡i.

Cháº¡y:
    $env:EMBEDDING_PROVIDER="local"; python scripts/bench_ca_nhom.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import re  # noqa: E402

from bench import BENCHMARK, DATA_DIR, _chuan_hoa, _tu  # noqa: E402
from ingest import chunk_document, load_documents  # noqa: E402
from main import _select_embedder  # noqa: E402

# Má»i thÃ nh viÃªn dá»±ng prompt theo format riÃªng (tiáº¿ng Viá»t / tiáº¿ng Anh, nhÃ£n khÃ¡c nhau).
# Stub LLM pháº£i nháº­n diá»n ÄÆ°á»£c Má»I format, náº¿u khÃ´ng cá»t "agent tráº£ lá»i ÄÃºng" sáº½ Äo
# Äá» khá»p format thay vÃ¬ cháº¥t lÆ°á»£ng truy xuáº¥t â tá»©c so sÃ¡nh sai hoÃ n toÃ n.
NHAN_NGU_CANH = ["NGá»® Cáº¢NH:", "Ngá»¯ cáº£nh:", "Ngu canh:", "CONTEXT:", "Context:"]
NHAN_CAU_HOI = ["CÃU Há»I:", "CÃ¢u há»i:", "Cau hoi:", "QUESTION:", "Question:"]
NHAN_TRA_LOI = ["TRáº¢ Lá»I:", "Tráº£ lá»i:", "ANSWER:", "Answer:"]


def _cat_sau(text: str, nhan: list[str]) -> tuple[str, bool]:
    for n in nhan:
        if n in text:
            return text.rsplit(n, 1)[1], True
    return text, False


def _cat_truoc(text: str, nhan: list[str]) -> str:
    for n in nhan:
        if n in text:
            return text.split(n, 1)[0]
    return text


def llm_trich_xuat_chung(prompt: str) -> str:
    """Báº£n LLM trÃ­ch xuáº¥t KHÃNG phá»¥ thuá»c format prompt cá»§a tá»«ng thÃ nh viÃªn.

    Äiá»m má»i cÃ¢u = sá» tá»« trÃ¹ng cÃ¢u há»i Ã (1/thá»© háº¡ng Äoáº¡n). Náº¿u prompt khÃ´ng ÄÃ¡nh
    sá» Äoáº¡n `[n]` thÃ¬ dÃ¹ng thá»© tá»± xuáº¥t hiá»n lÃ m thá»© háº¡ng.
    """
    sau_ngu_canh, co_ngu_canh = _cat_sau(prompt, NHAN_NGU_CANH)
    ngu_canh = _cat_truoc(sau_ngu_canh, NHAN_CAU_HOI).strip() if co_ngu_canh else ""
    cau_hoi, co_cau_hoi = _cat_sau(prompt, NHAN_CAU_HOI)
    cau_hoi = _cat_truoc(cau_hoi, NHAN_TRA_LOI).strip() if co_cau_hoi else ""
    if not ngu_canh or not cau_hoi:
        return "KhÃ´ng Äá»c ÄÆ°á»£c ngá»¯ cáº£nh hoáº·c cÃ¢u há»i tá»« prompt."

    tu_hoi = _tu(cau_hoi)
    best, best_block, best_score, best_trung = "", 0, -1.0, 0
    block, tu_dong_block = 0, 0
    for line in ngu_canh.splitlines():
        m = re.match(r"^\s*\[(\d+)\]", line)
        if m:
            block = int(m.group(1))
            continue
        if not line.strip():
            continue
        if block == 0:  # prompt khÃ´ng ÄÃ¡nh sá» -> láº¥y thá»© tá»± dÃ²ng lÃ m thá»© háº¡ng
            tu_dong_block += 1
        hang = block or tu_dong_block
        trong_so = 1.0 / hang if hang else 1.0
        for cau in re.split(r"(?<=[.!?])\s+", line):
            cau = cau.strip()
            if len(cau) < 15:
                continue
            trung = len(tu_hoi & _tu(cau))
            if trung * trong_so > best_score:
                best, best_block, best_score, best_trung = cau, hang, trung * trong_so, trung
    if best_trung <= 0:
        return "Ngá»¯ cáº£nh truy xuáº¥t ÄÆ°á»£c khÃ´ng chá»©a thÃ´ng tin tráº£ lá»i cÃ¢u há»i nÃ y."
    return f"{best} [{best_block}]"

# (tÃªn hiá»n thá», thÆ° má»¥c, tÃªn chunker, tham sá») â chiáº¿n lÆ°á»£c PHáº¢I khÃ¡c nhau giá»¯a cÃ¡c thÃ nh viÃªn.
PHAN_CONG = [
    ("Nguyá»n Thanh BÃ¬nh", "Nguyen-Thanh-Binh-2A202601274", "ClauseChunker", dict(max_sentences_per_clause=1)),
    ("Tráº§n ChÃ­ VÅ©", "Tran-Chi-Vu-2A202601044", "RecursiveChunker", dict(chunk_size=400)),
    ("Trá»nh Háº£i ÄÄng", "Trinh-Hai-Dang-2A202601602", "FixedSizeChunker", dict(chunk_size=500, overlap=50)),
    ("Äá» VÄn Linh", "Do-Van-Linh-2A202601190", "SentenceChunker", dict(max_sentences_per_chunk=3)),
    ("Äá» Thu Liá»u", "Do-Thu-Lieu-2A202601898", "FixedSizeChunker", dict(chunk_size=250, overlap=100)),
]


def nap_src(thu_muc: str):
    """Náº¡p gÃ³i src cá»§a má»t thÃ nh viÃªn (má»i ngÆ°á»i má»t implementation riÃªng)."""
    for ten in [m for m in list(sys.modules) if m == "src" or m.startswith("src.")]:
        del sys.modules[ten]
    sys.path.insert(0, str(REPO_ROOT / thu_muc))
    try:
        return importlib.import_module("src")
    finally:
        sys.path.pop(0)


def chay(ten: str, thu_muc: str, ten_chunker: str, tham_so: dict, embedder) -> dict:
    src = nap_src(thu_muc)
    if not hasattr(src, ten_chunker):
        return {"ten": ten, "loi": f"src/ khÃ´ng cÃ³ {ten_chunker}"}

    # KHÃNG dÃ¹ng ingest.build_knowledge_base: hÃ m ÄÃ³ gáº¯n cá»©ng EmbeddingStore cá»§a src á»
    # gá»c repo, nÃªn má»i thÃ nh viÃªn sáº½ cÃ¹ng cháº¡y store cá»§a má»t ngÆ°á»i. á» ÄÃ¢y dá»±ng store
    # báº±ng ÄÃNG lá»p EmbeddingStore cá»§a tá»«ng thÃ nh viÃªn; chá» tÃ¡i dÃ¹ng hai hÃ m thuáº§n cá»§a
    # ingest lÃ  load_documents vÃ  chunk_document (khÃ´ng phá»¥ thuá»c store).
    chunker = getattr(src, ten_chunker)(**tham_so)
    chunk_docs = []
    for doc in load_documents(DATA_DIR):
        for c in chunk_document(doc, chunker):
            chunk_docs.append(src.Document(id=c.id, content=c.content, metadata=c.metadata))

    store = src.EmbeddingStore(collection_name=thu_muc, embedding_fn=embedder)
    store.add_documents(chunk_docs)
    agent = src.KnowledgeBaseAgent(store=store, llm_fn=llm_trich_xuat_chung)

    hangs, agents, diem_tong, canh_bao = [], [], 0, []
    for item in BENCHMARK:
        loc = item["filter"]
        kq = store.search_with_filter(item["query"], top_k=3, metadata_filter=loc)
        # Filter dáº¡ng list chá» cháº¡y náº¿u store há» trá»£; náº¿u khÃ´ng, káº¿t quáº£ rá»ng -> bá» filter.
        if loc and isinstance(next(iter(loc.values())), list) and not kq:
            canh_bao.append(f"Q{item['id']}: store khÃ´ng há» trá»£ filter dáº¡ng list, ÄÃ£ bá» filter")
            loc = None
            kq = store.search_with_filter(item["query"], top_k=3, metadata_filter=None)

        hang = next((i for i, r in enumerate(kq, 1) if _chuan_hoa(item["gold_snippet"]) in _chuan_hoa(r["content"])), 0)
        try:
            tra_loi = agent.answer(item["query"], top_k=3, metadata_filter=loc)
        except TypeError:  # agent cá»§a báº¡n áº¥y chÆ°a cÃ³ tham sá» metadata_filter
            tra_loi = agent.answer(item["query"], top_k=3)
        dung = _chuan_hoa(item["gold_snippet"]) in _chuan_hoa(tra_loi)

        diem = 0 if hang == 0 else (2 if hang == 1 and dung else 1)
        diem_tong += diem
        hangs.append(hang)
        agents.append(dung)

    return {
        "ten": ten,
        "chien_luoc": f"{ten_chunker}({', '.join(f'{k}={v}' for k, v in tham_so.items())})",
        "chunk": store.get_collection_size(),
        "hangs": hangs,
        "agents": agents,
        "diem": diem_tong,
        "canh_bao": canh_bao,
    }


def main() -> int:
    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Corpus   : {DATA_DIR}")
    print(f"Embedder : {backend}")
    if backend == "mock embeddings fallback":
        print("Cáº¢NH BÃO : mock cho Äiá»m gáº§n nhÆ° ngáº«u nhiÃªn â Äáº·t EMBEDDING_PROVIDER=local.")
    print()

    ket_qua = [chay(*p, embedder) for p in PHAN_CONG]

    header = f"{'ThÃ nh viÃªn':<20}{'Chiáº¿n lÆ°á»£c':<40}{'#chunk':<9}" + "".join(f"Q{i:<5}" for i in range(1, 6)) + f"{'Agent':<8}Äiá»m"
    print(header)
    print("-" * len(header))
    for r in ket_qua:
        if r.get("loi"):
            print(f"{r['ten']:<20}Lá»I: {r['loi']}")
            continue
        o = "".join(f"{('#' + str(h)) if h else 'trÆ°á»£t':<6}" for h in r["hangs"])
        a = f"{sum(r['agents'])}/5"
        print(f"{r['ten']:<20}{r['chien_luoc']:<40}{r['chunk']:<9}{o}{a:<8}{r['diem']}/10")

    for r in ket_qua:
        for c in r.get("canh_bao", []):
            print(f"  [cáº£nh bÃ¡o] {r['ten']} â {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
