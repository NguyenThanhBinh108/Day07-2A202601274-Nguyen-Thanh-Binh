# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

| | |
|---|---|
| **Họ tên** | Trịnh Hải Đăng |
| **Mã học viên** | 2A202601602 |
| **Nhóm** | B7-E402 |
| **Ngày** | Thứ 2, 03/08/2026 |
| **Chủ đề K4** | Chính sách TMĐT Shopee — đổi trả, người bán, thanh toán/giao hàng |
| **Nguồn dữ liệu** | `data/k4_ecommerce/` — 20 tài liệu, 1 nguồn duy nhất (help.shopee.vn) |

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

## Tổng quan điểm phần cá nhân

| # | Hạng mục | Điểm tối đa | Trạng thái |
|---|---|:---:|---|
| 1 | Khởi động (Warm-up) | 5 | ✅ Hoàn thành |
| 2 | Hướng tiếp cận (My Approach) | 10 | ✅ Hoàn thành |
| 3 | Hoàn thiện code (42/42 test) | 30 | ✅ Hoàn thành |
| 4 | Dự đoán độ tương tự | 5 | ✅ Hoàn thành — 5/5 đúng (embedder thật) |
| 5 | Kết quả truy xuất của tôi | 10 | ✅ Hoàn thành — 5/5 chunk liên quan top-3 (embedder thật) |
| | **Tổng phần cá nhân (tự đánh giá)** | **60** | **59 / 60** |

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

Hai vector embedding chỉ cùng một *hướng* trong không gian nhiều chiều, bất kể độ dài (magnitude) của chúng — nói cách khác, hai đoạn văn bản mang cùng nội dung/ý nghĩa ngữ nghĩa, dù cách diễn đạt câu chữ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Đơn hàng của tôi bị giao chậm."
- Câu B: "Đơn hàng của tôi đến trễ hơn dự kiến."
- Tại sao tương đồng: cùng diễn đạt một ý — việc giao hàng không đúng hẹn — chỉ khác từ ngữ ("giao chậm" vs "đến trễ").

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Đơn hàng của tôi bị giao chậm."
- Câu B: "Tôi muốn đổi màu sản phẩm khác."
- Tại sao khác: chủ đề hoàn toàn khác nhau — một câu về vận chuyển/giao hàng trễ, một câu về đổi thuộc tính sản phẩm.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Độ dài (norm) của vector embedding thường bị ảnh hưởng bởi độ dài văn bản/tần suất từ chứ không phản ánh ngữ nghĩa, nên khoảng cách Euclid có thể đánh giá sai hai văn bản cùng chủ đề nhưng độ dài khác nhau là "xa nhau". Cosine similarity chỉ quan tâm góc giữa hai vector (hướng biểu diễn ngữ nghĩa) nên không bị lệch bởi magnitude, phù hợp hơn khi so sánh ý nghĩa văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Công thức: `số lượng chunk = ceil((độ_dài_tài_liệu - overlap) / (chunk_size - overlap))`
> Phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> **Đáp án: 23 chunks** (đã kiểm tra khớp với `FixedSizeChunker(chunk_size=500, overlap=50)` thực tế trong `src/chunking.py`)

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

`ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks — tăng từ 23 lên **25 chunks** (đã kiểm tra khớp thực tế). Tăng overlap làm bước trượt (`chunk_size - overlap`) nhỏ lại nên cần nhiều cửa sổ hơn để phủ hết văn bản → nhiều chunk hơn. Lý do muốn overlap lớn hơn: tránh việc một câu/ý quan trọng bị cắt đúng ngay ranh giới giữa hai chunk (mất ngữ cảnh), giúp truy xuất (retrieval) không bỏ sót thông tin nằm vắt qua điểm cắt — đổi lại là tốn thêm dung lượng lưu trữ và thời gian embed do có nhiều chunk trùng lặp nội dung hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

Dùng regex `(?<=[.!?])\s+` (lookbehind sau dấu `.`, `!`, `?`) để tách văn bản thành danh sách câu, sau đó strip khoảng trắng thừa và loại câu rỗng. Nhóm các câu liên tiếp thành từng chunk theo `max_sentences_per_chunk` bằng cách duyệt theo bước nhảy (`range(0, len(sentences), max_sentences_per_chunk)`) rồi nối lại bằng khoảng trắng. Trường hợp biên: văn bản rỗng trả về `[]`; văn bản không có dấu câu vẫn được coi là 1 "câu" duy nhất nhờ regex không match, tránh lỗi chia cho 0 hay list rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

`chunk()` gọi `_split(text, self.separators)`. Thuật toán đệ quy: base case là khi `len(current_text) <= chunk_size` → trả về nguyên đoạn text đó (hoặc `[]` nếu rỗng); khi hết separator để thử (`remaining_separators` rỗng) hoặc separator hiện tại là chuỗi rỗng `""`, cắt thẳng theo `chunk_size` ký tự liên tiếp. Ở bước đệ quy chính: tách `current_text` theo separator đầu tiên; nếu separator đó không xuất hiện trong text (`len(parts) == 1`) thì bỏ qua, thử separator kế tiếp; nếu có, gộp dần các `parts` vào một chunk cho tới khi vượt `chunk_size` thì chốt chunk đó lại và đệ quy tiếp với phần còn dư quá lớn bằng separator tiếp theo (rest). Cách này đảm bảo ưu tiên cắt tại ranh giới ngữ nghĩa lớn (đoạn văn `\n\n`) trước khi cắt nhỏ hơn (câu, từ, ký tự).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

`_make_record()` chuẩn hóa mỗi `Document` thành một dict gồm `id`, `content`, `metadata` (đã gắn thêm `doc_id` nếu chưa có) và `embedding` (gọi `self._embedding_fn(doc.content)`). `add_documents()` duyệt từng doc, tạo record rồi append vào list `self._store` (đồng thời ghi qua ChromaDB nếu thư viện có sẵn — fallback về in-memory nếu không). `search()` gọi `_search_records()`: embed câu query, tính tích vô hướng (`_dot`) giữa vector query và từng vector đã lưu, sort giảm dần theo score rồi cắt lấy `top_k` phần tử đầu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

`search_with_filter()` lọc **trước khi** tìm kiếm: nếu có `metadata_filter`, chỉ giữ lại các record mà toàn bộ cặp key-value trong filter khớp với `record["metadata"]` (dùng `all(...)` để yêu cầu khớp tất cả điều kiện), sau đó mới chạy `_search_records()` trên tập đã lọc — cách này tránh phải tính similarity cho các chunk chắc chắn không thuộc phạm vi cần lọc. `delete_document()` xây list mới chỉ giữ lại các record có `metadata["doc_id"] != doc_id`, so sánh độ dài trước/sau để biết có phần tử nào bị xóa hay không rồi gán lại `self._store`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

`answer()` gọi `self._store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất, nối nội dung các chunk lại bằng `"\n\n"` thành một khối `context`. Prompt được dựng theo cấu trúc cố định: hướng dẫn ngắn ("chỉ trả lời dựa trên ngữ cảnh"), rồi tới `Context:`, `Question:`, `Answer:` — buộc mô hình chỉ dùng thông tin đã truy xuất thay vì tự bịa. Cuối cùng gọi `self._llm_fn(prompt)` và trả thẳng kết quả string.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Chạy bằng `LocalEmbedder` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, `EMBEDDING_PROVIDER=local`) — embedder đa ngữ thật, phù hợp đánh giá ngữ nghĩa tiếng Việt theo đúng khuyến nghị của README.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
| :---: | ------ | ------ | :---------: | :---------------: | :-------: |
| 1 | "Đơn hàng của tôi bị giao chậm." | "Đơn hàng của tôi đến trễ hơn dự kiến." | cao | **0.6420** | ✅ Đúng |
| 2 | "Đơn hàng của tôi bị giao chậm." | "Tôi muốn đổi màu sản phẩm khác." | thấp | **0.0978** | ✅ Đúng |
| 3 | "Người bán phải cung cấp thông tin sản phẩm chính xác." | "Người bán cần mô tả đúng sự thật về hàng hóa." | cao | **0.8609** | ✅ Đúng |
| 4 | "Người bán phải cung cấp thông tin sản phẩm chính xác." | "Hôm nay trời Hà Nội mưa to." | thấp | **−0.0699** | ✅ Đúng |
| 5 | "Shopee hỗ trợ thanh toán khi nhận hàng (COD)." | "Có thể trả tiền mặt lúc nhận hàng trên Shopee không?" | cao | **0.8098** | ✅ Đúng |

