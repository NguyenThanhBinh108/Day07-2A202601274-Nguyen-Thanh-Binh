"""
Chay benchmark THAT cho phan cua Trinh Hai Dang (FixedSizeChunker(500,50))
tren corpus + src/ THAT cua nhom Bazoka (data/k4_ecommerce, 10 file).

5 cau hoi + gold snippet lay dung tu Muc 3 REPORT_NHOM.md (nhom da thong nhat),
gold_snippet la cum trich verbatim tu chinh cac file .md trong corpus.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from ingest import build_knowledge_base  # noqa: E402
from src import FixedSizeChunker, KnowledgeBaseAgent, LocalEmbedder  # noqa: E402

DATA_DIR = str(REPO_ROOT / "data" / "k4_ecommerce")

BENCHMARK = [
    {
        "id": 1,
        "query": "Đơn vị vận chuyển liên hệ người mua mấy lần để giao hàng, và nếu không liên hệ được thì người mua được yêu cầu giao lại trong thời hạn bao lâu?",
        "filter": None,
        "gold_snippet": "không quá 5 ngày kể từ lần liên hệ đầu tiên",
        "expected_doc": "delivery-process",
    },
    {
        "id": 2,
        "query": "Tôi trả hàng bằng cách tự sắp xếp vận chuyển cho đơn khác tỉnh/thành thì Shopee hoàn lại phí vận chuyển hoàn trả bao nhiêu và bằng hình thức gì?",
        "filter": None,
        "gold_snippet": "40.000 Shopee Xu nếu khác tỉnh/thành",
        "expected_doc": "return-shipping-fee",
    },
    {
        "id": 3,
        "query": "Phí vận chuyển được tính và xử lý như thế nào?",
        "filter": {"customer_role": "seller"},
        "gold_snippet": "6%, tối đa 50.000 VNĐ trên giá bán của mỗi sản phẩm",
        "expected_doc": "shipping-fee-discount-program",
    },
    {
        "id": 4,
        "query": "Người bán có được đăng bán đồ cổ và tác phẩm nghệ thuật trên Shopee không, và nếu vi phạm chính sách sản phẩm cấm thì bị xử lý ra sao?",
        "filter": {"customer_role": "seller"},
        "gold_snippet": "Đồ cổ và tác phẩm nghệ thuật chưa được cấp phép",
        "expected_doc": "restricted-products-policy",
    },
    {
        "id": 5,
        "query": "Người mua gửi khiếu nại đơn hàng ở đâu trên ứng dụng và Shopee đưa ra quyết định trong bao lâu đối với khiếu nại thông thường?",
        "filter": {"customer_role": ["buyer", "both"]},
        "gold_snippet": "quyết định trong vòng 7 ngày làm việc đối với khiếu nại thông thường",
        "expected_doc": "marketplace-operating-regulation",
    },
]


def _chuan_hoa(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _tu(s: str) -> set:
    return set(re.findall(r"\w+", _chuan_hoa(s)))


def llm_trich_xuat(prompt: str) -> str:
    """Extractive stub: cau nao trong ngu canh trung nhieu tu voi cau hoi nhat -> tra ve cau do."""
    if "NGá»® Cáº¢NH:" in prompt:
        ctx = prompt.split("NGá»® Cáº¢NH:", 1)[1].split("CÃU Há»I:", 1)[0]
        q = prompt.split("CÃU Há»I:", 1)[1].split("TRáº¢ Lá»I:", 1)[0]
    else:
        ctx = prompt.split("Context:", 1)[1].split("Question:", 1)[0] if "Context:" in prompt else ""
        q = prompt.split("Question:", 1)[1].split("Answer:", 1)[0] if "Question:" in prompt else ""
    tu_hoi = _tu(q)
    best, best_score = "", -1.0
    for cau in re.split(r"(?<=[.!?])\s+", ctx):
        cau = cau.strip()
        if len(cau) < 15:
            continue
        score = len(tu_hoi & _tu(cau))
        if score > best_score:
            best, best_score = cau, score
    return best


def main() -> None:
    embed = LocalEmbedder()
    chunker = FixedSizeChunker(chunk_size=500, overlap=50)
    store = build_knowledge_base(DATA_DIR, embedding_fn=embed, chunker=chunker)
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_trich_xuat)

    print(f"Chien luoc  : FixedSizeChunker(chunk_size=500, overlap=50)")
    print(f"So chunk    : {store.get_collection_size()}")
    print()

    tong_diem = 0
    dung_agent = 0
    for item in BENCHMARK:
        loc = item["filter"]
        kq = (
            store.search_with_filter(item["query"], top_k=3, metadata_filter=loc)
            if loc
            else store.search(item["query"], top_k=3)
        )
        hang = next(
            (i for i, r in enumerate(kq, 1) if _chuan_hoa(item["gold_snippet"]) in _chuan_hoa(r["content"])), 0
        )
        top1_doc = kq[0]["metadata"].get("doc_id") if kq else None

        try:
            tra_loi = agent.answer(item["query"], top_k=3, metadata_filter=loc)
        except TypeError:
            tra_loi = agent.answer(item["query"], top_k=3)
        dung = _chuan_hoa(item["gold_snippet"]) in _chuan_hoa(tra_loi)
        if dung:
            dung_agent += 1

        diem = 0 if hang == 0 else (2 if hang == 1 and dung else 1)
        tong_diem += diem

        print(f"Q{item['id']}: hang={hang or 'truot'} | top1_doc={top1_doc} | agent_dung={dung} | diem={diem}/2")
        print(f"    query : {item['query']}")
        print(f"    tra_loi_agent (rut gon): {tra_loi[:150]}")
        print()

    print(f"TONG DIEM: {tong_diem}/10  |  Agent dung: {dung_agent}/5")


if __name__ == "__main__":
    main()
