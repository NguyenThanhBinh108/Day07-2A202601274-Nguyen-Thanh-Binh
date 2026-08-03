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

### Bước 2 — Khởi động lý thuyết (Bài 1.1, 1.2 — 5đ) — ĐÃ XONG
- [x] Giải thích cosine similarity (khái niệm, ví dụ cao/thấp, vì sao ưu tiên hơn Euclidean) → `REPORT_CANHAN.md` Phần 1
- [x] Bài toán chunk: `ceil((10000-50)/(500-50))=23`, `overlap=100 → 25` — đã verify khớp `FixedSizeChunker` thật

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
- [x] Viết `REPORT_CANHAN.md` Phần 2 (hướng tiếp cận từng phần)

### Bước 4 — Chuẩn bị dữ liệu nhóm (song song với nhóm, Bài 3.0) — DỮ LIỆU XONG, REPORT CHƯA
- [x] Đọc `docs/DATA_COLLECTION.md` + `K4_VARIANT.md` (bắt buộc: `customer_role`, `source_url`, `retrieved_at`, `document_version`)
- [x] Phạm vi đã chọn: **1 nguồn duy nhất — Shopee (help.shopee.vn)**, kết hợp 3 mảng đổi trả + người bán + thanh toán/giao hàng (đã cân nhắc và loại phương án trộn nhiều sàn vì không nhất quán)
- [x] **Mở rộng vượt khung đề bài theo yêu cầu riêng của Đăng**: từ 10 → **20 tài liệu** (đề chỉ yêu cầu 5-10; 10 tài liệu thêm là để có kho dữ liệu phong phú hơn cho thử nghiệm cá nhân, không bắt buộc cho phần chấm điểm nhóm). 10 tài liệu ban đầu vào `data/k4_ecommerce/`, kèm `sources.csv` đủ 10 dòng:
  1. `return-refund-policy` (buyer) — Chính sách trả hàng và hoàn tiền
  2. `return-refund-general-rules` (buyer) — Quy định chung trả hàng/hoàn tiền
  3. `return-shipping-fee` (buyer) — Phương thức gửi hàng hoàn trả & phí hoàn trả
  4. `seller-listing-rules` (seller) — Quy định đăng bán sản phẩm
  5. `marketplace-operating-regulation` (both) — Quy chế hoạt động sàn TMĐT
  6. `restricted-products-policy` (seller) — Chính sách cấm/hạn chế sản phẩm
  7. `payment-methods` (buyer) — Các phương thức thanh toán
  8. `shipping-fee-discount-program` (seller) — Điều khoản ưu đãi phí vận chuyển
  9. `delivery-process` (buyer) — Quy trình giao hàng cho người mua
  10. `privacy-policy` (both) — Chính sách bảo mật
- [x] Đã verify nạp bằng `build_knowledge_base()` trong `ingest.py`: 10 doc → 31 chunk, metadata `customer_role`/`category` đầy đủ; `pytest tests/ -v` vẫn 42/42 pass
- [x] **Rà soát chuẩn hóa lần 2** theo đúng checklist `docs/DATA_COLLECTION.md`: đổi tên `returns-policy.md` → `return-refund-policy.md` và `seller-listing.md` → `seller-listing-rules.md` cho khớp `doc_id` (quy tắc "tên file nên trùng doc_id"); cập nhật `sources.csv` khớp 1-1; chuẩn hóa `license_or_permission` về đúng thuật ngữ ví dụ (`public-page`)
- [x] **Mở rộng lần 3 (theo yêu cầu)**: thêm **10 tài liệu mới**, cùng nguồn help.shopee.vn, mở rộng chủ đề (bảo hành, chống gian lận người bán, mã giảm giá/voucher, quy trình khiếu nại, điều khoản Shopee Mall, hướng dẫn COD, ShopeeVIP, chương trình bán hàng quốc tế, giao hàng tủ khóa) — không trùng lặp nội dung với 10 file đầu:
  1. `warranty-policy` (buyer) — Chính sách bảo hành sản phẩm
  2. `seller-anti-fraud-policy` (seller) — Chống gian lận & xử lý người bán vi phạm
  3. `voucher-discount-policy` (both) — Chính sách chung mã giảm giá
  4. `voucher-types` (buyer) — Các loại voucher trên Shopee
  5. `dispute-resolution-process` (both) — Quy trình giải quyết tranh chấp/khiếu nại
  6. `shopee-mall-terms` (seller) — Điều khoản dịch vụ Shopee Mall
  7. `cod-payment-guide` (buyer) — Hướng dẫn thanh toán COD
  8. `shopeevip-membership` (buyer) — Chương trình thành viên ShopeeVIP
  9. `global-selling-program` (seller) — Chương trình bán hàng toàn cầu
  10. `parcel-locker-delivery` (buyer) — Giao hàng qua tủ khóa