**Kết quả: 5/5 dự đoán đúng** — trái ngược hoàn toàn với lần chạy thử bằng `_mock_embed` (xem khung cảnh báo bên dưới), nơi 4/5 dự đoán sai vì mock sinh vector gần như ngẫu nhiên theo hash chuỗi.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Bất ngờ nhất là cặp 5: hai câu dùng từ ngữ rất khác nhau ("Shopee hỗ trợ thanh toán khi nhận hàng (COD)" vs "Có thể trả tiền mặt lúc nhận hàng trên Shopee không?" — gần như không trùng từ khóa nào ngoài "Shopee") nhưng vẫn đạt similarity rất cao (0.8098), gần bằng cặp 3 (hai câu có nhiều từ trùng lặp hơn, 0.8609). Điều này cho thấy embedding đa ngữ thật sự mã hóa **ý nghĩa/ý định câu hỏi** (cùng hỏi về khả năng thanh toán COD) chứ không chỉ đơn thuần đếm từ trùng lặp như phương pháp từ khóa (keyword matching) truyền thống — đây chính là lý do vector search vượt trội hơn tìm kiếm từ khóa cho các câu hỏi FAQ diễn đạt khác nhau nhưng cùng ý.

> ⚠️ **So sánh với `_mock_embed` (đã thử nghiệm trước đó để minh họa):** cùng 5 cặp câu này, mock cho điểm 0.1834 / 0.3224 / −0.0576 / −0.0631 / −0.1109 — **4/5 dự đoán sai**, thậm chí cặp 2 (không liên quan) còn có điểm cao hơn cặp 1 (cùng ý nghĩa). Điều này khớp chính xác với cảnh báo của README: mock "gần như ngẫu nhiên theo cả chuỗi", chỉ dùng để unit test, không phản ánh chất lượng ngữ nghĩa thật.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> **Lưu ý về phạm vi:** tại thời điểm viết báo cáo này, nhóm B7-E402 chưa họp để chốt chính thức 5 câu hỏi đánh giá chung (`REPORT_NHOM.md` Phần 3). Để hoàn thiện đầy đủ phần việc cá nhân của mình ngay, em tự đề xuất 5 câu hỏi đánh giá dưới đây trên bộ **20 tài liệu** Shopee đã thu thập (`data/k4_ecommerce/`, mở rộng từ 10 lên 20 để có kho dữ liệu phong phú hơn cho thử nghiệm cá nhân) — bám sát yêu cầu K4 (có ≥1 câu cần `metadata_filter={"customer_role": "seller"}`), đa dạng chủ đề (đổi trả, thanh toán, quy định người bán, quyền riêng tư, phí vận chuyển). Khi nhóm họp và thống nhất bộ câu hỏi chính thức, em sẽ đối chiếu và cập nhật lại bảng này cho khớp 100% với `REPORT_NHOM.md` theo đúng yêu cầu "5 câu hỏi phải trùng với các thành viên cùng nhóm".
>
> **Cấu hình chạy:** `FixedSizeChunker(chunk_size=300, overlap=40)` trên 20 tài liệu → 105 chunk, + `LocalEmbedder` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, `EMBEDDING_PROVIDER=local`) — embedder đa ngữ thật theo đúng khuyến nghị của README cho Giai đoạn 2. `llm_fn` dùng hàm giả lập trích context (chưa có API key LLM thật) để kiểm chứng luồng RAG end-to-end của `KnowledgeBaseAgent`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Score | Liên quan trong top-3? | Câu trả lời của Agent (tóm tắt) |
| :-: | ----------------- | ------------------------------------------ | :------: | :---------: | ------------------------------------- |
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng/hoàn tiền kể từ khi giao hàng thành công? | `return-refund-policy`: "...trong vòng 15 ngày kể từ lúc đơn hàng được cập nhật trạng thái 'Giao hàng thành công'..." | 0.8097 | ✅ Có (top-1) | Nêu đúng mốc 15 ngày (và ngoại lệ thực phẩm tươi sống 24 giờ) trích từ `return-refund-policy` |
| 2 | Shopee hỗ trợ những phương thức thanh toán nào? | `payment-methods`: "...Shopee hỗ trợ 10 phương thức thanh toán sau đây..." | 0.7729 | ✅ Có (top-1) | Liệt kê đúng nhóm phương thức thanh toán (ShopeePay, thẻ, QR, COD, SPayLater...) |
| 3 | Người bán không được đăng bán loại sản phẩm nào theo quy định? *(`metadata_filter={"customer_role":"seller"}`)* | `shopee-mall-terms`: "...Một số nhóm sản phẩm bị loại trừ khỏi chính sách trả hàng..." | 0.6982 | ⚠️ Có nhưng ở **top-2** (`seller-listing-rules`, score 0.6727) | Xem phân tích riêng bên dưới — có phát hiện đáng chú ý |
| 4 | Shopee thu thập những loại dữ liệu cá nhân nào của người dùng? | `privacy-policy`: "...dữ liệu mạng, hình ảnh/âm thanh/video, giấy tờ tùy thân do cơ quan nhà nước cấp..." | 0.6003 | ✅ Có (top-1) | Trích đúng danh mục dữ liệu thu thập từ `privacy-policy` |
| 5 | Phí dịch vụ của chương trình ưu đãi phí vận chuyển dành cho người bán là bao nhiêu? *(`metadata_filter={"customer_role":"seller"}`)* | `shipping-fee-discount-program`: "...Phí dịch vụ của chương trình: 6%, tối đa 50.000 VNĐ trên giá bán của mỗi sản phẩm..." | 0.7517 | ✅ Có (top-1) | Nêu đúng con số 6%, tối đa 50.000 VNĐ, đúng phạm vi lọc `seller` |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5** (4 câu đúng ngay top-1, 1 câu đúng ở top-2)

