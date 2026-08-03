# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đỗ Văn Linh - 2A202601190
**Nhóm:** K4 e-commerce
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau trong không gian vector. Với văn bản, điều này thường cho thấy hai câu/tài liệu có nội dung hoặc ý định ngữ nghĩa gần giống nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: Khách hàng muốn trả hàng vì sản phẩm bị hư hỏng.
- Câu B: Người mua yêu cầu hoàn tiền do hàng bị lỗi khi nhận.
- Tại sao tương đồng: Cả hai câu đều nói về tình huống hàng lỗi và nhu cầu trả hàng/hoàn tiền.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Kho voucher lưu các mã giảm giá của người mua.
- Câu B: Tài khoản Lazada bị xóa vĩnh viễn sau thời gian chờ.
- Tại sao khác: Hai câu thuộc hai chủ đề khác nhau: voucher/khuyến mãi và xóa tài khoản.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Cosine similarity tập trung vào hướng của vector nên phù hợp hơn để đo mức gần nhau về ý nghĩa giữa các văn bản. Euclidean distance dễ bị ảnh hưởng bởi độ lớn vector, độ dài văn bản hoặc số lượng từ, trong khi retrieval thường cần so sánh ý nghĩa hơn là độ dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

Kích thước bước nhảy là `500 - 50 = 450` ký tự.

Số chunk = `ceil((10000 - 50) / 450) = ceil(9950 / 450) = 23`.

**Đáp án:** 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

Khi overlap tăng lên 100, bước nhảy còn `500 - 100 = 400` ký tự nên số chunk = `ceil((10000 - 100) / 400) = ceil(9900 / 400) = 25`. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới giữa hai chunk, nhưng làm tăng số chunk cần embed và lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

Tôi strip văn bản đầu vào, trả về danh sách rỗng nếu text rỗng, rồi dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách câu sau dấu `.`, `!`, `?` và khoảng trắng hoặc xuống dòng. Sau đó tôi gom tối đa `max_sentences_per_chunk` câu vào mỗi chunk, loại bỏ khoảng trắng thừa để chunk trả về sạch hơn.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

Tôi dùng danh sách separator theo mức ưu tiên `["\n\n", "\n", ". ", " ", ""]`, nghĩa là ưu tiên tách theo đoạn, dòng, câu, từ rồi cuối cùng mới cắt cứng theo ký tự. Base case là text rỗng hoặc text đã ngắn hơn/equal `chunk_size`; nếu một phần vẫn quá dài thì hàm gọi đệ quy với separator tiếp theo.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

Mỗi `Document` được chuyển thành một record gồm `id`, `document_id`, `content`, `metadata` và vector embedding. Store hiện dùng in-memory list để kết quả test ổn định; khi search, query được embed rồi tính dot product với từng record và sắp xếp giảm dần theo score.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

Tôi lọc metadata trước rồi mới tính similarity để giảm ứng viên sai chủ đề. Hàm xóa dùng `doc_id` trong metadata hoặc `document_id` của record để loại bỏ toàn bộ chunk thuộc cùng một tài liệu, sau đó trả về `True/False` theo việc có xóa được record nào hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

Agent gọi vector store để lấy top-k kết quả, sau đó dựng prompt gồm câu hỏi và các đoạn ngữ cảnh được đánh số, kèm source và score. Prompt yêu cầu LLM chỉ trả lời dựa trên context đã truy xuất; nếu không có context thì nói rằng chưa đủ thông tin.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
Command:
C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/ -v

Result:
collected 42 items
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::* PASSED
tests/test_solution.py::TestSentenceChunker::* PASSED
tests/test_solution.py::TestRecursiveChunker::* PASSED
tests/test_solution.py::TestEmbeddingStore::* PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::* PASSED
tests/test_solution.py::TestComputeSimilarity::* PASSED
tests/test_solution.py::TestCompareChunkingStrategies::* PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::* PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::* PASSED

============================= 42 passed in 0.07s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi chạy `compute_similarity()` trên vector tạo bởi `_mock_embed` mặc định của repo. Vì `_mock_embed` là mock embedding deterministic để phục vụ test, điểm số không phản ánh ngữ nghĩa tốt như embedding model thật; phần này dùng để quan sát cách cosine hoạt động và thấy giới hạn của mock embedding.

