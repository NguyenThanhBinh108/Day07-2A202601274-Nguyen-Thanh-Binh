"""
Demo server cho buổi thuyết trình Lab 07 (K4 — Embedding & Vector Store).

Chạy pipeline RAG THẬT (LocalEmbedder + EmbeddingStore + KnowledgeBaseAgent từ src/)
trên bộ 20 tài liệu chính sách Shopee đã thu thập, qua một giao diện web để demo
trực tiếp lúc thuyết trình. Không gọi model tóm tắt/sinh văn bản bên ngoài — nếu
không có OPENAI_API_KEY, câu trả lời của agent là đoạn ngữ cảnh đã truy xuất
(ghi rõ trong response, không giả vờ là câu trả lời do LLM sinh ra).

Chạy: python demo/server.py
Mở trình duyệt: http://127.0.0.1:5000
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

DEMO_DIR = Path(__file__).parent
ROOT_DIR = DEMO_DIR.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(DEMO_DIR))

from clause_chunker import ClauseChunker  # noqa: E402
from ingest import build_knowledge_base, load_documents  # noqa: E402
from src import KnowledgeBaseAgent  # noqa: E402
from src.chunking import FixedSizeChunker  # noqa: E402

DATA_DIR = ROOT_DIR / "data" / "k4_ecommerce"

BENCHMARK_QUERIES = [
    {
        "question": "Người mua có bao nhiêu ngày để yêu cầu trả hàng/hoàn tiền kể từ khi giao hàng thành công?",
        "customer_role": None,
        "expected_doc_ids": ["return-refund-policy"],
    },
    {
        "question": "Shopee hỗ trợ những phương thức thanh toán nào?",
        "customer_role": None,
        "expected_doc_ids": ["payment-methods"],
    },
    {
        "question": "Người bán không được đăng bán loại sản phẩm nào theo quy định?",
        "customer_role": "seller",
        "expected_doc_ids": ["seller-listing-rules", "restricted-products-policy", "shopee-mall-terms"],
    },
    {
        "question": "Shopee thu thập những loại dữ liệu cá nhân nào của người dùng?",
        "customer_role": None,
        "expected_doc_ids": ["privacy-policy"],
    },
    {
        "question": "Phí dịch vụ của chương trình ưu đãi phí vận chuyển dành cho người bán là bao nhiêu?",
        "customer_role": "seller",
        "expected_doc_ids": ["shipping-fee-discount-program"],
    },
]

app = Flask(__name__, static_folder=str(DEMO_DIR / "static"), static_url_path="")

STATE: dict = {"ready": False}


def _extractive_answer(question: str, results: list[dict]) -> tuple[str, bool]:
    """Trả lời bằng cách trích ngữ cảnh (không có OPENAI_API_KEY nên không sinh văn bản mới)."""
    context = "\n\n".join(r["content"] for r in results)
    return context[:600], False


def _load_pipelines() -> None:
    print("[demo] Đang tải LocalEmbedder (model đa ngữ) ...", flush=True)
    t0 = time.time()
    from src import LocalEmbedder

    embed = LocalEmbedder()
    print(f"[demo] LocalEmbedder sẵn sàng ({time.time() - t0:.1f}s)", flush=True)

    docs = load_documents(str(DATA_DIR))

    t0 = time.time()
    store_fixed = build_knowledge_base(
        str(DATA_DIR), embedding_fn=embed, chunker=FixedSizeChunker(chunk_size=300, overlap=40)
    )
    print(f"[demo] Store 'fixed_size' sẵn sàng: {store_fixed.get_collection_size()} chunk "
          f"({time.time() - t0:.1f}s)", flush=True)

    t0 = time.time()
    store_clause = build_knowledge_base(str(DATA_DIR), embedding_fn=embed, chunker=ClauseChunker())
    print(f"[demo] Store 'clause' sẵn sàng: {store_clause.get_collection_size()} chunk "
          f"({time.time() - t0:.1f}s)", flush=True)

    stores = {"fixed_size": store_fixed, "clause": store_clause}
    agents = {name: KnowledgeBaseAgent(store=s, llm_fn=lambda p: p) for name, s in stores.items()}

    has_llm_key = bool(os.environ.get("OPENAI_API_KEY"))

    def run_query(strategy: str, question: str, customer_role: str | None, top_k: int = 3):
        store = stores[strategy]
        metadata_filter = {"customer_role": customer_role} if customer_role else None
        results = (
            store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
            if metadata_filter
            else store.search(question, top_k=top_k)
        )
        answer, is_generated = _extractive_answer(question, results)
        return results, answer, is_generated

    benchmark_results = []
    for q in BENCHMARK_QUERIES:
        row = {"question": q["question"], "customer_role": q["customer_role"], "strategies": {}}
        for strategy in stores:
            results, _, _ = run_query(strategy, q["question"], q["customer_role"])
            top1 = results[0] if results else None
            correct = bool(top1 and top1["metadata"].get("doc_id") in q["expected_doc_ids"])
            row["strategies"][strategy] = {
                "top1_doc_id": top1["metadata"].get("doc_id") if top1 else None,
                "top1_score": round(top1["score"], 4) if top1 else None,
                "correct": correct,
            }
        benchmark_results.append(row)

    doc_meta = [d.metadata for d in docs]
    role_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for m in doc_meta:
        role_counts[m.get("customer_role", "?")] = role_counts.get(m.get("customer_role", "?"), 0) + 1
        category_counts[m.get("category", "?")] = category_counts.get(m.get("category", "?"), 0) + 1

    STATE.update(
        {
            "ready": True,
            "stores": stores,
            "run_query": run_query,
            "has_llm_key": has_llm_key,
            "benchmark_results": benchmark_results,
            "stats": {
                "doc_count": len(docs),
                "total_chars": sum(len(d.content) for d in docs),
                "chunk_counts": {name: s.get_collection_size() for name, s in stores.items()},
                "role_counts": role_counts,
                "category_counts": category_counts,
                "docs": [
                    {
                        "doc_id": d.id,
                        "title": d.metadata.get("title"),
                        "customer_role": d.metadata.get("customer_role"),
                        "category": d.metadata.get("category"),
                        "chars": len(d.content),
                    }
                    for d in docs
                ],
            },
        }
    )
    print("[demo] San sang. Mo http://127.0.0.1:5000", flush=True)


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/status")
def status():
    return jsonify({"ready": STATE.get("ready", False)})


@app.get("/api/stats")
def stats():
    if not STATE.get("ready"):
        return jsonify({"error": "pipeline chưa sẵn sàng, vui lòng chờ vài giây rồi thử lại"}), 503
    return jsonify(STATE["stats"])


@app.get("/api/benchmark")
def benchmark():
    if not STATE.get("ready"):
        return jsonify({"error": "pipeline chưa sẵn sàng, vui lòng chờ vài giây rồi thử lại"}), 503
    return jsonify({"has_llm_key": STATE["has_llm_key"], "results": STATE["benchmark_results"]})


@app.post("/api/query")
def query():
    if not STATE.get("ready"):
        return jsonify({"error": "pipeline chưa sẵn sàng, vui lòng chờ vài giây rồi thử lại"}), 503

    payload = request.get_json(force=True) or {}
    question = (payload.get("question") or "").strip()
    strategy = payload.get("strategy") or "fixed_size"
    customer_role = payload.get("customer_role") or None
    top_k = int(payload.get("top_k") or 3)

    if not question:
        return jsonify({"error": "thiếu 'question'"}), 400
    if strategy not in STATE["stores"]:
        return jsonify({"error": f"strategy không hợp lệ: {strategy}"}), 400

    results, answer, is_generated = STATE["run_query"](strategy, question, customer_role, top_k)

    return jsonify(
        {
            "question": question,
            "strategy": strategy,
            "customer_role": customer_role,
            "answer": answer,
            "answer_is_generated": is_generated,
            "results": [
                {
                    "doc_id": r["metadata"].get("doc_id"),
                    "title": r["metadata"].get("title"),
                    "customer_role": r["metadata"].get("customer_role"),
                    "category": r["metadata"].get("category"),
                    "score": round(r["score"], 4),
                    "content": r["content"],
                }
                for r in results
            ],
        }
    )


if __name__ == "__main__":
    _load_pipelines()
    app.run(host="127.0.0.1", port=5000, debug=False)
