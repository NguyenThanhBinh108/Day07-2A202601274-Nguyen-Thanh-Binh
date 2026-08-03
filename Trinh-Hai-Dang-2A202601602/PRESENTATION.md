# Lab 07 — Embedding & Vector Store (K4: Chính sách TMĐT Shopee)

> Tài liệu tổng quan phục vụ thuyết trình. Mô tả toàn bộ nội dung trong folder nộp bài `Trinh-Hai-Dang-2A202601602/`: kiến trúc hệ thống, dữ liệu đã thu thập, kết quả thực nghiệm, và cách chạy demo trực tiếp.
>
> **Sinh viên:** Trịnh Hải Đăng — 2A202601602 — Nhóm B7-E402
> **Chủ đề K4:** Chính sách thương mại điện tử Shopee (đổi trả, người bán, thanh toán/giao hàng)

**Mục lục**

1. [Tóm tắt 30 giây](#1-tóm-tắt-30-giây)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Bản đồ thư mục](#3-bản-đồ-thư-mục)
4. [Dữ liệu: 20 tài liệu chính sách Shopee](#4-dữ-liệu-20-tài-liệu-chính-sách-shopee)
5. [Kết quả thực nghiệm chính](#5-kết-quả-thực-nghiệm-chính)
6. [Phát hiện đáng trình bày](#6-phát-hiện-đáng-trình-bày-chiến-lược-hợp-lý-về-lý-thuyết-vẫn-có-thể-thua-baseline)
7. [Cách chạy demo trực tiếp](#7-cách-chạy-demo-trực-tiếp-dùng-khi-thuyết-trình)
8. [Việc còn lại trước khi nộp](#8-việc-còn-lại-trước-khi-nộp-theo-planmd)

---

## 1. Tóm tắt 30 giây

Xây dựng một hệ thống **RAG (Retrieval-Augmented Generation)** hoàn chỉnh từ số 0: chia nhỏ văn bản (chunking) → nhúng vector (embedding) → lưu trữ & tìm kiếm (vector store) → tác tử trả lời dựa trên ngữ cảnh (agent). Áp dụng lên **20 tài liệu chính sách thật của Shopee** (help.shopee.vn), tổng cộng **~306.000 ký tự** nội dung verbatim đầy đủ (không phải bản tóm tắt). Kết quả: **42/42 unit test pass**, **5/5 câu hỏi benchmark trả lời đúng ngay top-1** khi dùng embedder ngữ nghĩa thật.

---

## 2. Kiến trúc hệ thống

```text
                    ┌─────────────────────┐
   data/*.md   ───▶ │  ingest.py           │
 (front matter      │  parse_front_matter  │
  + nội dung)       │  build_knowledge_base│
                    └──────────┬──────────┘
                               │ Document(id, content, metadata)
                               ▼
                    ┌─────────────────────┐
                    │  src/chunking.py     │
                    │  FixedSizeChunker    │  ← chia theo kích thước cố định
                    │  SentenceChunker     │  ← chia theo câu
                    │  RecursiveChunker    │  ← đệ quy theo separator ưu tiên
                    │  compute_similarity  │  ← cosine similarity
                    └──────────┬──────────┘
                               │ list[str] chunks (+ metadata gắn vào từng chunk)
                               ▼
                    ┌─────────────────────┐
                    │  src/embeddings.py   │
                    │  MockEmbedder        │  ← test/dev, gần ngẫu nhiên
                    │  LocalEmbedder       │  ← sentence-transformers đa ngữ (dùng cho benchmark)
                    │  OpenAIEmbedder      │  ← tùy chọn, cần API key
                    └──────────┬──────────┘
                               │ vector [float]
                               ▼
                    ┌─────────────────────┐
                    │  src/store.py        │
                    │  EmbeddingStore      │
                    │  .add_documents()    │
                    │  .search()           │  ← rank theo dot product
                    │  .search_with_filter()│ ← lọc metadata trước khi search
                    │  .delete_document()  │
                    └──────────┬──────────┘
                               │ top-k chunks
                               ▼
                    ┌─────────────────────┐
                    │  src/agent.py        │
                    │  KnowledgeBaseAgent  │
                    │  .answer(question)   │  ← retrieve → build prompt → gọi LLM
                    └─────────────────────┘
```

**Điểm thiết kế đáng chú ý:** `EmbeddingStore` nhận `embedding_fn` qua dependency injection — cùng một logic store/search hoạt động với mock (test nhanh, không cần internet) hoặc embedder thật (kết quả có ý nghĩa ngữ nghĩa), không cần sửa code.

---

## 3. Bản đồ thư mục

| Đường dẫn | Nội dung |
|---|---|
| `src/chunking.py` | 3 chiến lược chunking có sẵn + `compute_similarity` + `ChunkingStrategyComparator` |
| `src/store.py` | `EmbeddingStore` — lưu trữ, tìm kiếm, lọc metadata, xóa |
| `src/agent.py` | `KnowledgeBaseAgent` — luồng RAG hoàn chỉnh |
| `src/embeddings.py` | 3 backend embedding (mock / local / OpenAI) |
| `src/models.py` | `Document` dataclass |
| `ingest.py` | Pipeline nạp dữ liệu: parse front matter → chunk → gắn metadata → nạp vào store |
| `data/k4_ecommerce/` | **20 tài liệu** chính sách Shopee (`.md`) + `sources.csv` kiểm kê nguồn |
| `tests/test_solution.py` | 42 unit test cho toàn bộ `src/` |
| `report/REPORT_CANHAN.md` | Báo cáo cá nhân — lý thuyết, hướng tiếp cận code, dự đoán similarity, kết quả truy xuất |
| `report/REPORT_NHOM.md` | Báo cáo nhóm — lựa chọn dữ liệu, thiết kế chiến lược, benchmark, demo |
| `demo/` | Giao diện web demo trực tiếp (Flask) — gọi pipeline Python thật, so sánh 2 chiến lược chunking, xem `demo/README.md` |
| `PLAN.md` (ở thư mục cha) | Nhật ký kế hoạch & tiến độ chi tiết từng bước |
| `PRESENTATION.md` | File này — tổng quan phục vụ thuyết trình |

---

## 4. Dữ liệu: 20 tài liệu chính sách Shopee

**Vì sao chỉ một nguồn (help.shopee.vn)?** Trộn nhiều sàn TMĐT (Shopee/Tiki/Lazada) sẽ làm văn phong và cấu trúc điều khoản không nhất quán — khi đó khác biệt kết quả benchmark giữa các chiến lược chunking có thể do khác nguồn dữ liệu chứ không phải do khác chiến lược. Một nguồn duy nhất giữ biến số thí nghiệm sạch.

**Vì sao 20 thay vì 5-10 (mức đề bài yêu cầu)?** Mở rộng có chủ đích để có kho ngữ liệu đủ lớn cho việc so sánh chiến lược chunking có ý nghĩa thống kê hơn, và để bộc lộ được các trường hợp biên (edge case) thực tế — ví dụ phát hiện lỗi định dạng heading không nhất quán ở Mục 6 bên dưới chỉ xuất hiện khi corpus đủ đa dạng.

**Phân bố theo vai trò khách hàng (`customer_role`):**

| Vai trò | Số tài liệu | Ví dụ |
|---|:---:|---|
| `buyer` | 10 | return-refund-policy, payment-methods, warranty-policy... |
| `seller` | 6 | seller-listing-rules, restricted-products-policy, shopee-mall-terms... |
| `both` | 4 | marketplace-operating-regulation, privacy-policy, dispute-resolution-process... |

**Chất lượng thu thập:** Nội dung được trích **verbatim đầy đủ** trực tiếp từ dữ liệu SSR (`window["FORGE_SSR_DATA_MAP"]`) nhúng sẵn trong trang HTML gốc — không qua bước tóm tắt AI trung gian (vốn làm mất chi tiết/con số cụ thể). Một số tài liệu là văn bản pháp lý đầy đủ: quy chế sàn TMĐT (77.541 ký tự), chính sách bảo mật (42.987 ký tự), điều khoản Shopee Mall (33.464 ký tự).

---

## 5. Kết quả thực nghiệm chính

### 5.1 Code core — 42/42 test pass

```text
pytest tests/ -v
============================= 42 passed in 0.09s ==============================
```

### 5.2 Dự đoán Cosine Similarity — 5/5 đúng (với embedder thật)

| Cặp câu | Dự đoán | Điểm thực tế (`LocalEmbedder`) | Điểm thực tế (`_mock_embed`) |
|---|:---:|:---:|:---:|
| "Đơn hàng giao chậm" vs "đơn hàng đến trễ" | cao | **0.642** ✅ | 0.183 ❌ |
| "Đơn hàng giao chậm" vs "đổi màu sản phẩm" | thấp | **0.098** ✅ | 0.322 ❌ |
| "Người bán cung cấp thông tin chính xác" vs "mô tả đúng sự thật" | cao | **0.861** ✅ | -0.058 ❌ |
| "Người bán cung cấp thông tin chính xác" vs "trời Hà Nội mưa to" | thấp | **-0.070** ✅ | -0.063 ✅ (tình cờ) |
| "Shopee hỗ trợ COD" vs "trả tiền mặt lúc nhận hàng" | cao | **0.810** ✅ | -0.111 ❌ |

→ Minh chứng trực quan: **mock embedder gần như ngẫu nhiên** (4/5 sai), **embedder ngữ nghĩa thật cho kết quả đúng trực giác 5/5**.

### 5.3 Benchmark truy xuất — 5/5 câu đúng ngay top-1

Chạy 5 câu hỏi tự đề xuất (2 câu cần `metadata_filter={"customer_role": "seller"}` theo đúng yêu cầu K4) trên `FixedSizeChunker(300, 40)` + `LocalEmbedder`, corpus 20 tài liệu → **1185 chunk**:

| # | Câu hỏi | Top-1 đúng? | Score |
|---|---|:---:|:---:|
| 1 | Số ngày trả hàng/hoàn tiền | ✅ | 0.765 |
| 2 | Phương thức thanh toán | ✅ | 0.797 |
| 3 | Sản phẩm cấm đăng bán *(filter seller)* | ✅ | 0.803 |
| 4 | Dữ liệu cá nhân Shopee thu thập | ✅ | 0.764 |
| 5 | Phí ưu đãi vận chuyển *(filter seller)* | ✅ | 0.733 |

### 5.4 So sánh 3 lần chạy — minh chứng "đừng dùng mock để kết luận chiến lược"

| Cấu hình | Số chunk | Số câu đúng top-3 | Score top-1 trung bình |
|---|:---:|:---:|:---:|
| Mock embedder + dữ liệu tóm tắt | 105 | 0 / 5 | ~0.24 |
| Local embedder + dữ liệu tóm tắt | 105 | 5 / 5 (1 câu chỉ top-2) | ~0.71 |
| **Local embedder + dữ liệu đầy đủ** | **1185** | **5 / 5 (cả 5 đúng top-1)** | **~0.78** |

---

## 6. Phát hiện đáng trình bày: chiến lược "hợp lý về lý thuyết" vẫn có thể thua baseline

Thiết kế thêm `ClauseChunker` (chunk theo ranh giới điều/khoản, đúng gợi ý K4) với giả thuyết: văn bản luật/điều khoản nên được chunk theo từng điều thay vì cắt theo kích thước cố định.

**Kết quả:** `ClauseChunker` chỉ đúng **3/5** câu top-1, thua baseline `FixedSizeChunker` (5/5).

**Nguyên nhân thật (đã truy vết):**
1. `payment-methods.md` được viết bằng heading Markdown (`## 1. ...`) trong khi 19 tài liệu còn lại dùng heading dạng `**1. TÊN ĐIỀU KHOẢN**` — `ClauseChunker` không nhận diện được kiểu heading khác, "rơi" về chế độ dự phòng (chia theo đoạn văn), tạo ra 40 chunk rất nhỏ (72-176 ký tự) thay vì ~9 chunk theo từng phương thức thanh toán → làm giảm độ chính xác câu hỏi 2.
2. Với văn bản luật rất dài (`marketplace-operating-regulation`, 77K ký tự), một chunk-điều-khoản có thể dài tới 1500+ ký tự, nội dung rộng nhưng loãng — có thể vô tình khớp một phần với nhiều câu hỏi khác nhau, lấn át chunk nhỏ-nhưng-đúng-trọng-tâm từ tài liệu chuyên biệt hơn (câu hỏi 4).

**Bài học trình bày:** ý tưởng chiến lược đúng không đảm bảo kết quả tốt hơn nếu triển khai chưa xử lý hết các trường hợp biên của dữ liệu thật — đúng tinh thần `docs/SCORING.md`: đánh giá cao *khả năng suy nghĩ & giải thích* hơn điểm số truy xuất thuần túy.

---

## 7. Cách chạy demo trực tiếp (dùng khi thuyết trình)

### 7.1 Giao diện web trực tiếp (khuyến nghị cho thuyết trình)

```bash
pip install -r requirements.txt -r requirements-local.txt -r demo/requirements-demo.txt
python demo/server.py
# chờ dòng "[demo] San sang." rồi mở http://127.0.0.1:5000
```

Trang web gọi thẳng pipeline Python thật (`LocalEmbedder` + `EmbeddingStore` + `KnowledgeBaseAgent`) qua Flask — không phải dữ liệu tĩnh dựng sẵn. Có ô nhập câu hỏi trực tiếp, chọn chiến lược chunking (`FixedSizeChunker` vs `ClauseChunker`), lọc theo `customer_role`, và bảng benchmark 5 câu hỏi tính lại mỗi lần khởi động. Chi tiết: `demo/README.md`.

### 7.2 Demo dòng lệnh nhanh (không cần Flask)

```bash
pip install -r requirements.txt
pip install -r requirements-local.txt   # bắt buộc để có embedder thật, không dùng mock

pytest tests/ -v

python - <<'PY'
from ingest import build_knowledge_base
from src import LocalEmbedder, KnowledgeBaseAgent
from src.chunking import FixedSizeChunker

embed = LocalEmbedder()
store = build_knowledge_base("data/k4_ecommerce", embedding_fn=embed,
                              chunker=FixedSizeChunker(chunk_size=300, overlap=40))
print("Tổng số chunk:", store.get_collection_size())

agent = KnowledgeBaseAgent(store=store, llm_fn=lambda p: p[-300:])
print(agent.answer("Shopee hỗ trợ những phương thức thanh toán nào?"))
PY
```

---

## 8. Việc còn lại trước khi nộp (theo `PLAN.md`)

- [x] `REPORT_NHOM.md` — 5 thành viên nhóm Bazoka đã điền chiến lược riêng ở Mục 2 (mỗi người một chiến lược khác nhau), benchmark thật trên cùng corpus + cùng 5 câu hỏi ở Mục 3
- [ ] Buổi thuyết trình & demo trước lớp chưa diễn ra — sau đó điền phần "bài học từ nhóm khác" vào cả hai báo cáo, và chấm điểm mục Demo trong `REPORT_NHOM.md`
- [x] `pytest tests/ -v` — 42/42, đã rà soát lần cuối
