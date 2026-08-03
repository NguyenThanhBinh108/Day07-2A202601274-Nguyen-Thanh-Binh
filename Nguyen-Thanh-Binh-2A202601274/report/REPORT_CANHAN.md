# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thanh Bình
**Mã sinh viên:** 2A202601274
**Nhóm:** [Điền tên nhóm]
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

**Môi trường chạy:** Python 3.11.9 (venv `.venv`, đúng chuẩn `.python-version`), pytest 9.1.1, Windows 11.
**Backend nhúng:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (`EMBEDDING_PROVIDER=local`) cho Mục 4 & 5; `MockEmbedder` cho 42 unit test. Mục 4 có kèm bảng đối chứng mock vs. local.
**Lệnh tái lập:**

```bash
py -3.11 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt          # pytest + dotenv
.venv/Scripts/python -m pip install -r requirements-local.txt    # embedder đa ngữ (Mục 4, 5)

.venv/Scripts/python -m pytest tests/ -v                   # Mục 3 — 42/42
.venv/Scripts/python scripts/edge_cases_check.py           # Mục 3 — kiểm chứng ngoài bộ test

# Mục 4 & 5 phải chạy với embedder thật (PowerShell):
$env:EMBEDDING_PROVIDER="local"
.venv/Scripts/python scripts/similarity_predictions.py     # Mục 4
.venv/Scripts/python scripts/retrieval_benchmark.py        # Mục 5 — chiến lược đã chọn
.venv/Scripts/python scripts/strategy_sweep.py             # Mục 5 — quét & chấm điểm 12 chiến lược
```

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Hai vector embedding **chỉ về gần cùng một hướng** trong không gian nhiều chiều, nghĩa là hai đoạn văn bản nói về cùng chủ đề / cùng ý, bất kể chúng dài ngắn khác nhau hay dùng từ khác nhau. Điểm nằm trong khoảng [-1, 1]: 1 là cùng hướng (gần như đồng nghĩa), 0 là không liên quan, -1 là ngược hướng hoàn toàn.

**Ví dụ có độ tương tự CAO:**

- Câu A: *"Người bán phải cung cấp mô tả sản phẩm chính xác."*
- Câu B: *"Thông tin sản phẩm do người bán đăng tải phải đúng sự thật."*
- Tại sao tương đồng: cùng một nghĩa vụ, cùng chủ thể (người bán) và cùng đối tượng (thông tin sản phẩm); chỉ đảo cấu trúc câu và thay bằng từ đồng nghĩa ("mô tả chính xác" ↔ "đúng sự thật"). Embedding mã hoá **ý**, không mã hoá mặt chữ, nên hai vector gần như trùng hướng.

**Ví dụ có độ tương tự THẤP:**