| Cặp | Câu A                                                             | Câu B                                                            | Dự đoán | Điểm thực tế | Đúng?           |
| ---- | ------------------------------------------------------------------ | ----------------------------------------------------------------- | ---------- | ---------------- | ----------------- |
| 1    | Khách hàng muốn trả hàng vì sản phẩm bị hư hỏng.        | Người mua yêu cầu hoàn tiền do hàng bị lỗi khi nhận.    | cao        | -0.1120          | Sai               |
| 2    | Người dùng tìm kiếm sản phẩm trên Shopee.                  | Khách hàng nhập từ khóa để tìm món hàng cần mua.       | cao        | 0.2435           | Đúng            |
| 3    | Kho voucher lưu các mã giảm giá.                              | Tài khoản Lazada bị xóa vĩnh viễn sau thời gian chờ.      | thấp      | -0.0033          | Đúng            |
| 4    | SPayLater có các biện pháp bảo mật khi thanh toán.          | Người mua cần giữ an toàn thông tin khi dùng trả sau.     | cao        | 0.1797           | Đúng một phần |
| 5    | Điều khoản mua bán quy định trách nhiệm của người bán. | Chính sách bảo hành áp dụng cho sản phẩm mua tại Shopee. | thấp      | 0.2686           | Sai               |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Cặp 1 bất ngờ nhất vì hai câu gần nghĩa nhưng điểm lại âm. Điều này cho thấy mock embedding trong repo chỉ phù hợp để test pipeline ổn định, chưa phải embedding ngữ nghĩa thật; khi dùng model semantic tốt hơn, tôi kỳ vọng cặp 1 và 2 sẽ có điểm cao hơn rõ rệt.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Thiết lập cá nhân: dùng `RecursiveChunker(chunk_size=900)`, embedding đơn giản dạng normalized bag-of-words để benchmark local, và `search_with_filter(..., metadata_filter={"category": ...})`. Tổng số chunk sau ingest: 166. `KnowledgeBaseAgent.answer()` hiện chưa nhận metadata filter trực tiếp, nên tôi đánh giá retrieval bằng store rồi tóm tắt câu trả lời dựa trên top-3 chunk truy xuất được.

| # | Câu hỏi (Query)                                                                              | Top-1 Chunk truy xuất được (tóm tắt)                                                                                                                               | Điểm Score | Có liên quan không? (Relevant)       | Câu trả lời của Agent (tóm tắt)                                                                                                         |
| - | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | Nếu hàng Shopee bị lỗi hoặc khác mô tả thì có được trả hàng hoàn tiền không? | `k4-returns-policy`: top-1 nói về hoàn mã/voucher khi Trả hàng/Hoàn tiền; top-2/top-3 chứa điều kiện và lý do trả hàng như hàng lỗi, khác mô tả. | 0.0652       | Có trong top-3, top-1 lệch một phần | Có thể gửi yêu cầu Trả hàng/Hoàn tiền nếu sản phẩm lỗi, hư hỏng hoặc khác mô tả trong thời hạn Shopee quy định.        |
| 2 | Làm sao tìm kiếm sản phẩm cần mua trên Shopee?                                          | `k4-search-product`: hướng dẫn tìm sản phẩm bằng từ khóa/tên sản phẩm trên Shopee.                                                                        | 0.0580       | Có                                     | Người mua có thể nhập từ khóa liên quan đến sản phẩm cần mua để Shopee hiển thị kết quả phù hợp.                         |
| 3 | Kho voucher Shopee là gì và dùng để làm gì?                                            | `k4-voucher`: Kho Voucher trên Shopee và nơi lưu/tìm mã giảm giá.                                                                                              | 0.2629       | Có                                     | Kho Voucher là nơi người dùng xem, lưu và sử dụng các mã giảm giá hợp lệ khi mua hàng.                                        |
| 4 | Sử dụng SPayLater có an toàn không?                                                       | `k4-payment-security`: nội dung Shopee về an toàn khi dùng SPayLater.                                                                                              | 0.1955       | Có                                     | SPayLater có cơ chế bảo mật, nhưng người dùng vẫn cần bảo vệ thông tin tài khoản và giao dịch.                              |
| 5 | Trước khi gửi Yêu Cầu Xóa Tài Khoản Lazada cần đáp ứng điều kiện gì?           | `k4-account-deletion`: đoạn điều kiện về lần xóa gần nhất, không có giao dịch đang diễn ra, không có số dư ví/giao dịch chờ xử lý.             | 0.0652       | Có                                     | Tài khoản cần ở trạng thái tốt, không có giao dịch/tranh chấp đang xử lý, không còn số dư ví hoặc nghĩa vụ LazPayLater. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5. Trong đó 4 câu có top-1 trực tiếp tốt, câu 1 có top-1 cùng tài liệu nhưng chưa đúng trọng tâm bằng top-2/top-3.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

Tôi học được rằng metadata filter rất hữu ích khi bộ tài liệu cùng thuộc một miền rộng như TMĐT. Tuy vậy, filter chỉ giúp chọn đúng nhóm tài liệu; để top-1 đúng ý hơn vẫn cần embedding tốt hơn hoặc chunking giữ các mục điều kiện thành đoạn mạch lạc hơn.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                  |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                |
| Dự đoán độ tương tự (Similarity Predictions) | 3 / 5                  |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10                |
| **Tổng phần cá nhân**                      | **58 / 60**      |
