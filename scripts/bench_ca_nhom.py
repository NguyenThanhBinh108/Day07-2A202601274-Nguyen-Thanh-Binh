"""
Chạy 5 benchmark query của nhóm trên `src/` của TỪNG thành viên — dữ liệu cho
bảng so sánh ở REPORT_NHOM.md mục 2.

Ba biến giữ NGUYÊN cho mọi người (điều kiện so sánh công bằng):
    corpus   = data/k4_ecommerce   (10 tài liệu dùng chung)
    query    = 5 câu đã khoá trong bench.py
    embedder = EMBEDDING_PROVIDER=local
Chỉ khác đúng một biến: chiến lược chunking.

Script này KHÔNG chọn hộ chiến lược — nó chỉ chạy cấu hình ghi trong PHAN_CONG
để nhóm có số liệu đối chiếu. Mỗi thành viên tự xác nhận hoặc đổi chiến lược
của mình rồi chạy lại.

Chạy:
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

# Mỗi thành viên dựng prompt theo format riêng (tiếng Việt / tiếng Anh, nhãn khác nhau).
# Stub LLM phải nhận diện được MỌI format, nếu không cột "agent trả lời đúng" sẽ đo
# độ khớp format thay vì chất lượng truy xuất — tức so sánh sai hoàn toàn.
NHAN_NGU_CANH = ["NGỮ CẢNH:", "Ngữ cảnh:", "Ngu canh:", "CONTEXT:", "Context:"]
NHAN_CAU_HOI = ["CÂU HỎI:", "Câu hỏi:", "Cau hoi:", "QUESTION:", "Question:"]
NHAN_TRA_LOI = ["TRẢ LỜI:", "Trả lời:", "ANSWER:", "Answer:"]


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
    """Bản LLM trích xuất KHÔNG phụ thuộc format prompt của từng thành viên.

    Điểm mỗi câu = số từ trùng câu hỏi × (1/thứ hạng đoạn). Nếu prompt không đánh
    số đoạn `[n]` thì dùng thứ tự xuất hiện làm thứ hạng.
    """
    sau_ngu_canh, co_ngu_canh = _cat_sau(prompt, NHAN_NGU_CANH)
    ngu_canh = _cat_truoc(sau_ngu_canh, NHAN_CAU_HOI).strip() if co_ngu_canh else ""
    cau_hoi, co_cau_hoi = _cat_sau(prompt, NHAN_CAU_HOI)
    cau_hoi = _cat_truoc(cau_hoi, NHAN_TRA_LOI).strip() if co_cau_hoi else ""
    if not ngu_canh or not cau_hoi:
        return "Không đọc được ngữ cảnh hoặc câu hỏi từ prompt."

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
        if block == 0:  # prompt không đánh số -> lấy thứ tự dòng làm thứ hạng
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
        return "Ngữ cảnh truy xuất được không chứa thông tin trả lời câu hỏi này."
    return f"{best} [{best_block}]"

# (tên hiển thị, thư mục, tên chunker, tham số) — chiến lược PHẢI khác nhau giữa các thành viên.
PHAN_CONG = [
    ("Nguyễn Thanh Bình", "Nguyen-Thanh-Binh-2A202601274", "ClauseChunker", dict(max_sentences_per_clause=1)),
    ("Trần Chí Vũ", "Tran-Chi-Vu-2A202601044", "RecursiveChunker", dict(chunk_size=400)),
    ("Trịnh Hải Đăng", "Trinh-Hai-Dang-2A202601602", "FixedSizeChunker", dict(chunk_size=500, overlap=50)),
    ("Đỗ Văn Linh", "Do-Van-Linh-2A202601190", "SentenceChunker", dict(max_sentences_per_chunk=3)),
    ("Đỗ Thu Liễu", "Do-Thu-Lieu-2A202601898", "FixedSizeChunker", dict(chunk_size=250, overlap=100)),
]


def nap_src(thu_muc: str):
    """Nạp gói src của một thành viên (mỗi người một implementation riêng)."""
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
        return {"ten": ten, "loi": f"src/ không có {ten_chunker}"}

    # KHÔNG dùng ingest.build_knowledge_base: hàm đó gắn cứng EmbeddingStore của src ở
    # gốc repo, nên mọi thành viên sẽ cùng chạy store của một người. Ở đây dựng store
    # bằng ĐÚNG lớp EmbeddingStore của từng thành viên; chỉ tái dùng hai hàm thuần của
    # ingest là load_documents và chunk_document (không phụ thuộc store).
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
        # Filter dạng list chỉ chạy nếu store hỗ trợ; nếu không, kết quả rỗng -> bỏ filter.
        if loc and isinstance(next(iter(loc.values())), list) and not kq:
            canh_bao.append(f"Q{item['id']}: store không hỗ trợ filter dạng list, đã bỏ filter")
            loc = None
            kq = store.search_with_filter(item["query"], top_k=3, metadata_filter=None)

        hang = next((i for i, r in enumerate(kq, 1) if _chuan_hoa(item["gold_snippet"]) in _chuan_hoa(r["content"])), 0)
        try:
            tra_loi = agent.answer(item["query"], top_k=3, metadata_filter=loc)
        except TypeError:  # agent của bạn ấy chưa có tham số metadata_filter
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
        print("CẢNH BÁO : mock cho điểm gần như ngẫu nhiên — đặt EMBEDDING_PROVIDER=local.")
    print()

    ket_qua = [chay(*p, embedder) for p in PHAN_CONG]

    header = f"{'Thành viên':<20}{'Chiến lược':<40}{'#chunk':<9}" + "".join(f"Q{i:<5}" for i in range(1, 6)) + f"{'Agent':<8}Điểm"
    print(header)
    print("-" * len(header))
    for r in ket_qua:
        if r.get("loi"):
            print(f"{r['ten']:<20}LỖI: {r['loi']}")
            continue
        o = "".join(f"{('#' + str(h)) if h else 'trượt':<6}" for h in r["hangs"])
        a = f"{sum(r['agents'])}/5"
        print(f"{r['ten']:<20}{r['chien_luoc']:<40}{r['chunk']:<9}{o}{a:<8}{r['diem']}/10")

    for r in ket_qua:
        for c in r.get("canh_bao", []):
            print(f"  [cảnh báo] {r['ten']} — {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