- [x] Verify toàn diện bộ **20 tài liệu**: `sources.csv` khớp 1-1 (20/20), tên file đúng chuẩn (chữ thường/không dấu/gạch ngang), `doc_id` duy nhất, đủ field bắt buộc cho cả 20 file, phân bổ `customer_role` cân đối (buyer=10, seller=6, both=4), 8 category khác nhau; nạp qua `build_knowledge_base()` → 62 chunk (bản tóm tắt ban đầu); `pytest tests/ -v` vẫn 42/42
- [x] **Thu thập lại toàn bộ 20 file bằng nội dung verbatim đầy đủ** (theo phản hồi: dữ liệu tóm tắt qua WebFetch quá sơ sài, ví dụ so sánh trực tiếp với nội dung `payment-methods` người dùng dán ra cho thấy WebFetch chỉ trả bản tóm tắt qua model nhỏ, mất rất nhiều chi tiết/con số):
  - Phát hiện: mỗi trang help.shopee.vn nhúng toàn bộ nội dung HTML gốc trong biến `window["FORGE_SSR_DATA_MAP"]` ngay trong SSR HTML — không cần qua WebFetch/model tóm tắt
  - Viết script Python (`curl`/`requests` + regex trích JSON + `html2text`) tải lại cả 20 URL, trích đúng nội dung đầy đủ theo đúng `article id`, tôn trọng rate-limit (~1.2s/request)
  - Tổng dung lượng tăng từ ~24.000 → **305.807 ký tự** (một số tài liệu là văn bản pháp lý đầy đủ: quy chế sàn 77.541 ký tự, chính sách bảo mật 42.987 ký tự, điều khoản Shopee Mall 33.464 ký tự)
  - Dọn dẹp artifact định dạng do `html2text` (dòng `**`/`__` thừa, khoảng trắng non-breaking, dòng trống thừa) bằng script, giữ nguyên front matter đã kiểm chứng (doc_id/customer_role/category/document_version), chỉ thay phần nội dung
  - Đối chiếu lại `document_version` với ngày "đăng tải/hiệu lực" tìm thấy trong toàn văn — phát hiện và sửa 1 lỗi ngày tháng do WebFetch tóm tắt sai trước đó (`voucher-discount-policy`: "14/11/2026" → đúng là "14/05/2026", ngày hiệu lực 23/05/2026 không đổi)
  - Verify lại: `build_knowledge_base()` → **1185 chunk** (chunk_size=300/overlap=40), `pytest tests/ -v` vẫn 42/42 sau khi thay toàn bộ nội dung
  - Re-run benchmark cá nhân (Bước 8) với dữ liệu đầy đủ: **5/5 câu đúng ngay top-1** (trước đó với dữ liệu tóm tắt: 4/5 top-1 + 1/5 top-2) — cập nhật đầy đủ vào `REPORT_CANHAN.md` Phần 5, kèm phân tích 3 lần chạy (mock/tóm tắt → local/tóm tắt → local/đầy đủ)
- [ ] Ghi bảng tài liệu vào `REPORT_NHOM.md` Phần 1 — còn lại

