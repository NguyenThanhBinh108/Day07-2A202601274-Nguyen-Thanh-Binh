"""
bench.py — chạy 5 benchmark query của NHÓM trên chiến lược chunking của RIÊNG tôi.

Sinh viên : Nguyễn Thanh Bình — 2A202601274 — lớp K4
Chiến lược: ClauseChunker (chia theo điều/khoản + gắn tiêu đề), tự viết trong src/chunking.py

Ba điều kiện phải GIỐNG NHAU giữa các thành viên để so sánh công bằng:
    corpus  = data/k4_ecommerce   (10 tài liệu, dùng chung ở gốc repo)
    query   = 5 câu trong BENCHMARK bên dưới (đã khoá, không đổi sau khi chạy)
    embedder= EMBEDDING_PROVIDER=local
Chỉ MỘT dòng được khác nhau: dòng chọn chunker ở CHUNKER bên dưới.

Chạy:
    $env:EMBEDDING_PROVIDER="local"; python bench.py
"""
from __future__ import annotations

import os
import re
import sys
import unicodedata

from ingest import build_knowledge_base
from main import _select_embedder
from src import ClauseChunker, KnowledgeBaseAgent

DATA_DIR = os.getenv("LAB_DATA_DIR", "data/k4_ecommerce")

# >>> DÒNG DUY NHẤT khác với các bạn cùng nhóm <<<
CHUNKER = ClauseChunker(max_sentences_per_clause=1)
TEN_CHIEN_LUOC = "ClauseChunker(max_sentences_per_clause=1) — chia theo điều/khoản + gắn tiêu đề"

# 5 câu hỏi đánh giá của nhóm. `gold_snippet` là cụm trích NGUYÊN VĂN từ corpus,
# đã grep kiểm tra mỗi cụm chỉ khớp đúng 1 tài liệu -> chấm được ở MỨC CHUNK.
BENCHMARK = [
    {
        "id": 1,
        "query": "Đơn vị vận chuyển liên hệ người mua mấy lần để giao hàng, và nếu không liên hệ được thì người mua được yêu cầu giao lại trong thời hạn bao lâu?",
        "gold": "Liên hệ 2-3 lần; người mua có thể yêu cầu giao lại trong không quá 5 ngày kể từ lần liên hệ đầu tiên.",
        "gold_doc": "delivery-process",
        "gold_snippet": "không quá 5 ngày kể từ lần liên hệ đầu tiên",
        "filter": None,
    },
    {
        "id": 2,
        "query": "Tôi trả hàng bằng cách tự sắp xếp vận chuyển cho đơn khác tỉnh/thành thì Shopee hoàn lại phí vận chuyển hoàn trả bao nhiêu và bằng hình thức gì?",
        "gold": "Hoàn bằng Shopee Xu trong 3-5 ngày làm việc: 25.000 Xu cùng tỉnh/thành, 40.000 Xu khác tỉnh/thành.",
        "gold_doc": "return-shipping-fee",
        "gold_snippet": "40.000 Shopee Xu nếu khác tỉnh/thành",
        "filter": None,
    },
    {
        "id": 3,
        # Câu BẮT BUỘC dùng filter của K4, thiết kế theo đúng mẫu đề bài mô tả: câu hỏi
        # KHÔNG nêu người hỏi là ai, trong khi corpus có hai tài liệu cùng chủ đề "phí
        # vận chuyển" nhưng khác đối tượng và khác đáp án —
        #   return-shipping-fee (buyer)            : hoàn 25.000/40.000 Shopee Xu
        #   shipping-fee-discount-program (seller) : phí dịch vụ 6%, tối đa 50.000 VNĐ
        # Không lọc thì top-1 rơi vào tài liệu người mua và trả lời sai đối tượng.
        "query": "Phí vận chuyển được tính và xử lý như thế nào?",
        "gold": "Với người bán: phí dịch vụ của chương trình là 6%, tối đa 50.000 VNĐ trên giá bán mỗi sản phẩm.",
        "gold_doc": "shipping-fee-discount-program",
        "gold_snippet": "6%, tối đa 50.000 VNĐ trên giá bán của mỗi sản phẩm",
        "filter": {"customer_role": "seller"},
    },
    {
        "id": 4,
        "query": "Người bán có được đăng bán đồ cổ và tác phẩm nghệ thuật trên Shopee không, và nếu vi phạm chính sách sản phẩm cấm thì bị xử lý ra sao?",
        "gold": "Không được. Vi phạm bị xóa sản phẩm, hạn chế/khóa tài khoản, tịch thu số dư.",
        "gold_doc": "restricted-products-policy",
        "gold_snippet": "Đồ cổ và tác phẩm nghệ thuật chưa được cấp phép",
        "filter": {"customer_role": "seller"},
    },
    {
        "id": 5,
        "query": "Người mua gửi khiếu nại đơn hàng ở đâu trên ứng dụng và Shopee đưa ra quyết định trong bao lâu đối với khiếu nại thông thường?",
        "gold": "Khiếu nại qua mục Đơn Mua; quyết định trong 7 ngày làm việc với khiếu nại thông thường.",
        "gold_doc": "marketplace-operating-regulation",
        "gold_snippet": "7 ngày làm việc đối với khiếu nại thông thường",
        # Tài liệu gold có customer_role=both -> lọc cứng "buyer" sẽ MẤT gold doc.
        "filter": {"customer_role": ["buyer", "both"]},
    },
]


