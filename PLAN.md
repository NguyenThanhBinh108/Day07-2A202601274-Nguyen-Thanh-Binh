# PLAN.md — Kế hoạch làm Lab 07 (K4: Embedding & Vector Store — Chính sách TMĐT)

> File kế hoạch cá nhân, tổng hợp từ README.md, exercises.md, K4_VARIANT.md, docs/SCORING.md, docs/DATA_COLLECTION.md, docs/EVALUATION.md.
> Sinh viên: Trịnh Hải Đăng — MSSV 01602 — Lớp K4
> Nộp bài trong: `Trinh_Hai_Dang_01602/`

---

## 0. Việc cần làm ngay: chuẩn bị folder nộp bài — ĐÃ XONG

- [x] Tạo folder `Trinh_Hai_Dang_01602/` ở root repo
- [x] Copy `src/`, `tests/`, `ingest.py`, `main.py`, `data/`, `report/`, `requirements.txt`, `requirements-local.txt`, `.env.example` vào đó

```
Trinh_Hai_Dang_01602/
├── src/                  ← chunking.py, store.py, agent.py, embeddings.py, models.py (đã hoàn thành TODO)
├── tests/                ← test_solution.py — KHÔNG sửa file test
├── ingest.py             ← pipeline đã cung cấp sẵn
├── main.py
├── data/                 ← dữ liệu mẫu có sẵn; cần thêm data/<ten-chu-de>/ của nhóm (Bước 4)
├── report/
│   ├── REPORT_NHOM.md    ← chưa điền
│   └── REPORT_CANHAN.md  ← chưa điền (phần của Đăng)
├── requirements.txt
├── requirements-local.txt
└── .env.example          ← đổi tên thành .env khi cần EMBEDDING_PROVIDER=local (Bước 5)
```

Toàn bộ code TODO viết trực tiếp trong `Trinh_Hai_Dang_01602/src/`. Chạy test bằng:

```bash
cd Trinh_Hai_Dang_01602
python -m pytest tests/ -v
```

---

## 1. Tổng quan cấu trúc điểm (100đ)

| Phần | Điểm | Nộp ở đâu |
|---|---|---|
| Code core (`src/`) pass test | 30 | `Trinh_Hai_Dang_01602/src/` |
| Hướng tiếp cận (giải thích code) | 10 | `REPORT_CANHAN.md` §2 |
| Kết quả truy xuất (5 câu benchmark) | 10 | `REPORT_CANHAN.md` §5 |
| Khởi động (cosine + chunking math) | 5 | `REPORT_CANHAN.md` §1 |
| Dự đoán similarity (5 cặp câu) | 5 | `REPORT_CANHAN.md` §4 |
| **Cá nhân** | **60** | |
| Thiết kế chiến lược (nhóm) | 15 | `REPORT_NHOM.md` §2 |
| Chất lượng bộ tài liệu (nhóm) | 10 | `REPORT_NHOM.md` §1 |
| Chất lượng truy xuất (nhóm) | 10 | `REPORT_NHOM.md` §3 |
| Demo | 5 | `REPORT_NHOM.md` §4 |
| **Nhóm** | **40** | |

---

## 2. Thứ tự công việc (làm theo đúng thứ tự này)

### Bước 1 — Setup môi trường — ĐÃ XONG
- [x] Cài `pytest`, `python-dotenv` trong `Trinh_Hai_Dang_01602/`
- [x] Chạy `pytest tests/ -v` baseline (TODO chưa làm → nhiều test fail, đúng kỳ vọng)

### Bước 2 — Khởi động lý thuyết (Bài 1.1, 1.2 — 5đ) — CHƯA LÀM
- [ ] Viết giải thích cosine similarity (khái niệm, ví dụ câu tương đồng cao/thấp, vì sao ưu tiên hơn Euclidean) → `REPORT_CANHAN.md` Phần 1
- [ ] Giải bài toán tính số chunk: `len=10000, chunk_size=500, overlap=50` → công thức `ceil((10000-50)/(500-50))`; rồi so sánh khi `overlap=100`
- Việc lý thuyết, không phụ thuộc code — có thể làm bất kỳ lúc nào, kể cả trước Bước 3.

### Bước 3 — Lập trình cốt lõi cá nhân (30đ) — CODE XONG, REPORT CHƯA
1. [x] `src/chunking.py`
   - [x] `SentenceChunker` (tách theo câu, gộp lại thành chunk)
   - [x] `RecursiveChunker` (thử separator theo thứ tự, đệ quy nếu đoạn còn quá lớn)
   - [x] `compute_similarity` (cosine, có guard chia-cho-0)
   - [x] `ChunkingStrategyComparator` (gọi cả 3 chiến lược + tính thống kê)
2. [x] `src/store.py` — `EmbeddingStore`
   - [x] `__init__` (khởi tạo in-memory, fallback nếu không có ChromaDB)
   - [x] `add_documents` (embed + lưu)
   - [x] `search` (embed query, rank theo dot product)
   - [x] `get_collection_size`
   - [x] `search_with_filter` (lọc metadata trước, search sau)
   - [x] `delete_document`