- Câu A: *"Chính sách đổi trả chỉ áp dụng cho hàng bị lỗi hoặc không đúng mô tả."*
- Câu B: *"Con mèo đang nằm ngủ trên mái nhà vào buổi trưa."*
- Tại sao khác: không chia sẻ chủ đề, chủ thể, lẫn trường từ vựng — một câu thuộc miền chính sách TMĐT, một câu tả cảnh sinh hoạt. Hai vector gần như trực giao nên điểm tiến về 0.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Vì **độ dài vector phản ánh độ dài / tần suất từ của văn bản, không phản ánh ý nghĩa**. Một đoạn 500 từ và một câu 10 từ nói cùng một điều sẽ có độ lớn vector rất khác nhau, khiến khoảng cách Euclid lớn dù nghĩa giống hệt; cosine chuẩn hoá độ lớn đi và chỉ so **hướng**, nên không bị chunk dài/ngắn đánh lừa. Ngoài ra cosine luôn bị chặn trong [-1, 1] nên có thể đặt ngưỡng dùng chung cho mọi corpus, còn khoảng cách Euclid không có trần và ở số chiều lớn thì các khoảng cách bị "co cụm" gần bằng nhau (curse of dimensionality), rất khó phân biệt tốt/nhiễu.
>
> *Ghi chú kỹ thuật từ chính code của tôi:* các embedder trong lab (`MockEmbedder`, `LocalEmbedder`) đều trả vector **đã chuẩn hoá L2**, nên `dot(a, b)` bằng đúng `cosine(a, b)`. Đó là lý do `EmbeddingStore.search()` xếp hạng bằng tích vô hướng mà vẫn tương đương xếp hạng theo cosine — tiết kiệm được 2 phép tính căn cho mỗi lần so sánh.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Trình bày phép tính:
>
> - Bước nhảy (step) giữa hai chunk liên tiếp = `chunk_size - overlap` = `500 - 50` = **450 ký tự**.
> - Chunk đầu tiên "tiêu thụ" trọn 500 ký tự; mỗi chunk sau đó chỉ thêm 450 ký tự mới.
> - `số chunk = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
>
> **Đáp án: 23 chunks.**
>
> *Đã kiểm chứng bằng chính `FixedSizeChunker` của tôi:*
>
> ```
> overlap=50    công thức=23   thực tế từ code=23   khớp=True
> overlap=100   công thức=25   thực tế từ code=25   khớp=True
> overlap=200   công thức=33   thực tế từ code=33   khớp=True
> ```

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Số chunk **tăng từ 23 lên 25** (`ceil(9900 / 400) = 25`, tăng ~8.7%): overlap càng lớn thì step càng nhỏ nên cần nhiều chunk hơn để phủ hết cùng một tài liệu. Ta chấp nhận trả giá đó để **không cắt đứt một câu / một ý ngay tại ranh giới chunk**: với overlap 100, mọi đoạn văn ngắn hơn 100 ký tự chắc chắn xuất hiện **nguyên vẹn trong ít nhất một chunk**, nhờ vậy câu trả lời nằm vắt qua ranh giới vẫn được truy xuất đủ ngữ cảnh (tăng recall). Mặt trái: nhiều chunk hơn ⇒ tốn chi phí nhúng và lưu trữ hơn, đồng thời nội dung lặp lại có thể chiếm nhiều suất trong top-k và đẩy chunk khác ra ngoài.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi dùng regex **`re.compile(r"(?<=[.!?])\s+")`** để cắt. Chọn *lookbehind* `(?<=...)` thay vì `split(". ")` vì lookbehind **giữ lại dấu chấm câu ở cuối câu trước**, nên chunk vẫn đọc tự nhiên; còn `\s+` phủ một lượt cả `". "`, `"! "`, `"? "` lẫn `".\n"` mà đề yêu cầu. Sau khi cắt, tôi `strip()` từng câu, **loại bỏ câu rỗng** rồi gom theo lô `max_sentences_per_chunk` bằng `range(0, len(sentences), size)`.
> Các edge case đã xử lý: text rỗng hoặc chỉ toàn khoảng trắng → trả `[]` (không trả `[""]`); text kết thúc bằng `". "` sinh ra phần tử rỗng ở cuối → đã lọc; text không có dấu kết câu nào → trả về đúng 1 chunk là cả đoạn; `max_sentences_per_chunk` bị truyền 0 hoặc số âm → constructor ép về tối thiểu 1 bằng `max(1, ...)`.
> Hạn chế tôi ý thức được: regex này cắt nhầm ở viết tắt kiểu "TP. HCM" hay "Dr. Smith". Với corpus chính sách TMĐT tiếng Việt thì hiếm gặp nên tôi chấp nhận đánh đổi để giữ hàm đơn giản.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> `chunk()` chỉ là lớp vỏ: kiểm tra text rỗng rồi gọi `self._split(text, self.separators)`. Toàn bộ thuật toán nằm ở `_split`, chạy theo tư tưởng "**ưu tiên cắt ở ranh giới ngữ nghĩa lớn nhất còn dùng được**": thử `"\n\n"` (đoạn văn) trước, không đủ nhỏ mới hạ xuống `"\n"`, rồi `". "`, rồi `" "`, cuối cùng là `""`.
> Sau khi cắt theo một separator, tôi **gom lại (greedy merge)** các mảnh liên tiếp vào một buffer chừng nào tổng độ dài còn `<= chunk_size` — bước này quan trọng, nếu thiếu thì mỗi câu sẽ thành một chunk riêng và chunk bị vụn quá mức. Mảnh nào tự nó đã dài hơn `chunk_size` thì **đệ quy xuống danh sách separator còn lại**.
> Có 2 base case: (1) `len(text) <= chunk_size` → trả về nguyên đoạn; (2) hết separator, hoặc separator hiện tại là `""` → gọi `_hard_split()` cắt cứng theo ký tự. Base case (2) là **lưới an toàn**: nó bảo đảm thuật toán luôn dừng kể cả khi gặp một "từ" dài 1000 ký tự không có chỗ nào để ngắt. Tôi cũng thêm nhánh `len(pieces) == 1` (separator không xuất hiện trong text) để **hạ ngay xuống separator tiếp theo** thay vì lặp vô ích.
> Đã stress-test: chuỗi toàn khoảng trắng, 1 từ dài 1000 ký tự, `separators=[]`, `separators=[""]`, separator không có trong text, text kết thúc bằng separator, và tiếng Việt có dấu — với `chunk_size` 10/50/400 đều **không lỗi, không chunk nào vượt `chunk_size`, không đệ quy vô hạn**.
>
> **Lỗi tôi tự phát hiện và sửa (bản đầu tiên đã pass đủ 42 test nhưng vẫn sai):** `str.split(separator)` **ăn mất separator**. Ở bản đầu tôi nối separator lại bằng `candidate = buffer + separator + piece`, nghĩa là separator chỉ được khôi phục **khi hai mảnh nằm chung một buffer**; mảnh nào bị chốt thành chunk riêng thì mất separator. Với separator `". "` điều đó có nghĩa là **dấu chấm cuối câu bị xoá ở mọi ranh giới chunk**:
>
> ```
> RecursiveChunker(chunk_size=4).chunk("aaa. bbb")  ->  ['aaa', 'bbb']   # mất dấu chấm
> ```
>
> Đo trên toàn bộ `data/`: **9 dấu chấm bị nuốt**, và mâu thuẫn nội bộ là `"! "`/`"? "` không nằm trong `DEFAULT_SEPARATORS` nên `"one! two"` lại giữ nguyên `!` — cùng một chunker mà hành xử khác nhau tuỳ dấu câu. Bộ test **không hề bắt được lỗi này** (cả 42 test đều pass ở cả hai bản), nên nó là ví dụ rõ ràng cho việc *pass test ≠ đúng*.
> Cách sửa: gắn separator trở lại **vào cuối mảnh đứng trước** ngay khi tách, rồi gộp thẳng `candidate = buffer + piece`:
>
> ```python
> pieces = [piece + separator for piece in raw_pieces[:-1]] + [raw_pieces[-1]]
> ```
>
> Sau khi sửa: **0/108 dấu chấm bị mất** trên toàn corpus, 42/42 test vẫn pass, không chunk nào vượt `chunk_size`. Việc này quan trọng với RAG vì chunk cụt dấu câu vừa khó đọc cho người kiểm chứng, vừa lệch phân phối so với dữ liệu mà mô hình nhúng được huấn luyện.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Tôi tách riêng một hàm `_make_record(doc)` để **chuẩn hoá** mỗi `Document` thành một bản ghi `{id, storage_id, content, embedding, metadata}`, nhúng luôn `content` tại thời điểm add (nhúng một lần, tái dùng cho mọi truy vấn về sau). Trong `_make_record` tôi gọi `metadata.setdefault("doc_id", doc.id)` — nhờ đó tài liệu do test tạo ra với `metadata={}` vẫn có `doc_id` để lọc và xoá, còn tài liệu do `ingest.py` tạo thì giữ nguyên `doc_id` sẵn có. Tôi cũng gán `storage_id = f"{doc.id}#{index}"` để **thêm trùng `doc.id` nhiều lần vẫn đếm đúng số chunk** (test `test_add_more_increases_further` thêm `doc0/doc1` hai lần và yêu cầu size = 5).
> `search()` uỷ quyền cho `_search_records(query, self._store, top_k)`: nhúng câu hỏi **một lần duy nhất**, tính `_dot(query_vec, record_vec)` cho từng bản ghi (vector đã chuẩn hoá nên dot = cosine), `sort(reverse=True)` rồi cắt `top_k`. Việc tách `_search_records` ra giúp `search()` và `search_with_filter()` dùng chung đúng một logic chấm điểm, không sợ hai đường lệch nhau.
> Về ChromaDB: `__init__` thử `import chromadb`, dùng `EphemeralClient` (hoặc `PersistentClient` nếu có `CHROMA_PERSIST_DIR`) và `get_or_create_collection`. Tôi cố ý **giữ `self._store` in-memory làm chỉ mục chấm điểm** và mirror dữ liệu sang Chroma, để hành vi (và điểm số) **giống hệt nhau dù máy chấm có hay không có chromadb**; mọi thao tác Chroma đều bọc `try/except`, lỗi thì tự hạ về in-memory chứ không làm mất dữ liệu.
> Hai chi tiết tôi phải xử lý thêm sau khi phát hiện vấn đề kiểu dữ liệu YAML ở trên: (1) Chroma **từ chối nguyên cả lô** nếu bất kỳ giá trị metadata nào không phải `str/int/float/bool` — mà `retrieved_at` lại là `datetime.date`, nên tôi thêm `_chroma_safe_metadata()` ép kiểu **chỉ khi ghi sang Chroma**, giữ nguyên bản gốc trong `self._store` để việc lọc không bị ảnh hưởng; (2) bản đầu nuốt lỗi hoàn toàn, khiến store âm thầm chạy in-memory mà không ai biết — nay đổi thành `warnings.warn` tường minh. Đã kiểm chứng bằng một `chromadb` giả **cố tình từ chối kiểu không vô hướng**: `_use_chroma=True`, size = 10 khớp in-memory, `delete_document()` xoá đúng, và chạy với `-W error::UserWarning` không phát sinh cảnh báo nào (tức là không hề rơi về in-memory).

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Tôi lọc **TRƯỚC rồi mới tìm kiếm** (pre-filter), không phải tìm xong mới lọc (post-filter). Lý do: nếu tìm top-k trước rồi lọc, một truy vấn có filter hẹp có thể trả về ít hơn `top_k` kết quả — thậm chí rỗng — dù trong kho vẫn còn chunk hợp lệ. Pre-filter bảo đảm `top_k` được lấy trên **đúng tập ứng viên hợp lệ**. Điều kiện lọc là AND trên mọi cặp key-value; khi `metadata_filter` là `None` hoặc rỗng thì tập ứng viên = toàn bộ store, nên kết quả trùng khớp `search()`.
>
> **Vấn đề thứ hai tôi phát hiện khi chạy thật:** bản đầu tôi so khớp bằng `record["metadata"].get(k) == v`. Nhưng `ingest.py` **dùng `pyyaml` nếu môi trường có**, và YAML tự suy kiểu — cùng một file `.md`, cùng một dòng `retrieved_at: 2026-08-02`, cho ra `str` khi máy không có pyyaml nhưng ra `datetime.date(2026, 8, 2)` khi có. Hệ quả: `metadata_filter={"retrieved_at": "2026-08-02"}` **âm thầm trả về rỗng** trên máy có pyyaml — kiểu lỗi rất khó truy vì không có exception nào, chỉ là "không tìm thấy gì". (Tôi gặp đúng tình huống này: cài `requirements-local.txt` kéo theo pyyaml và làm đổi kiểu dữ liệu metadata.)
> Cách xử lý: tách ra hàm `_matches(stored, wanted)` với 2 nới lỏng có chủ đích, vẫn **giữ `==` làm mặc định**: (1) nếu khác kiểu thì so tiếp bằng `str()`, để lọc theo ngày chạy đúng ở mọi môi trường; (2) nếu `wanted` là list thì kiểm tra thuộc tập — rất hợp với K4 vì `customer_role` có giá trị `both`, nên `{"customer_role": ["seller", "both"]}` mới lấy đủ tài liệu dùng chung thay vì bỏ sót. Đo thực tế trên corpus K4: lọc `retrieved_at="2026-08-02"` trả **3 chunk** sau khi sửa (trước khi sửa là **0**), lọc giá trị không tồn tại vẫn đúng **0 chunk**, và 42/42 test vẫn pass.
> `delete_document(doc_id)` lọc ngược danh sách, **giữ lại** các bản ghi có `metadata["doc_id"] != doc_id`, rồi so số lượng trước/sau để trả `True`/`False`. Cách này xoá **tất cả chunk** của một tài liệu chỉ trong một lượt duyệt, đúng ý đồ của `ingest.py` (mọi chunk đều mang `doc_id` của tài liệu gốc). Nếu Chroma đang bật thì đồng thời gọi `collection.delete(where={"doc_id": doc_id})`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> `__init__` chỉ lưu `self.store` và `self.llm_fn` (dependency injection — nhờ vậy test tiêm được LLM giả, còn tôi tiêm được LLM trích xuất khi chạy benchmark). `answer()` đi đúng 3 bước RAG: **truy xuất → dựng prompt → gọi LLM**.
> Prompt được đóng khuôn ở hằng `PROMPT_TEMPLATE` với 3 ràng buộc chống bịa (hallucination): *chỉ trả lời dựa trên ngữ cảnh*, *không đủ thông tin thì nói rõ là không tìm thấy*, *phải trích số hiệu đoạn đã dùng*. Ngữ cảnh được **đánh số `[1] [2] [3]` kèm nguồn (`source_url`/`doc_id`) và score** — chính nhờ đánh số này mà ở Mục 5 tôi chỉ ra được đoạn nào nuôi câu trả lời nào, tức là kiểm chứng được grounding chứ không chỉ đọc câu trả lời cho vui. Trường hợp store không trả về gì, tôi chèn câu ngữ cảnh rỗng tường minh thay vì đưa prompt trống cho LLM.
> **Một cải tiến tôi bổ sung sau khi chạy benchmark:** ban đầu `answer()` luôn gọi `store.search()`, nên ở câu hỏi số 3 (câu bắt buộc dùng metadata filter của K4) agent lấy nhầm ngữ cảnh từ tài liệu dành cho người mua và **trả lời sai hoàn toàn**. Tôi thêm tham số tuỳ chọn `metadata_filter=None`; khi có filter thì dùng `store.search_with_filter()`. Mặc định `None` nên không ảnh hưởng 42 test, mà câu 3 thì từ sai chuyển thành đúng (xem bảng Mục 5).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ .venv/Scripts/python -m pytest tests/ -v

============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Lab Vin AI\Day07-2A202601274-Nguyen-Thanh-Binh
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.09s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

Kiểm chứng bổ sung ngoài bộ test:

| Kiểm chứng                                              | Lệnh                                  | Kết quả                                                                                                                            |
| --------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Pipeline nạp dữ liệu chạy được với code của tôi | `python ingest.py`                   | `ingest self-check OK: parse được 4 khóa metadata, tạo 18 chunk`                                                              |
| Demo đầu-cuối (ingest → search → agent)              | `python main.py`                     | Chạy hết, in top-3 + câu trả lời của agent                                                                                     |
| Stress-test ca biên (ngoài 42 test)                     | `python scripts/edge_cases_check.py` | `TẤT CẢ KIỂM CHỨNG BIÊN ĐỀU ĐẠT` — 0 lỗi, 0 chunk vượt `chunk_size`, 0 đệ quy vô hạn, 0/108 dấu chấm bị mất |

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Dự đoán được ghi cứng trong `scripts/similarity_predictions.py` **trước khi chạy**, script chỉ tính điểm thật và đối chiếu.

**Backend:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (`EMBEDDING_PROVIDER=local`) — embedder đa ngữ thật, đúng yêu cầu đề bài.

| Cặp | Câu A                                                                                 | Câu B                                                                                      | Dự đoán                       | Điểm thực tế  | Đúng?                                   |
| ---- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------- | ----------------- | ----------------------------------------- |
| 1    | Người mua có thể trả lại hàng trong vòng 7 ngày kể từ khi nhận.            | Khách hàng được hoàn trả sản phẩm trong thời hạn một tuần sau khi nhận hàng. | **CAO**                    | **0.7623**  | ✅ Đúng                                 |
| 2    | Người bán phải cung cấp mô tả sản phẩm chính xác.                           | Thông tin sản phẩm do người bán đăng tải phải đúng sự thật.                   | **CAO**                    | **0.7823**  | ✅ Đúng (cao nhất bảng)               |
| 3    | Chính sách đổi trả chỉ áp dụng cho hàng bị lỗi hoặc không đúng mô tả. | Con mèo đang nằm ngủ trên mái nhà vào buổi trưa.                                  | **THẤP**                  | **-0.0705** | ✅ Đúng (thậm chí âm)                |
| 4    | Đơn hàng này được hoàn tiền.                                                  | Đơn hàng này không được hoàn tiền.                                                | **CAO** (bẫy phủ định) | **0.4768**  | ⚠️ Đúng một phần — xem phân tích |
| 5    | Phí vận chuyển được tính theo khối lượng đơn hàng.                        | Thời gian giao hàng dự kiến là 3-5 ngày làm việc.                                   | **TRUNG BÌNH**            | **0.3574**  | ✅ Đúng                                 |

Xếp hạng thực tế (cao → thấp): **cặp 2 (0.7823) > cặp 1 (0.7623) > cặp 4 (0.4768) > cặp 5 (0.3574) > cặp 3 (-0.0705)**. Tôi dự đoán đúng **4.5 / 5** cặp; chỉ sai ở mức độ của cặp 4.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Bất ngờ nhất là **cặp 4 — bẫy phủ định — chỉ đạt 0.4768 chứ không "gần như 1" như tôi đoán**. Hai câu chỉ khác nhau đúng một chữ "không" (trùng ~90% ký tự), vậy mà mô hình vẫn kéo điểm xuống hẳn **0.28–0.30 điểm** so với hai cặp diễn giải thật (0.76 và 0.78). Tức là mô hình đa ngữ này **có** nhận ra phủ định chứ không mù hoàn toàn như tôi tưởng — điều này tốt hơn kỳ vọng của tôi.
> **Nhưng kết luận nguy hiểm vẫn giữ nguyên, chỉ đổi độ lớn:** 0.4768 vẫn **cao hơn rất nhiều** so với cặp không liên quan (-0.0705) và còn cao hơn cả cặp cùng chủ đề khác khía cạnh (cặp 5, 0.3574). Đặt vào hệ thống thật: với câu hỏi *"Đơn hàng này có được hoàn tiền không?"*, một chunk nói *"KHÔNG được hoàn tiền"* vẫn thừa sức lọt top-3 và thậm chí đứng trên các chunk đúng chủ đề khác. Embedding sắp xếp theo **"nói về cùng chuyện gì"**, không theo **"khẳng định hay phủ định"** — nên không bao giờ được dùng riêng điểm similarity để kết luận, mà agent phải **trích nguyên văn chunk kèm số hiệu `[n]`** để người đọc tự đọc chữ "không" (đúng cách tôi thiết kế prompt ở Mục 2).
> Quan sát thứ hai: cặp 3 ra điểm **âm** (-0.0705), tức là hai vector còn "quá cả trực giao". Với embedding chuẩn hoá, điểm âm là tín hiệu rất mạnh cho việc *không liên quan*, có thể dùng làm ngưỡng chặn: nếu top-1 mà score < 0 thì nên để agent trả lời "không tìm thấy trong tài liệu" thay vì cố sinh câu trả lời.

**Đối chứng mock vs. local — bằng chứng cụ thể cho cảnh báo trong README:**

| Cặp                               | Mock (`MockEmbedder`)              | Local (MiniLM đa ngữ) | Nhận xét                                                  |
| ---------------------------------- | ------------------------------------ | ----------------------- | ----------------------------------------------------------- |
| 1 (đồng nghĩa)                  | 0.0752 —**thấp nhất bảng** | **0.7623**        | Mock xếp cặp đồng nghĩa xuống đáy                   |
| 3 (không liên quan)              | 0.0801 —**cao hơn cặp 1**   | **-0.0705**       | Mock xếp "con mèo ngủ"**trên** cặp đồng nghĩa |
| 5 (cùng miền, khác khía cạnh) | 0.2304 —**cao nhất bảng**   | 0.3574                  | Mock đảo lộn hoàn toàn thứ tự                        |

Toàn bộ 5 cặp chạy mock nằm gọn trong dải hẹp **0.07–0.23** và thứ tự gần như ngẫu nhiên, vì `MockEmbedder` chỉ băm MD5 chuỗi rồi sinh vector bằng bộ sinh số tuyến tính — đổi một ký tự là ra vector không liên quan. Với embedder thật, dải điểm giãn ra **-0.07 → 0.78** và thứ tự khớp trực giác ngữ nghĩa. Đây là lý do rất cụ thể để **không bao giờ kết luận chiến lược chunking bằng mock**.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Cấu hình của tôi:** corpus chung `data/k4_ecommerce/` (**10 tài liệu chính sách Shopee, 108 chunk**) · chiến lược **`ClauseChunker(max_sentences_per_clause=1)`** — chunker tuỳ chỉnh tôi tự viết cho K4 · `top_k=3` · embedder `paraphrase-multilingual-MiniLM-L12-v2` · LLM là `llm_trich_xuat` (hàm trích xuất tất định, chỉ lấy câu **trong ngữ cảnh đã truy xuất**, có trọng số theo thứ hạng, luôn kèm số hiệu đoạn `[n]` — repo không có API key nên đây là cách trung thực nhất để kiểm chứng grounding mà không bịa).

**Lệnh tái lập:** `$env:EMBEDDING_PROVIDER="local"; python bench.py`

| # | Câu hỏi (Query) | Top-1 chunk truy xuất được | Score | Có liên quan không? | Câu trả lời của Agent | Điểm |
|---|---|---|---|---|---|---|
| 1 | Đơn vị vận chuyển liên hệ mấy lần, người mua được yêu cầu giao lại trong bao lâu? | `delivery-process` — đúng đoạn chứa đáp án | **0.7962** | ✅ **Gold ở #1** | "…yêu cầu giao lại trong vòng không quá 5 ngày kể từ lần liên hệ đầu tiên. **[1]**" ✅ đúng | **2** |
| 2 | Tự sắp xếp vận chuyển trả hàng khác tỉnh thì được hoàn bao nhiêu, bằng hình thức gì? | `return-shipping-fee` — đúng tài liệu nhưng là đoạn tổng quát | **0.8653** | ⚠️ Đúng tài liệu, **gold ở #2** | "Người mua tự sắp xếp vận chuyển và trả phí trước; Shopee sẽ hoàn phí lại sau. **[1]**" ❌ **thiếu mức 25.000/40.000 Xu** | **1** |
| 3 | Phí vận chuyển được tính và xử lý như thế nào? *(lọc `customer_role=seller`)* | `shipping-fee-discount-program` — đúng đoạn | **0.6924** | ✅ **Gold ở #1** | "Phí dịch vụ của chương trình: 6%, tối đa 50.000 VNĐ trên giá bán của mỗi sản phẩm. **[1]**" ✅ đúng | **2** |
| 4 | Có được đăng bán đồ cổ không, vi phạm bị xử lý ra sao? | `seller-listing-rules` — **SAI TÀI LIỆU** | **0.7690** | ❌ Top-1 sai tài liệu, **gold ở #2** | "…gỡ sản phẩm, tạm khóa/khóa vĩnh viễn tài khoản… **[1]**" ❌ **không trả lời được phần "đồ cổ"** | **1** |
| 5 | Khiếu nại ở đâu, Shopee quyết trong bao lâu? | `marketplace-operating-regulation` — đúng đoạn | **0.7573** | ✅ **Gold ở #1** | "…quyết định trong vòng 7 ngày làm việc đối với khiếu nại thông thường… **[1]**" ✅ đúng | **2** |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5** — trong đó **3/5 đứng top-1**.

Tự chấm theo `docs/SCORING.md`: **2 + 1 + 2 + 1 + 2 = 8 / 10**.

### Chấm ở mức CHUNK, không chỉ doc_id

Tôi khai báo cho mỗi câu một `gold_snippet` — cụm trích **nguyên văn** từ corpus — và đã `grep` xác minh mỗi cụm chỉ khớp **đúng 1 tài liệu**. Việc chấm dựa trên "chunk có chứa cụm đó không", không phải "doc_id có xuất hiện không".

Khác biệt giữa hai cách chấm chính là phát hiện đáng giá nhất của tôi. Ở **Q2**, cả 3 slot top-3 đều thuộc đúng tài liệu gold `return-shipping-fee`, nên chấm theo `doc_id` sẽ tính là **thành công tuyệt đối**. Nhưng chunk #1 chỉ nói *"Người mua tự sắp xếp vận chuyển và trả phí trước; Shopee sẽ hoàn phí lại sau"* — **không có con số nào**, trong khi câu hỏi hỏi thẳng "bao nhiêu". Agent vì thế trả lời đúng chủ đề nhưng **vô dụng**. Đúng như đề bài cảnh báo: *"một strategy hoàn toàn có thể chiếm trọn cả ba slot bằng đúng tài liệu gold mà không chunk nào chứa câu trả lời"*.

Score cũng không cứu được: Q2 có **score cao nhất trong cả 5 câu (0.8653)** nhưng lại là một trong hai câu bị mất điểm. **Score cao là tín hiệu xếp hạng, không phải bằng chứng nội dung đúng.**

### So sánh 12 cấu hình chiến lược (chạy bằng `scripts/strategy_sweep.py`)

Số trong ô là **thứ hạng của chunk chứa gold answer**; cột "Agent" đếm số câu agent trả lời có chứa nguyên văn gold.

| Chiến lược | #chunk | Q1 | Q2 | Q3 | Q4 | Q5 | Agent | Điểm |
|---|---|---|---|---|---|---|---|---|
| **`ClauseChunker(1 câu)`** ← chọn | 108 | #1 | #2 | #1 | **#2** | #1 | 3/5 | **8/10** |
| `ClauseChunker(2 câu)` | 95 | #1 | #2 | #1 | **#2** | #1 | 3/5 | **8/10** |
| `FixedSizeChunker(500,50)` | 32 | #1 | #1 | #1 | **trượt** | #1 | 3/5 | 7/10 |
| `RecursiveChunker(400)` | 45 | #1 | #1 | #1 | **trượt** | #1 | 3/5 | 7/10 |
| `SentenceChunker(3 câu)` | 38 | #1 | #2 | #1 | trượt | #1 | 2/5 | 6/10 |
| `SentenceChunker(2 câu)` | 51 | #1 | #2 | #1 | trượt | #1 | 2/5 | 6/10 |
| `RecursiveChunker(200)` | 94 | #1 | trượt | #3 | trượt | #2 | 1/5 | 4/10 |
| `FixedSizeChunker(200,40)` | 79 | #2 | trượt | trượt | trượt | #1 | 1/5 | 3/10 |
| `SentenceChunker(1 câu)` | 99 | #3 | #3 | #3 | trượt | #2 | 0/5 | 4/10 |
| `ClauseChunker(1, **bỏ tiêu đề**)` | 108 | #3 | #3 | #2 | trượt | #2 | 0/5 | **4/10** |
| `RecursiveChunker(120)` | 144 | trượt | trượt | trượt | trượt | #2 | 0/5 | 1/10 |

Bốn điều rút ra:

1. **Điểm phân biệt duy nhất giữa 8/10 và 7/10 là Q4.** Ba chunker có sẵn cho thứ hạng đẹp hơn ở Q2 (#1 thay vì #2) nhưng **trượt hẳn Q4 khỏi top-3**. `ClauseChunker` đánh đổi một bậc thứ hạng để với được câu mà các chiến lược kia không chạm tới — recall đổi lấy precision, và ở rubric này recall thắng vì trượt top-3 bị **0 điểm** còn lệch thứ hạng vẫn được **1 điểm**.

2. **Tiền tố tiêu đề là yếu tố sống còn.** Ablation bỏ tiêu đề khiến **cùng một chunker, cùng 108 chunk** rơi từ **8/10 xuống 4/10** (agent sai cả 5, mọi câu tụt hạng). Câu đơn lẻ tách khỏi tài liệu thì mất hết ngữ cảnh. Đề bài cũng nêu đúng chi tiết này: *"khi cắt nhỏ một section dài, nên gắn lại tiêu đề vào từng mảnh con"*.

3. **Mịn hơn không phải tốt hơn.** `RecursiveChunker(120)` mịn nhất (144 chunk) nhưng **tệ nhất, 1/10**. Điều quyết định không phải kích thước chunk mà là **cắt có tôn trọng ranh giới ngữ nghĩa hay không**: cắt theo ký tự xé câu làm đôi, cắt theo điều khoản thì không.

4. **Agent mới là nút thắt, không phải retrieval.** Mọi chiến lược tốt đều đưa được chunk liên quan vào top-3 ở 4–5 câu, nhưng **không cấu hình nào cho agent trả lời đúng quá 3/5**. Trần điểm hiện nằm ở tầng sinh câu trả lời chứ không phải tầng truy xuất.

### A/B metadata filter (câu 3 — câu bắt buộc của K4)

| Câu 3 | Top-3 tài liệu trả về | Hạng chunk chứa gold |
|---|---|---|
| **CÓ** `metadata_filter={"customer_role":"seller"}` | `shipping-fee-discount-program × 3` | **#1** ✅ |
| **KHÔNG** filter | `return-shipping-fee`, `shipping-fee-discount-program`, `shipping-fee-discount-program` | **#2** |

Câu hỏi *"Phí vận chuyển được tính và xử lý như thế nào?"* **cố tình không nêu người hỏi là ai**, trong khi corpus có hai tài liệu cùng chủ đề "phí vận chuyển" nhưng khác đối tượng và **khác đáp án**:

- `return-shipping-fee` (`customer_role: buyer`) — hoàn 25.000 / 40.000 Shopee Xu
- `shipping-fee-discount-program` (`customer_role: seller`) — phí dịch vụ 6%, tối đa 50.000 VNĐ

Không lọc thì **top-1 rơi vào tài liệu người mua** và agent trả lời sai đối tượng; bật filter thì cả 3 slot đều là tài liệu người bán, gold lên #1 và agent trả lời đúng. Đây là bằng chứng trực tiếp cho giá trị của `customer_role` — trường metadata bắt buộc của K4.

> **Tôi đã phải thiết kế lại câu 3.** Bản đầu hỏi *"Gian hàng cần đáp ứng điều kiện gì để tham gia chương trình ưu đãi phí vận chuyển?"*. Câu đó nêu thẳng chữ "gian hàng" nên embedding tự khoá vào tài liệu người bán, và A/B cho kết quả **giống hệt nhau dù có hay không filter** — tức filter hoàn toàn vô dụng, không chứng minh được gì. Một câu hỏi chỉ thực sự "cần filter" khi nó **mơ hồ về đối tượng**, còn corpus thì có hai đáp án khác nhau cho hai đối tượng.

### Phân tích lỗi (failure case)

**1. Q4 — câu hỏi hai vế làm truy xuất bị xé đôi giữa hai tài liệu.** Câu hỏi gồm hai phần: *"có được bán đồ cổ không"* + *"vi phạm bị xử lý ra sao"*. Top-1 (score 0.7690) lại là `seller-listing-rules` — **sai tài liệu** — vì đoạn *"Vi phạm các quy định trên có thể dẫn đến: gỡ sản phẩm, tạm khóa/khóa vĩnh viễn tài khoản…"* khớp rất mạnh với **vế thứ hai**. Tài liệu đúng `restricted-products-policy` (chứa "Đồ cổ và tác phẩm nghệ thuật chưa được cấp phép") bị đẩy xuống #2. Agent vì thế trả lời được phần chế tài nhưng **không trả lời được phần đồ cổ**.
*Đề xuất:* tách câu hỏi hai vế thành hai truy vấn rồi hợp kết quả, hoặc thêm `metadata_filter={"category": "seller-policy"}` để thu hẹp — nhưng lưu ý cả hai tài liệu đều thuộc `seller-policy` nên filter này **không cứu được**, cần metadata mịn hơn ở mức chủ đề.

**2. Q2 — đúng tài liệu, sai đoạn, và score cao nhất bảng.** Đã phân tích ở trên. Nguyên nhân sâu xa: `ClauseChunker` cắt mỗi câu thành một chunk, nên câu nêu *phương thức* và câu nêu *số tiền* nằm ở hai chunk khác nhau; câu hỏi lại chứa cả hai ý nên chunk "phương thức" thắng về độ giống tổng thể.
*Đề xuất:* cho `ClauseChunker` gộp 2–3 câu liền kề có **overlap** để số liệu và ngữ cảnh cùng nằm trong một chunk. Biến thể `ClauseChunker(2 câu)` đã thử vẫn ra 8/10 nên cần overlap thật, không chỉ tăng số câu.

**3. Q4 bị cả 3 chunker có sẵn trượt hoàn toàn khỏi top-3.** "Đồ cổ và tác phẩm nghệ thuật" chỉ là **một dòng trong danh sách 20 nhóm hàng cấm**. Chunk 400–500 ký tự nuốt trọn cả danh sách, vector bị trung bình hoá trên 20 chủ đề khác nhau nên không khớp riêng "đồ cổ". Chỉ khi mỗi mục thành một chunk thì dòng đó mới có vector riêng.
*Bài học tổng quát:* **danh sách liệt kê phải được cắt theo từng mục**, không thể gộp khối — đây là lý do cấu trúc để chọn chunker theo điều/khoản cho văn bản chính sách.

> ⚠️ **Giới hạn:** 5 câu hỏi là mẫu nhỏ; chênh lệch giữa 8/10 và 7/10 chỉ đến từ **một câu duy nhất (Q4)**, nên kết luận "ClauseChunker tốt hơn" cần thêm câu hỏi mới thật vững. Ngược lại, ablation bỏ tiêu đề (8 → 4, agent sai cả 5) thì đủ mạnh để kết luận chắc chắn.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(Điền sau buổi demo.)*

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá | Căn cứ                                                                                                         |
| ---------------------------------------------------- | ---------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Khởi động (Warm-up)                               | 5 / 5                  | Giải thích đủ 3 ý cosine + bài toán chunking có kiểm chứng bằng code (23 chunks, khớp công thức)   |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                | Giải thích đủ 5 nhóm hàm, kèm 2 lỗi tự phát hiện & sửa mà 42 test không bắt được               |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                | 42/42 pass +`ingest.py`, `main.py`, `edge_cases_check.py` đều chạy sạch                                |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                  | Dự đoán ghi cứng trước khi chạy, đúng 4.5/5, có phân tích bẫy phủ định + đối chứng mock/local |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10                 | Đo thật trên corpus chung 10 tài liệu: 2+1+2+1+2 = 8 (`python bench.py`)                                            |
| **Tổng phần cá nhân**                      | **58 / 60**      |                                                                                                                  |

**Lý do tự trừ 2 điểm:** hai câu Q2 và Q4 chỉ đạt 1/2 — truy xuất đưa được chunk liên quan vào top-3 nhưng chunk đứng #1 không chứa đáp án, nên agent trả lời thiếu số liệu (Q2) hoặc lệch vế câu hỏi (Q4). Cả hai đều là hạn chế **có thể sửa được** bằng chunk có overlap và tách câu hỏi hai vế, đã phân tích trong phần failure case.

> **Ghi chú về tính trung thực của số liệu:** bản báo cáo trước ghi 10/10, nhưng con số đó đo trên corpus tạm chỉ có 2 tài liệu mẫu. Khi nhóm đưa corpus thật 10 tài liệu vào, điểm giảm còn **8/10** — đúng như phần cảnh báo overfit tôi đã tự ghi lúc đó. Toàn bộ số liệu hiện tại đo trên corpus chung, embedder đa ngữ thật, và tái lập được bằng một lệnh `python bench.py`.

> 📌 **Ghi chú cho báo cáo nhóm:** `ClauseChunker` (mã nguồn trong `src/chunking.py`) là **chiến lược riêng của tôi** cho Bài tập 3.1 — cần chép mã + phần lý do thiết kế sang `REPORT_NHOM.md` mục 2 (Thiết kế chiến lược, 15 điểm). Nó cũng thoả yêu cầu bắt buộc của K4: *"Ít nhất một thành viên thử chia nhỏ theo điều/khoản, tiêu đề (heading) hoặc cặp FAQ."*