### Bước 5 — Thiết kế chiến lược cá nhân (Bài 3.1 — 15đ nhóm) — CHƯA LÀM
- [ ] Đặt `EMBEDDING_PROVIDER=local` trong `.env` (bắt buộc để so sánh có ý nghĩa, KHÔNG dùng mock)
- [ ] Chạy baseline: `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu, ghi kết quả
- [ ] Chọn 1 chiến lược riêng (built-in tuned hoặc `CustomChunker` — vd chia theo Q&A pair/heading/điều khoản, theo yêu cầu K4 ít nhất 1 thành viên nhóm phải thử kiểu này)
- [ ] So sánh với baseline, ghi vào `REPORT_NHOM.md` Phần 2

### Bước 6 — Câu hỏi đánh giá (Bài 3.2, làm chung cả nhóm 1 lần) — CHƯA LÀM
- [ ] Thống nhất đúng 5 benchmark queries + gold answers
- [ ] Bắt buộc theo K4: ít nhất 1 câu cần `metadata_filter={"customer_role": "seller"|"buyer"}`
- [ ] Ghi vào `REPORT_NHOM.md` Phần 3

### Bước 7 — Dự đoán cosine similarity (Bài 3.3 — 5đ cá nhân) — ĐÃ XONG
- [x] Chọn 5 cặp câu, dự đoán similarity cao/thấp trước
- [x] Cài `sentence-transformers` (local embedder, `requirements-local.txt`) và tải model `paraphrase-multilingual-MiniLM-L12-v2`
- [x] Chạy `compute_similarity()` với `LocalEmbedder` thật → **5/5 dự đoán đúng**, ghi vào `REPORT_CANHAN.md` Phần 4 kèm so sánh với lần chạy mock trước đó (4/5 sai) để minh họa vì sao không dùng mock đánh giá ngữ nghĩa

### Bước 8 — Chạy benchmark & so sánh (Bài 3.4) — PHẦN CÁ NHÂN ĐÃ XONG, PHẦN NHÓM CHƯA
- [x] Chạy 5 câu hỏi tự đề xuất (2 câu có `metadata_filter={"customer_role":"seller"}`, đúng yêu cầu K4) trên `FixedSizeChunker(300,40)` + `LocalEmbedder` thật, corpus 20 tài liệu (105 chunk) → **5/5 chunk liên quan trong top-3** (4/5 đúng top-1, 1/5 đúng top-2 do nhiễu ngữ nghĩa sau khi mở rộng corpus), ghi đầy đủ vào `REPORT_CANHAN.md` Phần 5 kèm bảng so sánh mock (0/5) vs local (5/5), và phát hiện thêm: `KnowledgeBaseAgent.answer()` hiện không hỗ trợ `metadata_filter` (đúng theo signature đề bài) — đã ghi rõ giới hạn này
- [ ] Thay bằng **5 câu hỏi chính thức của nhóm** khi họp chốt xong (Bước 6) — đối chiếu lại, dự kiến không đổi nhiều
- [ ] So sánh trong nhóm: chiến lược nào tốt hơn, có đảo ngược giữa câu hỏi không, metadata filter có giúp không
- [ ] Cập nhật `REPORT_NHOM.md` Phần 3 (đây là phần việc của nhóm, không phải cá nhân)

### Bước 9 — Phân tích lỗi (Bài 3.5) — ĐÃ XONG
- [x] Failure case thật tìm được khi so sánh `FixedSizeChunker` vs `ClauseChunker` (custom): câu hỏi 2 ("phương thức thanh toán") sai vì `ClauseChunker` không nhận diện heading Markdown `## N.` của riêng `payment-methods.md` (19/20 tài liệu khác dùng heading `**N. TIÊU ĐỀ**`), rơi về chia theo đoạn văn → 40 chunk rất nhỏ (72-176 ký tự) làm loãng kết quả; câu hỏi 4 sai vì chunk quá lớn (1500+ ký tự) từ văn bản luật dài lấn át chunk đúng trọng tâm từ tài liệu chuyên biệt hơn
- [x] Ghi đầy đủ vào `REPORT_NHOM.md` Mục 2 (so sánh chiến lược) và Mục 4 (bài học nhóm)