3. [x] `src/agent.py` — `KnowledgeBaseAgent.answer` (retrieve → build prompt → gọi LLM)
4. [x] `pytest tests/ -v` → **42/42 PASS**
- [ ] Viết `REPORT_CANHAN.md` Phần 2 (hướng tiếp cận từng phần) — **còn lại, chưa làm**

### Bước 4 — Chuẩn bị dữ liệu nhóm (song song với nhóm, Bài 3.0) — CHƯA LÀM
- [ ] Đọc `docs/DATA_COLLECTION.md` + `K4_VARIANT.md` (bắt buộc: `customer_role`, `source_url`, `retrieved_at`, `document_version`)
- [ ] Nhóm thống nhất phạm vi cụ thể trong chủ đề K4 (vd: đổi trả, điều kiện người bán, thanh toán, giao hàng, quyền riêng tư)
- [ ] Thu thập **10 tài liệu** (đề bài cho khoảng 5-10 → luôn làm mức tối đa) `.md`/`.txt` → `data/<ten-chu-de>/`, kèm `sources.csv`
- [ ] Nạp bằng `build_knowledge_base()` trong `ingest.py` — không viết lại pipeline
- [ ] Ghi bảng tài liệu vào `REPORT_NHOM.md` Phần 1

### Bước 5 — Thiết kế chiến lược cá nhân (Bài 3.1 — 15đ nhóm) — CHƯA LÀM
- [ ] Đặt `EMBEDDING_PROVIDER=local` trong `.env` (bắt buộc để so sánh có ý nghĩa, KHÔNG dùng mock)
- [ ] Chạy baseline: `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu, ghi kết quả
- [ ] Chọn 1 chiến lược riêng (built-in tuned hoặc `CustomChunker` — vd chia theo Q&A pair/heading/điều khoản, theo yêu cầu K4 ít nhất 1 thành viên nhóm phải thử kiểu này)
- [ ] So sánh với baseline, ghi vào `REPORT_NHOM.md` Phần 2

### Bước 6 — Câu hỏi đánh giá (Bài 3.2, làm chung cả nhóm 1 lần) — CHƯA LÀM
- [ ] Thống nhất đúng 5 benchmark queries + gold answers
- [ ] Bắt buộc theo K4: ít nhất 1 câu cần `metadata_filter={"customer_role": "seller"|"buyer"}`
- [ ] Ghi vào `REPORT_NHOM.md` Phần 3

### Bước 7 — Dự đoán cosine similarity (Bài 3.3 — 5đ cá nhân) — CHƯA LÀM
- [ ] Chọn 5 cặp câu, dự đoán similarity cao/thấp trước
- [ ] Chạy `compute_similarity()` thật, so sánh với dự đoán, ghi phản ngẫm → `REPORT_CANHAN.md` Phần 4

### Bước 8 — Chạy benchmark & so sánh (Bài 3.4) — CHƯA LÀM
- [ ] Chạy 5 câu hỏi với chiến lược riêng, ghi top-3 kết quả mỗi câu
- [ ] So sánh trong nhóm: chiến lược nào tốt hơn, có đảo ngược giữa câu hỏi không, metadata filter có giúp không
- [ ] Ghi vào `REPORT_CANHAN.md` Phần 5 + `REPORT_NHOM.md` Phần 3

### Bước 9 — Phân tích lỗi (Bài 3.5) — CHƯA LÀM
- [ ] Tìm ít nhất 1 failure case, giải thích nguyên nhân (chunk sai kích thước/thiếu metadata/câu hỏi mơ hồ), đề xuất cải thiện
- [ ] Ghi vào `REPORT_NHOM.md` Phần 4

### Bước 10 — Hoàn thiện & nộp bài (làm cuối cùng) — CHƯA LÀM
- [x] `pytest tests/ -v` toàn bộ pass trong `Trinh_Hai_Dang_01602/` (42/42 — nhưng cần chạy lại lần cuối trước khi nộp)
- [ ] Rà lại `REPORT_CANHAN.md` đủ 5 phần, `REPORT_NHOM.md` đủ 4 phần
- [ ] Kiểm tra `data/` không chứa dữ liệu nhạy cảm/đăng nhập
- [x] Đảm bảo mọi thứ nằm trong `Trinh_Hai_Dang_01602/`

---

## 3. Checklist tổng (đối chiếu README/exercises)

- [x] Vượt tất cả test: `pytest tests/ -v` (42/42, cần re-check lần cuối sau khi thêm data/report)
- [x] `src/` hoàn thành TODO cá nhân
- [ ] `REPORT_NHOM.md` đầy đủ (1 file/nhóm)
- [ ] `REPORT_CANHAN.md` đầy đủ (1 file/sinh viên — của Đăng)
- [x] Toàn bộ code + báo cáo nằm trong `Trinh_Hai_Dang_01602/`

---

## 4. Đang làm tiếp theo (next action)

Việc tiếp theo cần làm: **Bước 2 + Bước 3 (report)** — viết `REPORT_CANHAN.md` Phần 1 (lý thuyết cosine + chunking math) và Phần 2 (giải thích hướng tiếp cận code), vì đây là phần không phụ thuộc dữ liệu nhóm và có thể hoàn thành ngay. Sau đó mới chuyển sang Bước 4 (thu thập 10 tài liệu K4).
