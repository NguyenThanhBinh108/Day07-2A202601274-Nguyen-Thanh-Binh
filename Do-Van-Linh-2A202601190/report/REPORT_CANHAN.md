
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

Agent gọi vector store để lấy top-k kết quả, có thể truyền thêm `metadata_filter` để dùng `search_with_filter()` khi câu hỏi cần lọc theo danh mục. Sau đó agent dựng prompt gồm câu hỏi và các đoạn ngữ cảnh được đánh số, kèm source và score, rồi gọi `llm_fn` để sinh câu trả lời dựa trên context đã truy xuất.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
================================================ test session starts ================================================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: D:\AI_In_Action\Day07\K4-Day07-2A202601190_DoVanLinh
plugins: anyio-4.14.2, hydra-core-1.3.2
collected 42 items                                                                                               

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                          [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                   [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                            [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                             [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                  [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                  [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                        [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                         [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                       [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                         [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                         [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                    [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                          [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                 [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                     [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED               [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                     [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                         [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                           [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                             [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                   [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                        [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                          [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED              [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                           [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                    [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                   [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                              [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                          [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                     [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                         [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                               [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                         [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED      [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                    [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                   [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED       [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                  [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED           [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED     [100%]

================================================ 42 passed in 0.09s =================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi chạy `compute_similarity()` trên vector normalized bag-of-words tự tạo từ 5 cặp câu. Cách này vẫn đơn giản hơn embedding model thật, nhưng phù hợp để quan sát cosine similarity vì các câu cùng chủ đề sẽ chia sẻ nhiều token hơn.

| Cặp | Câu A                                                             | Câu B                                                                    | Dự đoán | Điểm thực tế | Đúng? |
| ---- | ------------------------------------------------------------------ | ------------------------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | Khách hàng muốn trả hàng vì sản phẩm bị hư hỏng.        | Người mua yêu cầu hoàn tiền do hàng bị lỗi khi nhận.            | cao        | 0.4875           | Đúng  |
| 2    | Người dùng tìm kiếm sản phẩm trên Shopee.                  | Khách hàng nhập từ khóa để tìm món hàng cần mua.               | cao        | 0.5842           | Đúng  |
| 3    | Kho voucher lưu các mã giảm giá.                              | Tài khoản Lazada bị xóa vĩnh viễn sau thời gian chờ.              | thấp      | 0.0546           | Đúng  |
| 4    | SPayLater có các biện pháp bảo mật khi thanh toán.          | Người mua cần giữ an toàn thông tin khi dùng SPayLater.            | cao        | 0.4167           | Đúng  |
| 5    | Điều khoản mua bán quy định trách nhiệm của người bán. | Người bán có trách nhiệm tuân thủ quy định mua bán hàng hóa. | cao        | 0.8405           | Đúng  |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Cặp 5 có điểm cao nhất vì hai câu chia sẻ nhiều cụm từ quan trọng như "người bán", "trách nhiệm", "quy định", "mua bán". Cặp 3 thấp nhất vì hai câu thuộc hai chủ đề khác nhau, chỉ có rất ít từ chung; điều này cho thấy cosine similarity phụ thuộc mạnh vào cách biểu diễn vector.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Thiết lập cá nhân: dùng `SentenceChunker(max_sentences_per_chunk=2)`, embedding đơn giản dạng normalized bag-of-words để benchmark local, và gọi thật `KnowledgeBaseAgent.answer(..., metadata_filter={"category": ...})`. `llm_fn` là hàm extractive local: đọc prompt/context truy xuất được rồi sinh câu trả lời chỉ dựa trên context đó. Tổng số chunk sau ingest: 314.

| # | Câu hỏi (Query)                                                                                                                                                   | Top-1 Chunk truy xuất được (tóm tắt)                                                                                                 | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt)                                                                                                                                                                                                                  |
| - | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------ | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1 | Nếu hàng Shopee bị lỗi hoặc khác mô tả thì có được trả hàng hoàn tiền không?                                                                      | `k4-returns-policy`: đoạn "Điều kiện Trả hàng/Hoàn tiền", nêu nguyên tắc chung khi hàng có vấn đề.                      | 0.5531       | Có                               | Có. Theo ngữ cảnh truy xuất, Shopee cho phép gửi yêu cầu Trả hàng/Hoàn tiền khi hàng nhận được có vấn đề như khác mô tả hoặc hư hỏng; yêu cầu phải trong thời hạn Shopee quy định.                                  |
| 2 | Làm sao tìm kiếm sản phẩm cần mua trên Shopee?                                                                                                               | `k4-search-product`: hướng dẫn tìm sản phẩm bằng từ khóa/tên sản phẩm trên Shopee.                                          | 0.7044       | Có                               | Trên ứng dụng Shopee, người mua có thể dùng thanh tìm kiếm để nhập từ khóa liên quan, sau đó lọc/sắp xếp kết quả; cũng có thể tìm bằng hình ảnh để tìm sản phẩm tương tự.                                        |
| 3 | Kho voucher Shopee là gì và dùng để làm gì?                                                                                                                 | `k4-voucher`: định nghĩa Kho Voucher là nơi lưu voucher/mã giảm giá nhận hoặc mua trên Shopee.                               | 0.4734       | Có                               | Kho Voucher là nơi lưu các Voucher/Mã giảm giá người dùng nhận hoặc mua trên Shopee; người dùng có thể truy cập Kho Voucher để xem, lọc và sử dụng mã giảm giá.                                                            |
| 4 | Sử dụng SPayLater có an toàn không?                                                                                                                            | `k4-payment-security`: đoạn hỏi trực tiếp "Sử dụng SPayLater có an toàn không?" và giới thiệu nội dung an toàn/bảo mật. | 0.7673       | Có                               | Có. Ngữ cảnh cho biết thông tin đăng ký và sử dụng SPayLater được bảo mật, giao dịch cần xác minh bởi chính chủ; người dùng nên bảo mật thông tin đăng nhập và chỉ thao tác trong ứng dụng Shopee/ShopeePay.      |
| 5 | Trước khi gửi yêu cầu xóa tài khoản Lazada, cần kiểm tra trạng thái tài khoản, giao dịch đang diễn ra, số dư ví và LazPayLater như thế nào? | `k4-account-deletion`: đoạn mở đầu điều kiện xóa tài khoản và mục tài khoản ở trạng thái tốt.                         | 0.5839       | Có                               | Trước khi gửi yêu cầu xóa tài khoản Lazada, tài khoản cần ở trạng thái tốt, không có giao dịch/đơn hàng/tranh chấp đang xử lý, không còn số dư ví hoặc giao dịch chờ xử lý, và không còn nghĩa vụ LazPayLater. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5. Cả 5 câu đều có top-1 thuộc đúng tài liệu và đúng chủ đề cần trả lời.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

Tôi học được rằng metadata filter rất hữu ích khi bộ tài liệu cùng thuộc một miền rộng như TMĐT. Sau khi đổi sang `SentenceChunker(max_sentences_per_chunk=2)`, các chunk ngắn hơn và bám sát câu hỏi hơn, giúp top-1 rõ trọng tâm hơn so với cấu hình recursive ban đầu.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                  |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                  |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10                |
| **Tổng phần cá nhân**                      | **60 / 60**      |