### Bước 10 — Hoàn thiện & nộp bài (làm cuối cùng) — GẦN XONG
- [x] `pytest tests/ -v` toàn bộ pass trong `Trinh_Hai_Dang_01602/` (42/42, re-check sau mọi thay đổi kể cả sau khi thêm `demo/`)
- [x] `REPORT_CANHAN.md` đủ 5 phần, `REPORT_NHOM.md` đủ 4 phần (Phần "Demo" của nhóm và tên 2 thành viên còn lại vẫn để trống — cần nhóm họp bổ sung)
- [x] Kiểm tra `data/` không chứa dữ liệu nhạy cảm/đăng nhập (chỉ trang chính sách công khai)
- [x] Đảm bảo mọi thứ nằm trong `Trinh_Hai_Dang_01602/`

### Bước 11 — Tài liệu thuyết trình + demo trực tiếp (bổ sung theo yêu cầu) — ĐÃ XONG
- [x] Viết `PRESENTATION.md` (tổng quan toàn bộ folder: kiến trúc, dữ liệu, kết quả, cách chạy demo) phục vụ thuyết trình
- [x] Thiết kế chiến lược tùy chỉnh `ClauseChunker` (chunk theo điều/khoản) — dùng cho cả `REPORT_NHOM.md` Mục 2 và demo trực tiếp
- [x] Xây `demo/` — giao diện web (Flask + HTML/CSS/JS, màu theo dataviz skill) gọi **pipeline Python thật** (không phải dữ liệu tĩnh): truy vấn trực tiếp, chọn chiến lược chunking, lọc `customer_role`, bảng benchmark 5 câu hỏi tính lại mỗi lần chạy
- [x] Test trực tiếp: khởi động server, gọi `/api/stats`, `/api/benchmark`, `/api/query` — tất cả trả kết quả đúng khớp báo cáo; dừng server test sau khi verify xong
- [x] `pytest tests/ -v` vẫn 42/42 sau khi thêm `demo/` (không đụng tới `src/` được chấm điểm)

---

## 3. Checklist tổng (đối chiếu README/exercises)

- [x] Vượt tất cả test: `pytest tests/ -v` (42/42)
- [x] `src/` hoàn thành TODO cá nhân
- [x] `REPORT_NHOM.md` đầy đủ 4 phần (còn thiếu tên/chiến lược của 2 thành viên khác — cần họp nhóm bổ sung)
- [x] `REPORT_CANHAN.md` đầy đủ (1 file/sinh viên — của Đăng)
- [x] Toàn bộ code + báo cáo nằm trong `Trinh_Hai_Dang_01602/`
- [x] Tài liệu thuyết trình (`PRESENTATION.md`) + demo trực tiếp (`demo/`)

---

## 4. Đang làm tiếp theo (next action)

**Phần cá nhân (60/60đ) và khung báo cáo nhóm đã hoàn thiện với số liệu thật**, kèm tài liệu thuyết trình và demo web chạy pipeline thật (đã test end-to-end). Việc còn lại thuộc phạm vi **họp nhóm thật với các thành viên khác** (không thể tự làm thay):
1. Các thành viên khác của B7-E402 điền chiến lược chunking riêng của họ vào `REPORT_NHOM.md` Mục 2 (đã có sẵn 1 chiến lược của Đăng + baseline làm mẫu).
2. Đối chiếu 5 câu hỏi benchmark hiện tại (tự đề xuất) với ý kiến cả nhóm, chốt chính thức nếu cần điều chỉnh.
3. Chạy `demo/server.py` trước buổi thuyết trình vài phút (mất ~1-2 phút tải model) để demo trực tiếp mượt mà, không phải chờ trên lớp.
4. Sau buổi demo: điền phần "bài học từ nhóm khác" còn bỏ trống trong cả 2 báo cáo.