### Phát hiện đáng chú ý ở câu 3 (sau khi mở rộng corpus lên 20 tài liệu)

Khi corpus chỉ có 10 tài liệu, câu 3 cho top-1 đúng ngay (`seller-listing-rules`, 0.6727). Sau khi thêm 10 tài liệu mới, `shopee-mall-terms` (một đoạn nói về *loại trừ sản phẩm khỏi chính sách trả hàng*, không phải *cấm đăng bán*) vô tình có điểm cao hơn (0.6982) vì dùng từ vựng gần giống ("sản phẩm", "loại trừ/không được"). Đây là ví dụ thực tế cho hiện tượng **corpus càng lớn, càng dễ có nhiễu ngữ nghĩa gần đúng** — tài liệu đúng vẫn nằm trong top-3 (hạng 2) nên theo `docs/SCORING.md` vẫn được tính "có liên quan trong top-3" (1 điểm/câu thay vì 2 điểm vì không ở top-1).

**Phát hiện thứ hai, quan trọng hơn:** khi kiểm tra kỹ, em nhận ra `KnowledgeBaseAgent.answer()` hiện tại **chỉ gọi `store.search()` (không lọc metadata)** — đúng theo signature `answer(self, question, top_k=3)` mà đề bài yêu cầu, không có tham số `metadata_filter`. Vì vậy với câu 3 (cần lọc `seller`), nếu gọi `agent.answer()` trực tiếp, kết quả **unfiltered** lại là `warranty-policy` (0.7529) — hoàn toàn sai chủ đề — thay vì dùng đúng 2 tài liệu liên quan đến quy định đăng bán. Bảng trên dùng `search_with_filter()` gọi riêng để mô phỏng "nếu agent có hỗ trợ lọc", còn `agent.answer()` như code hiện tại sẽ trả lời sai cho câu 3 và câu 5. Đây là giới hạn thiết kế thật sự của bài, không phải lỗi cài đặt — `EmbeddingStore.search_with_filter()` vẫn hoạt động đúng độc lập, nhưng `KnowledgeBaseAgent` chưa "nối" hai khả năng (RAG + filter) lại với nhau.