def _chuan_hoa(text: str) -> str:
    text = unicodedata.normalize("NFC", text.lower())
    return re.sub(r"\s+", " ", re.sub(r"[^\w\sÀ-ỹ]", " ", text)).strip()


def _tu(text: str) -> set[str]:
    return {t for t in _chuan_hoa(text).split() if len(t) > 2}


def llm_trich_xuat(prompt: str) -> str:
    """LLM tất định: trích câu trong ngữ cảnh, điểm = số từ trùng x (1/thứ hạng).

    Repo không cấu hình API key. Hàm này chỉ TRÍCH từ ngữ cảnh đã truy xuất nên
    không bao giờ bịa, và luôn ghi số hiệu đoạn [n] để kiểm chứng grounding.
    Nhân trọng số thứ hạng để không biến thành keyword matching thuần — nếu bỏ,
    tín hiệu ngữ nghĩa mà retriever tạo ra sẽ bị vứt đi.
    """
    cau_hoi = prompt.split("CÂU HỎI:")[-1].split("TRẢ LỜI:")[0].strip()
    ngu_canh = prompt.split("NGỮ CẢNH:")[-1].split("CÂU HỎI:")[0].strip()
    if not ngu_canh or ngu_canh.startswith("(Không tìm thấy"):
        return "Không tìm thấy thông tin trong tài liệu."

    tu_hoi = _tu(cau_hoi)
    best, best_block, best_score, best_trung = "", 0, -1.0, 0
    block = 0
    for line in ngu_canh.splitlines():
        m = re.match(r"^\[(\d+)\]", line.strip())
        if m:
            block = int(m.group(1))
            continue
        trong_so = 1.0 / block if block else 1.0
        for cau in re.split(r"(?<=[.!?])\s+", line):
            cau = cau.strip()
            if len(cau) < 15:
                continue
            trung = len(tu_hoi & _tu(cau))
            if trung * trong_so > best_score:
                best, best_block, best_score, best_trung = cau, block, trung * trong_so, trung
    if best_trung <= 0:
        return "Ngữ cảnh truy xuất được không chứa thông tin trả lời câu hỏi này."
    return f"{best} [{best_block}]"


def chunk_chua_gold(kq: dict, item: dict) -> bool:
    """Chấm ở MỨC CHUNK: chunk phải chứa nguyên văn câu trả lời, không chỉ đúng doc_id."""
    return _chuan_hoa(item["gold_snippet"]) in _chuan_hoa(kq.get("content", ""))


def thu_hang(ket_qua: list[dict], item: dict) -> int:
    for hang, kq in enumerate(ket_qua, start=1):
        if chunk_chua_gold(kq, item):
            return hang
    return 0


def main() -> int:
    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)

    print("=" * 96)
    print(f"Chiến lược : {TEN_CHIEN_LUOC}")
    print(f"Corpus     : {DATA_DIR}")
    print(f"Embedder   : {backend}")
    if backend == "mock embeddings fallback":
        print("CẢNH BÁO   : mock cho điểm gần như ngẫu nhiên — đặt EMBEDDING_PROVIDER=local để đo thật.")
    print("=" * 96)

    store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=CHUNKER)
    print(f"Đã nạp {store.get_collection_size()} chunk từ corpus\n")

    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_trich_xuat)
    tong_diem = 0

    for item in BENCHMARK:
        ket_qua = store.search_with_filter(item["query"], top_k=3, metadata_filter=item["filter"])
        hang = thu_hang(ket_qua, item)
        tra_loi = agent.answer(item["query"], top_k=3, metadata_filter=item["filter"])
        dung = _chuan_hoa(item["gold_snippet"]) in _chuan_hoa(tra_loi)

        # Rubric docs/SCORING.md: 2đ nếu gold ở top-1 và agent đúng, 1đ nếu có trong
        # top-3 nhưng lệch, 0đ nếu không có bằng chứng đáp án trong top-3.
        diem = 0 if hang == 0 else (2 if hang == 1 and dung else 1)
        tong_diem += diem

        print(f"--- Q{item['id']}: {item['query']}")
        print(f"    Gold  : {item['gold']}")
        print(f"    Filter: {item['filter']}")
        for i, kq in enumerate(ket_qua, start=1):
            danh_dau = "  <== CHUNK CHỨA GOLD" if chunk_chua_gold(kq, item) else ""
            xem = kq["content"].replace("\n", " ")[:100]
            print(f"    top{i} score={kq['score']:.4f} doc={kq['metadata'].get('doc_id')}{danh_dau}")
            print(f"         {xem}...")
        print(f"    Hạng chunk chứa gold: {'#' + str(hang) if hang else 'TRƯỢT khỏi top-3'}")
        print(f"    Agent: {tra_loi}")
        print(f"    Điểm : {diem}/2\n")

    print("=" * 96)
    print(f"TỔNG ĐIỂM BENCHMARK: {tong_diem}/10")

    # A/B filter cho câu bắt buộc của K4 — chứng minh metadata có tác dụng hay không.
    print("\n--- A/B metadata filter (câu 3, câu bắt buộc của K4) ---")
    item = BENCHMARK[2]
    for nhan, f in (("CÓ filter   ", item["filter"]), ("KHÔNG filter", None)):
        kq = store.search_with_filter(item["query"], top_k=3, metadata_filter=f)
        docs = [r["metadata"].get("doc_id") for r in kq]
        print(f"    {nhan} -> top-3: {docs}")
        print(f"                  hạng chunk gold: {thu_hang(kq, item) or 'trượt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
