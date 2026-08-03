# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đỗ Văn Linh - 2A202601190
**Nhóm:** K4 e-commerce
**Ngày:** 03/08/2026

> Số liệu trong báo cáo này được chạy lại trên đúng corpus chung: `D:\AI_In_Action\Day07\Day07-2A202601274-Nguyen-Thanh-Binh\data\k4_ecommerce`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)

**Độ tương tự cosine cao nghĩa là gì?**

Độ tương tự cosine cao nghĩa là hai vector có hướng gần nhau trong không gian embedding. Với văn bản, điều này thường cho thấy hai câu hoặc hai tài liệu có nội dung, ý định hoặc chủ đề ngữ nghĩa gần nhau.

**Ví dụ có độ tương tự cao:**

- Câu A: Khách hàng muốn trả hàng vì sản phẩm bị hư hỏng.
- Câu B: Người mua yêu cầu hoàn tiền do hàng bị lỗi khi nhận.
- Lý do: Cả hai câu cùng nói về tình huống hàng lỗi và nhu cầu trả hàng/hoàn tiền.

**Ví dụ có độ tương tự thấp:**

- Câu A: Ưu đãi phí vận chuyển áp dụng cho đơn hàng đủ điều kiện.
- Câu B: Cookie bên thứ ba được dùng cho phân tích và quảng cáo.
- Lý do: Hai câu thuộc hai chủ đề khác nhau: vận chuyển/khuyến mãi và quyền riêng tư/cookie.

**Vì sao cosine similarity thường phù hợp hơn Euclidean distance cho text embeddings?**

Cosine similarity tập trung vào hướng của vector nên đo tốt hơn mức gần nhau về ý nghĩa. Euclidean distance dễ bị ảnh hưởng bởi độ lớn vector hoặc độ dài văn bản, trong khi bài toán truy xuất văn bản thường cần so sánh ý nghĩa hơn là so sánh độ dài.

### Bài toán tính toán Chunking

Với tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:

- Bước nhảy: `500 - 50 = 450`
- Số chunk: `ceil((10000 - 50) / 450) = ceil(9950 / 450) = 23`

Nếu tăng overlap lên 100, bước nhảy còn `500 - 100 = 400`, số chunk là `ceil((10000 - 100) / 400) = 25`. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới chunk, nhưng làm tăng số chunk cần embed và lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`**

Tôi strip văn bản đầu vào, trả về danh sách rỗng nếu text rỗng, rồi dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách câu sau dấu `.`, `!`, `?`. Sau đó tôi gom tối đa `max_sentences_per_chunk` câu vào mỗi chunk, loại khoảng trắng thừa để chunk sạch và giữ được ranh giới câu.

**`RecursiveChunker.chunk` / `_split`**

Tôi dùng các separator theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`, nghĩa là ưu tiên tách theo đoạn, dòng, câu, từ rồi cuối cùng mới cắt cứng theo ký tự. Nếu một phần vẫn dài hơn `chunk_size`, hàm gọi đệ quy với separator tiếp theo.

### Lớp EmbeddingStore

**`add_documents` + `search`**

Mỗi `Document` được chuyển thành record gồm `id`, `document_id`, `content`, `metadata` và embedding. Store dùng in-memory list để ổn định cho unit test. Khi search, query được embed rồi tính dot product với từng record, sau đó sắp xếp giảm dần theo score.

**`search_with_filter` + `delete_document`**

`search_with_filter()` lọc metadata trước rồi mới tính similarity. `delete_document()` xóa toàn bộ chunk có `doc_id` hoặc `document_id` khớp với tài liệu cần xóa và trả về `True/False` theo việc có xóa được record nào hay không.

### Tác tử KnowledgeBaseAgent

`KnowledgeBaseAgent.answer()` lấy top-k chunk từ store, có hỗ trợ `metadata_filter`, dựng prompt gồm câu hỏi và context được đánh số, rồi gọi `llm_fn` để sinh câu trả lời dựa trên context truy xuất.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Lệnh chạy thật trong thư mục cá nhân:

```powershell
C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests\ -q
```

Kết quả:

```text
..........................................                               [100%]
42 passed in 0.08s
```

**Số lượng bài test vượt qua:** 42 / 42.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi chạy thật `compute_similarity()` trong `Do-Van-Linh-2A202601190\src\chunking.py` trên vector normalized bag-of-words tự tạo từ 5 cặp câu bám theo corpus `data\k4_ecommerce`.

| Cặp | Câu A                                                                                      | Câu B                                                                            | Dự đoán | Điểm thực tế | Đúng? |
| ---- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------- | ---------------: | ------- |
| 1    | Người mua có thể gửi yêu cầu trả hàng/hoàn tiền trong 15 ngày.                  | Khách hàng được yêu cầu hoàn tiền sau khi đơn hàng giao thành công. | Cao        |           0.7738 | Đúng  |
| 2    | Shopee hỗ trợ thanh toán khi nhận hàng và ví ShopeePay.                              | Người mua có thể chọn phương thức thanh toán phù hợp trên Shopee.     | Cao        |           0.5369 | Đúng  |
| 3    | Người bán không được đăng hàng giả hoặc sản phẩm vi phạm sở hữu trí tuệ. | Shop phải tuân thủ quy định đăng bán sản phẩm trên Shopee.             | Cao        |           0.6061 | Đúng  |
| 4    | Shopee thu thập dữ liệu cá nhân để xử lý giao dịch và chăm sóc khách hàng.   | Chính sách bảo mật mô tả mục đích sử dụng dữ liệu người dùng.     | Cao        |           0.6724 | Đúng  |
| 5    | Đơn vị vận chuyển giao hàng qua nhiều bước xử lý.                                | Trẻ em dưới 13 tuổi không thuộc đối tượng dịch vụ.                    | Thấp      |           0.1964 | Đúng  |