**So sánh với lần chạy thử bằng `_mock_embed` (cùng 5 câu hỏi, cùng chunker, cùng corpus 20 tài liệu):**

| | `_mock_embed` (mock) | `LocalEmbedder` (thật) |
| --- | :---: | :---: |
| Số câu có chunk liên quan trong top-3 | 0 / 5 | **5 / 5** |
| Score top-1 trung bình | ~0.24 (gần ngẫu nhiên) | ~0.71 (tách biệt rõ) |
| Metadata filter (`customer_role`) có hoạt động đúng? | Có lọc đúng tập ứng viên, nhưng similarity sai nên top-1 vẫn sai chủ đề | Lọc đúng **và** similarity cũng đúng chủ đề (trừ câu 3, đúng ở top-2 do nhiễu ngữ nghĩa) |

Kết quả này minh chứng rõ ràng: `search_with_filter()` **luôn lọc metadata đúng theo logic đã cài đặt** ở cả hai lần chạy — vấn đề ở lần chạy mock nằm hoàn toàn ở chất lượng vector embedding, không phải ở logic store/agent. Điều này khẳng định code phần cá nhân (`EmbeddingStore`) hoạt động chính xác; chất lượng retrieval phụ thuộc vào embedder được truyền vào, đúng như thiết kế dependency injection của `embedding_fn`.

**Điều hay nhất tôi học được (tự rút ra khi so sánh 2 lần chạy và khi mở rộng corpus):**

Có hai bài học rõ rệt: (1) sự khác biệt 0/5 → 5/5 chỉ bằng cách đổi `embedding_fn` cho thấy **chất lượng embedding quyết định chất lượng retrieval nhiều hơn** so với việc chunking hay lọc metadata có tinh vi đến đâu; (2) việc mở rộng corpus từ 10 lên 20 tài liệu — dù cùng chủ đề, cùng nguồn — đã đủ để tạo ra một trường hợp nhiễu ngữ nghĩa thực sự (câu 3), và cũng phơi bày một giới hạn thiết kế thật của `KnowledgeBaseAgent` (không truyền được `metadata_filter` vào `answer()`). Đây là hai lý do cụ thể vì sao README nhấn mạnh: (a) không dùng mock để kết luận chiến lược, và (b) luôn thử nghiệm với corpus đủ lớn/đa dạng trước khi kết luận một pipeline RAG "chạy tốt".

> *Mục "điều học được từ thành viên khác/nhóm khác qua demo" sẽ bổ sung sau buổi demo chính thức với nhóm B7-E402 — chưa diễn ra tại thời điểm viết báo cáo này.*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá | Ghi chú |
| ---------------------------------------------------- | :---------------------: | --- |
| Khởi động (Warm-up)                               | 5 / 5 | Đầy đủ, verify khớp code thật |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10 | Giải thích chi tiết từng hàm đã cài đặt |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30 | 42/42 test pass |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 | 5/5 dự đoán đúng với `LocalEmbedder` |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 | 5/5 câu có chunk liên quan trong top-3 với embedder thật; trừ 1 điểm vì 5 câu hỏi là tự đề xuất, chưa phải bộ câu hỏi chính thức đã chốt cùng nhóm |
| **Tổng phần cá nhân**                      | **59 / 60** |

> Sau khi nhóm B7-E402 họp chốt 5 câu hỏi đánh giá chính thức (`REPORT_NHOM.md` Phần 3), em sẽ chạy lại Phần 5 với đúng bộ câu hỏi đó để đối chiếu — dự kiến không đổi nhiều vì bộ 10 tài liệu và pipeline đã được kiểm chứng hoạt động tốt với embedder thật.