**Nhận xét:** Cặp 1 có điểm cao nhất vì cùng nói về trả hàng/hoàn tiền sau khi đơn hàng được giao. Cặp 5 thấp nhất vì hai câu thuộc hai mảng khác nhau của corpus: quy trình vận chuyển và điều khoản về trẻ em/quyền riêng tư.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Thiết lập chạy thật

- Corpus: `D:\AI_In_Action\Day07\Day07-2A202601274-Nguyen-Thanh-Binh\data\k4_ecommerce`
- Code dùng để chạy: `Do-Van-Linh-2A202601190\src`
- Chunker: `SentenceChunker(max_sentences_per_chunk=3)`
- Tổng số chunk sau ingest: 38
- Lệnh benchmark nhóm: `$env:EMBEDDING_PROVIDER='local'; python scripts\bench_ca_nhom.py`
- Backend thực tế trên máy khi chạy: `mock embeddings fallback`

`sentence_transformers` và `torch` chưa có trong môi trường Python hiện tại; lệnh cài `requirements-local.txt` bị timeout, nên `_select_embedder()` fallback sang `MockEmbedder`. Vì vậy bảng dưới đây ghi đúng kết quả tái lập được trên máy hiện tại, không dùng lại số liệu local chưa tái lập được.

| # | Câu hỏi nhóm                                                                                                                                                                   | Filter                         | Top-1 doc                      | Top-1 score | Hạng chunk chứa gold | Agent đúng? | Điểm |
| - | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ------------------------------ | ----------: | ---------------------- | ------------- | -----: |
| 1 | Đơn vị vận chuyển liên hệ người mua mấy lần để giao hàng, và nếu không liên hệ được thì người mua được yêu cầu giao lại trong thời hạn bao lâu? | Không                         | `voucher-discount-policy`    |      0.1799 | Trượt                | Không        |      0 |
| 2 | Tôi trả hàng bằng cách tự sắp xếp vận chuyển cho đơn khác tỉnh/thành thì Shopee hoàn lại phí vận chuyển hoàn trả bao nhiêu và bằng hình thức gì?     | Không                         | `seller-listing-rules`       |      0.3048 | Trượt                | Không        |      0 |
| 3 | Phí vận chuyển được tính và xử lý như thế nào?                                                                                                                       | `customer_role=seller`       | `seller-listing-rules`       |      0.2120 | Trượt                | Không        |      0 |
| 4 | Người bán có được đăng bán đồ cổ và tác phẩm nghệ thuật trên Shopee không, và nếu vi phạm chính sách sản phẩm cấm thì bị xử lý ra sao?            | `customer_role=seller`       | `restricted-products-policy` |      0.2271 | #1                     | Không        |      1 |
| 5 | Người mua gửi khiếu nại đơn hàng ở đâu trên ứng dụng và Shopee đưa ra quyết định trong bao lâu đối với khiếu nại thông thường?                       | `customer_role=[buyer,both]` | `return-shipping-fee`        |      0.2333 | Trượt                | Không        |      0 |

**Tổng điểm benchmark đo thật:** 1 / 10.

**Agent trả lời đúng:** 0 / 5.

**Câu trả lời thực tế của Agent:** cả 5 câu đều trả về `Không đọc được ngữ cảnh hoặc câu hỏi từ prompt.` khi dùng `llm_trich_xuat_chung` trong benchmark nhóm. Điều này cho thấy lỗi hiện tại không chỉ nằm ở retrieval mock mà còn ở tầng parser/extractive answer của hàm `llm_fn` khi đọc prompt do `KnowledgeBaseAgent` tạo ra.

**Bao nhiêu câu hỏi có gold answer trong top-3?** 1 / 5. Chỉ Q4 lấy được chunk chứa gold ở top-1; bốn câu còn lại trượt khỏi top-3.

**Điều học được:** Không được kết luận chất lượng chunking khi backend đang là `MockEmbedder`, vì mock dùng vector giả lập theo hash chuỗi nên kết quả retrieval gần như ngẫu nhiên. Muốn so sánh chiến lược thật sự cần cài được `sentence-transformers` và chạy lại với `EMBEDDING_PROVIDER=local`.

---

## Tự đánh giá phần cá nhân

| Tiêu chí                                                      | Điểm tự đánh giá |
| --------------------------------------------------------------- | ---------------------: |
| Khởi động (Warm-up)                                          |                  5 / 5 |
| Hướng tiếp cận của tôi (My Approach)                      |                10 / 10 |
| Hoàn thiện code (Core Implementation)                         |                30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions)            |                  5 / 5 |
| Kết quả truy xuất của tôi (Competition Results)            |                 1 / 10 |
| **Tổng phần cá nhân theo kết quả chạy hiện tại** |      **51 / 60** |
