# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Bazoka
**Thành viên:** Nguyễn Thanh Bình (2A202601274) · Trần Chí Vũ (2A202601044) · Trịnh Hải Đăng (2A202601602) · Đỗ Văn Linh (2A202601190) · Đỗ Thu Liễu (2A202601898)
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng.

**Phạm vi cụ thể nhóm tập trung:**

> Chính sách vận hành sàn Shopee nhìn từ **hai phía** — nghĩa vụ của người mua (đổi trả, hoàn phí, giao hàng, thanh toán) và nghĩa vụ của người bán (đăng bán, hàng cấm, phí dịch vụ). Chọn hai phía có chủ đích để trường `customer_role` thực sự phân biệt được tài liệu, nếu không thì query có filter sẽ không chứng minh được gì.

### Danh sách tài liệu (Data Inventory)

Corpus dùng chung: `data/k4_ecommerce/` — **10 tài liệu**, toàn bộ lấy từ trang trợ giúp công khai của Shopee, ngày lấy 03/08/2026.

| #  | doc_id                               | Tên tài liệu                                           | customer_role | category      | Số ký tự |
| -- | ------------------------------------ | --------------------------------------------------------- | ------------- | ------------- | ----------- |
| 1  | `return-refund-policy`             | Chính sách trả hàng và hoàn tiền                   | buyer         | returns       | 1.490       |
| 2  | `return-shipping-fee`              | Phương thức gửi hàng hoàn trả và phí hoàn trả  | buyer         | returns       | 836         |
| 3  | `payment-methods`                  | Các phương thức thanh toán Shopee hỗ trợ           | buyer         | payment       | 946         |
| 4  | `delivery-process`                 | Đơn vị vận chuyển giao hàng như thế nào          | buyer         | shipping      | 1.095       |
| 5  | `seller-listing-rules`             | Quy định về đăng bán sản phẩm                     | seller        | seller-policy | 1.094       |
| 6  | `restricted-products-policy`       | Chính sách cấm/hạn chế sản phẩm                    | seller        | seller-policy | 1.189       |
| 7  | `shipping-fee-discount-program`    | Điều khoản chương trình ưu đãi phí vận chuyển | seller        | shipping      | 1.113       |
| 8  | `marketplace-operating-regulation` | Quy chế hoạt động sàn Shopee.vn                      | both          | seller-policy | 1.259       |
| 9  | `privacy-policy`                   | Chính sách bảo mật                                    | both          | privacy       | 1.887       |
| 10 | `voucher-discount-policy`          | Chính sách voucher và ưu đãi giảm giá             | both          | promotion     | 1.447       |

Nguồn đầy đủ (URL gốc, ngày lấy, phiên bản, căn cứ sử dụng) trong `data/k4_ecommerce/sources.csv`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [X] Tập tài liệu chỉ chứa **trang trợ giúp công khai của Shopee**, không có dữ liệu cá nhân, thông tin đăng nhập hay tài liệu nội bộ. Không đăng nhập, không vượt CAPTCHA, không crawl toàn website.
- [X] Mỗi tài liệu có `source_url`, `retrieved_at` (2026-08-03), `document_version` trong metadata; `sources.csv` khớp **một–một** với 10 file.

**Kết quả CHECKPOINT 2** (`python scripts/kiem_tra_corpus.py`):

```
10/10 file OK   |   so file: 10 (can 5-10)   |   csv: khop
customer_role : {'buyer': 4, 'seller': 3, 'both': 3}
```

Hai việc nhóm đã phải sửa để đạt checkpoint:

1. **Đổi tên 2 file cho khớp `doc_id`** — script chấm của đề so `doc_id` với tên file, `returns-policy.md` (doc_id `return-refund-policy`) và `seller-listing.md` (doc_id `seller-listing-rules`) bị báo `THIEU METADATA` dù metadata đủ. Đã đổi tên file và cập nhật `file_path` trong `sources.csv`.
2. **Thay toàn bộ dữ liệu khởi động** — 2 file mẫu của repo còn `source_url: https://example.com/...` và câu *"Nhóm phải bổ sung nguồn chính sách công khai"*, không dùng để chấm được.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata    | Kiểu | Ví dụ giá trị                                                          | Tại sao hữu ích cho truy xuất?                                                                                                                                                                                                                                 |
| -------------------- | ----- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `doc_id`           | str   | `return-shipping-fee`                                                    | Khoá truy vết: mọi chunk đều mang`doc_id` của file gốc, nhờ đó `delete_document()` xoá đúng và câu trả lời chỉ được về đúng nguồn                                                                                                     |
| `customer_role`    | str   | `buyer` / `seller` / `both`                                          | **Trường bắt buộc của K4.** Corpus có hai tài liệu cùng chủ đề "phí vận chuyển" nhưng khác đối tượng và **khác đáp án**; không có trường này thì câu hỏi mơ hồ sẽ trả lời sai đối tượng (xem A/B ở Mục 3) |
| `category`         | str   | `returns` / `seller-policy` / `shipping` / `payment` / `privacy` | Thu hẹp theo chủ đề khi`customer_role` chưa đủ — 3 tài liệu `seller-policy` vẫn cạnh tranh nhau ở câu hỏi về hàng cấm                                                                                                                        |
| `source_url`       | str   | `https://help.shopee.vn/...`                                             | Truy vết nguồn khi agent trả lời; agent in kèm URL trong ngữ cảnh đánh số`[n]`                                                                                                                                                                         |
| `retrieved_at`     | date  | `2026-08-03`                                                             | Kiểm tra độ mới của chính sách — chính sách TMĐT thay đổi thường xuyên                                                                                                                                                                             |
| `document_version` | str   | `2026.1` / `not-stated`                                                | Phân biệt phiên bản chính sách khi cùng một trang được cập nhật                                                                                                                                                                                       |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=400)` trên 3 tài liệu (đã bỏ front matter, chỉ đo phần thân):

| Tài liệu                                | Chiến lược    | Số chunk | Độ dài TB | Giữ được ngữ cảnh không?                                                |
| ----------------------------------------- | ---------------- | --------- | ------------ | ------------------------------------------------------------------------------ |
| `return-refund-policy` (1.490 ký tự)  | `fixed_size`   | 5         | 330,0        | Không — cắt giữa câu, mốc "15 ngày" và điều kiện đi kèm bị tách |
|                                           | `by_sentences` | 4         | 370,3        | Có — mỗi chunk trọn câu                                                   |
|                                           | `recursive`    | 7         | 211,3        | Có — cắt ở ranh giới đoạn trước                                       |
| `restricted-products-policy` (1.189)    | `fixed_size`   | 4         | 327,3        | Không — danh sách 20 nhóm hàng cấm bị cắt ngang                        |
|                                           | `by_sentences` | 2         | 593,0        | Kém — 2 chunk quá to, gộp nhiều nhóm hàng vào một vector              |
|                                           | `recursive`    | 4         | 296,3        | Trung bình                                                                    |
| `shipping-fee-discount-program` (1.113) | `fixed_size`   | 3         | 397,7        | Không                                                                         |
|                                           | `by_sentences` | 4         | 275,8        | Có                                                                            |
|                                           | `recursive`    | 4         | 276,8        | Có                                                                            |

Tổng số chunk trên toàn corpus 10 tài liệu:

| Chiến lược                 | Số chunk |
| ----------------------------- | --------- |
| `FixedSizeChunker(500, 50)` | 32        |
| `SentenceChunker(3 câu)`   | 38        |
| `RecursiveChunker(400)`     | 45        |
| `ClauseChunker(1 câu)`     | 108       |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Thanh Bình (2A202601274)**

- **Loại chiến lược:** Custom — `ClauseChunker(max_sentences_per_clause=1)`, chia theo **điều/khoản + gắn tiêu đề**
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản chính sách TMĐT được biên soạn theo mục, và trong mỗi mục **mỗi câu thường là một nghĩa vụ độc lập gắn với một chủ thể**. Ba chunker có sẵn đều cắt theo độ dài hoặc số câu cố định nên hay gộp nghĩa vụ của người mua và người bán vào chung một chunk, khiến vector bị trung bình hoá và agent trích nhầm câu. `ClauseChunker` cắt tại ranh giới cấu trúc đầu dòng (tiêu đề `#`, gạch đầu dòng, khoản đánh số, dòng trống, khối `>`), rồi **gắn tiêu đề gần nhất làm tiền tố** để mỗi chunk tự đủ nghĩa khi bị lấy ra khỏi tài liệu.
- **Kết quả:** **8/10** — cao nhất trong 12 cấu hình đã quét. Điểm mạnh quyết định là Q4 (hàng cấm): ba chunker có sẵn đều **trượt khỏi top-3**, chỉ `ClauseChunker` với được ở #2, vì "đồ cổ và tác phẩm nghệ thuật" chỉ là một dòng trong danh sách 20 nhóm hàng cấm — chunk 400–500 ký tự nuốt trọn cả danh sách làm vector bị trung bình hoá trên 20 chủ đề.
- **Code snippet:**

```python
class ClauseChunker:
    _HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
    _BULLET  = re.compile(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+)")
    _QUOTE   = re.compile(r"^\s{0,3}>")
    _SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

    def chunk(self, text):
        # 1) cắt tại ranh giới CẤU TRÚC đầu dòng, nhớ tiêu đề gần nhất
        # 2) trong mỗi khối, tách câu và gom tối đa max_sentences_per_clause câu
        # 3) gắn tiêu đề làm tiền tố -> chunk tự đủ nghĩa
        return [f"{heading}: {body}" for heading, body in ...]
```

> Mã đầy đủ trong `src/chunking.py`.

> **Cách lấy số liệu cho 4 khối dưới đây:** chạy `python scripts/bench_ca_nhom.py` với
> `EMBEDDING_PROVIDER=local`. Script nạp **đúng gói `src/` của từng thành viên** (chunker,
> `EmbeddingStore`, `KnowledgeBaseAgent` đều là code của người đó), trên **cùng corpus và
> cùng 5 câu hỏi**. Cấu hình chiến lược là **bản tạm do nhóm phân công** để có số đối chiếu —
> **mỗi thành viên tự xác nhận hoặc đổi tham số của mình, rồi tự viết phần lý do thiết kế.**

**Thành viên 2 — Trần Chí Vũ (2A202601044)**

- **Loại chiến lược:** `RecursiveChunker(chunk_size=400)` — separator mặc định `["\n\n", "\n", ". ", " ", ""]`
- **Mô tả & lý do chọn:** Văn bản chính sách Shopee được biên soạn theo **đoạn văn**, mỗi đoạn thường trọn một nhóm quy định. `RecursiveChunker` thử separator theo thứ tự `"\n\n"` → `"\n"` → `". "` → `" "` → `""`, tức **ưu tiên cắt đúng ranh giới đoạn trước**, chỉ hạ xuống mức nhỏ hơn khi đoạn vẫn dài quá ngưỡng. Chọn `chunk_size=400` vì đo trên corpus thấy đa số đoạn nằm trong khoảng 200–400 ký tự, nên phần lớn đoạn được giữ nguyên vẹn thay vì bị ghép hoặc xé. Đây là chiến lược "an toàn": không bao giờ cắt giữa câu như `FixedSize`, nhưng cũng không mịn tới mức làm vụn ý như cắt theo từng câu.
- **Kết quả benchmark (đo thật):** **7/10** · 43 chunk · thứ hạng `#1 #1 #1 trượt #1` · agent đúng 3/5
- **Nhận xét từ số liệu:** đứng thứ 2 toàn nhóm. Cắt theo ranh giới đoạn giúp giữ trọn câu nên Q2 lên được #1 (Bình chỉ #2), nhưng **trượt Q4** vì chunk ~400 ký tự nuốt trọn danh sách 20 nhóm hàng cấm.

**Thành viên 3 — Trịnh Hải Đăng (2A202601602)**

- **Loại chiến lược:** `FixedSizeChunker(chunk_size=500, overlap=50)`
- **Mô tả & lý do chọn:** Đây là **đường cơ sở (baseline)** của cả nhóm — chiến lược đơn giản nhất, chi phí thấp nhất và dễ dự đoán nhất: mọi chunk đều đúng 500 ký tự, số chunk tính được trước bằng công thức `ceil((L - overlap) / (chunk_size - overlap))`. Chọn `overlap=50` (10%) để mọi cụm thông tin ngắn hơn 50 ký tự chắc chắn xuất hiện **nguyên vẹn trong ít nhất một chunk**, tránh mất thông tin nằm vắt qua ranh giới. Giá trị của chiến lược này không nằm ở điểm số mà ở chỗ nó cho nhóm một mốc để đo: mọi chiến lược phức tạp hơn phải chứng minh được là **hơn baseline này**, nếu không thì độ phức tạp thêm vào là vô ích.
- **Kết quả benchmark (đo thật):** **6/10** · 32 chunk · thứ hạng `#1 #1 #1 trượt #1` · agent đúng 2/5
- **Nhận xét từ số liệu:** thứ hạng truy xuất ngang Vũ nhưng agent kém hơn 1 câu. Ít chunk nhất nhóm (32) nên mỗi chunk chứa nhiều chủ đề, vector bị trung bình hoá.
- ⚠️ Bản báo cáo cá nhân hiện tại của Đăng chạy bằng `_mock_embed` nên chỉ được 0/5 — **không phải do code sai**, cần chạy lại với `EMBEDDING_PROVIDER=local`.

**Thành viên 4 — Đỗ Văn Linh (2A202601190)**

- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=3)`
- **Mô tả & lý do chọn:** Giả thuyết kiểm chứng ở đây là: **chunk không bao giờ được cắt giữa câu**. `SentenceChunker` tách tại ranh giới `[.!?]` rồi gom đúng 3 câu một chunk, nên mọi chunk luôn là những câu trọn vẹn — khắc phục đúng nhược điểm lớn nhất của `FixedSizeChunker`. Chọn 3 câu vì trong văn bản chính sách, một quy định thường được trình bày trong 2–3 câu (câu nêu quy tắc + câu nêu điều kiện/ngoại lệ), gom 3 câu là đủ để giữ cả quy tắc lẫn ngoại lệ trong cùng một ngữ cảnh. Điểm yếu đã biết trước: chiến lược này **hoàn toàn bỏ qua cấu trúc tài liệu** — không phân biệt tiêu đề, danh sách hay đoạn văn, chỉ đếm câu.
- **Kết quả benchmark (đo thật):** **4/10** · 38 chunk · thứ hạng `#1 #2 #1 trượt #1` · agent đúng 0/5
- **Nhận xét từ số liệu:** truy xuất tốt (4/5 câu có gold trong top-3) nhưng **agent không trả lời đúng câu nào**. Đây là ca rõ nhất cho bài học *retrieval đúng ≠ trả lời đúng*: chunk gom 3 câu nên đáp án bị lẫn với hai câu khác, phần trích ra không trúng.
- ⚠️ Bản hiện tại chạy trên corpus riêng trong thư mục cá nhân, cần chuyển sang `data/k4_ecommerce` ở gốc.

**Thành viên 5 — Đỗ Thu Liễu (2A202601898)**

- **Loại chiến lược:** `FixedSizeChunker(chunk_size=250, overlap=100)` — biến thể mịn, overlap cao (40%)
- **Mô tả & lý do chọn:** Chiến lược này kiểm chứng một giả thuyết riêng: **liệu overlap lớn có bù được nhược điểm của cắt theo ký tự hay không?** Dùng chung kiểu chunker với Đăng nhưng đẩy hai tham số ngược hướng — chunk nhỏ hơn một nửa (250 thay vì 500) và overlap gấp đôi tỷ lệ (100/250 = **40%**, so với 50/500 = 10%). Với overlap 40%, mọi cụm thông tin ngắn hơn 100 ký tự chắc chắn xuất hiện nguyên vẹn trong ít nhất một chunk, tức tối đa hoá recall. Cặp cấu hình Đăng–Liễu vì thế tạo thành một **thí nghiệm có kiểm soát**: cùng thuật toán, chỉ khác độ mịn và độ chồng lấp, nên chênh lệch điểm số phản ánh đúng ảnh hưởng của hai tham số đó.
- **Kết quả benchmark (đo thật):** **5/10** · 79 chunk · thứ hạng `#1 #3 #2 trượt #1` · agent đúng 1/5
- **Nhận xét từ số liệu:** overlap 40% giúp không mất thông tin ở ranh giới, nhưng cắt theo **ký tự** vẫn xé câu làm đôi nên Q2 tụt xuống #3 và Q3 xuống #2. Cho thấy **overlap không bù được việc cắt sai ranh giới ngữ nghĩa**.

### So Sánh Giữa Các Thành Viên

Toàn bộ số dưới đây **đo thật** bằng `python scripts/bench_ca_nhom.py` (`EMBEDDING_PROVIDER=local`), chạy đúng gói `src/` của từng người trên cùng corpus và cùng 5 câu hỏi. Số trong cột Q là **thứ hạng của chunk chứa gold answer**.

| Thành viên                  | Chiến lược                  | #chunk | Q1 | Q2           | Q3 | Q4           | Q5 | Agent | Điểm         |
| ----------------------------- | ------------------------------ | ------ | -- | ------------ | -- | ------------ | -- | ----- | -------------- |
| **Nguyễn Thanh Bình** | `ClauseChunker(1 câu)`      | 108    | #1 | #2           | #1 | **#2** | #1 | 3/5   | **8/10** |
| Trần Chí Vũ                | `RecursiveChunker(400)`      | 43     | #1 | **#1** | #1 | trượt      | #1 | 3/5   | **7/10** |
| Trịnh Hải Đăng            | `FixedSizeChunker(500, 50)`  | 32     | #1 | **#1** | #1 | trượt      | #1 | 2/5   | **6/10** |
| Đỗ Thu Liễu                | `FixedSizeChunker(250, 100)` | 79     | #1 | #3           | #2 | trượt      | #1 | 1/5   | **5/10** |
| Đỗ Văn Linh                | `SentenceChunker(3 câu)`    | 38     | #1 | #2           | #1 | trượt      | #1 | 0/5   | **4/10** |

| Thành viên        | Điểm mạnh                                                                                 | Điểm yếu                                                                    |
| ------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Nguyễn Thanh Bình | **Người duy nhất với được Q4**; tiền tố tiêu đề làm chunk tự đủ nghĩa | Chunk quá mịn nên đáp án và ngữ cảnh tách rời (Q2 mất số liệu)   |
| Trần Chí Vũ      | Tôn trọng ranh giới đoạn, Q2 lên#1; agent tốt ngang Bình                             | Trượt Q4 — chunk 400 ký tự nuốt trọn danh sách hàng cấm              |
| Trịnh Hải Đăng  | Ít chunk nhất (32), rẻ nhất về chi phí nhúng                                          | Mỗi chunk chứa nhiều chủ đề nên vector bị trung bình hoá; agent kém |
| Đỗ Thu Liễu      | Overlap 40% không để mất thông tin ở ranh giới                                        | Cắt theo ký tự vẫn xé câu; Q2 tụt#3, Q3 tụt #2                         |
| Đỗ Văn Linh      | Chunk luôn trọn câu, truy xuất 4/5 câu vào top-3                                       | **Agent 0/5** — chunk gom 3 câu làm phần trích không trúng        |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> **`ClauseChunker` dẫn đầu (8/10)**, nhưng khoảng cách với Vũ (7/10) chỉ đến từ **một câu duy nhất — Q4**, nên nhóm không kết luận dứt khoát dựa trên bảng xếp hạng.
>
> Điều nhóm tự tin kết luận là **cơ chế**: chiến lược thắng ở Q4 vì nó cắt **danh sách liệt kê theo từng mục**. Khi 20 nhóm hàng cấm nằm chung một chunk, vector của chunk đó là trung bình của 20 chủ đề nên không khớp riêng "đồ cổ"; tách mỗi mục thành một chunk thì dòng đó mới có vector riêng. **Bốn thành viên còn lại đều trượt Q4**, dù dùng ba kiểu chunker khác nhau và số chunk chênh nhau từ 32 đến 79 — cho thấy đây không phải chuyện may rủi mà là **giới hạn chung của mọi cách cắt theo độ dài**.
>
> Ba quan sát nữa từ bảng:
>
> 1. **Số chunk không quyết định chất lượng.** Liễu có 79 chunk (mịn thứ nhì) nhưng chỉ 5/10, còn Đăng có 32 chunk (thô nhất) lại được 6/10. Cái quyết định là **cắt ở đâu**, không phải cắt bao nhiêu.
> 2. **Overlap không cứu được ranh giới sai.** Liễu dùng overlap 40% — cao nhất nhóm — nhưng vẫn tụt hạng ở Q2 và Q3 vì cắt theo ký tự làm câu bị xé đôi.
> 3. **Truy xuất tốt không kéo theo trả lời tốt.** Linh truy xuất 4/5 câu vào top-3, ngang Vũ và Đăng, nhưng agent đúng **0/5** trong khi Vũ được 3/5. Chênh lệch nằm ở **độ mịn của chunk**, không ở thứ hạng.
>
> Bằng chứng mạnh nhất lại là ablation chứ không phải so sánh giữa người: bỏ tiền tố tiêu đề khiến **cùng một chunker, cùng 108 chunk** rơi từ **8/10 xuống 4/10**. Ngữ cảnh tiêu đề đóng góp nhiều hơn hẳn việc chọn kiểu chunker nào.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

Mỗi `gold_snippet` là cụm trích **nguyên văn** từ corpus và đã được `grep` xác minh **chỉ khớp đúng 1 tài liệu**, nên chấm được tự động ở **mức chunk**.

| # | Câu hỏi (Query)                                                                                                                                                                 | Câu trả lời chuẩn (Gold Answer)                                                                                                                                                  | Chunk nào chứa thông tin?         |
| - | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------ |
| 1 | Đơn vị vận chuyển liên hệ người mua mấy lần để giao hàng, và nếu không liên hệ được thì người mua được yêu cầu giao lại trong thời hạn bao lâu? | Liên hệ 2–3 lần; người mua có thể yêu cầu giao lại trong**không quá 5 ngày kể từ lần liên hệ đầu tiên**                                                  | `delivery-process`                 |
| 2 | Tôi trả hàng bằng cách tự sắp xếp vận chuyển cho đơn khác tỉnh/thành thì Shopee hoàn lại phí vận chuyển hoàn trả bao nhiêu và bằng hình thức gì?     | Hoàn bằng Shopee Xu trong 3–5 ngày làm việc: 25.000 Xu cùng tỉnh/thành,**40.000 Shopee Xu nếu khác tỉnh/thành**                                                   | `return-shipping-fee`              |
| 3 | **Phí vận chuyển được tính và xử lý như thế nào?** *(cần `metadata_filter={"customer_role":"seller"}`)*                                                   | Với người bán: phí dịch vụ của chương trình là**6%, tối đa 50.000 VNĐ trên giá bán của mỗi sản phẩm**                                                    | `shipping-fee-discount-program`    |
| 4 | Người bán có được đăng bán đồ cổ và tác phẩm nghệ thuật trên Shopee không, và nếu vi phạm chính sách sản phẩm cấm thì bị xử lý ra sao?            | Không được —**"Đồ cổ và tác phẩm nghệ thuật chưa được cấp phép"** thuộc nhóm bị cấm; vi phạm bị xóa sản phẩm, khóa tài khoản, tịch thu số dư | `restricted-products-policy`       |
| 5 | Người mua gửi khiếu nại đơn hàng ở đâu trên ứng dụng và Shopee đưa ra quyết định trong bao lâu đối với khiếu nại thông thường?                       | Khiếu nại qua mục "Đơn Mua"; quyết định trong**7 ngày làm việc đối với khiếu nại thông thường**                                                             | `marketplace-operating-regulation` |

Năm câu phủ 5 kiểu hỏi khác nhau: **thời hạn** (Q1) · **số liệu/phí** (Q2, Q3) · **điều kiện đối tượng** (Q3) · **danh mục cấm + chế tài** (Q4) · **quy trình** (Q5).

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (`docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan **và** agent trả lời đúng (2); có liên quan nhưng không ở top-1 hoặc trả lời thiếu (1); không có trong top-3 (0).

| # | Câu hỏi                      | Chiến lược tốt nhất cho câu này       | Bao nhiêu người có gold trong top-3? | Ghi chú                                                                                              |
| - | ------------------------------ | -------------------------------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| 1 | Thời hạn giao lại           | **Cả 5 người đều #1**             | 5/5                                      | Câu dễ nhất — đáp án nằm gọn trong một câu, mọi cách cắt đều giữ được             |
| 2 | Phí hoàn trả khác tỉnh    | Vũ, Đăng (#1)                             | 5/5                                      | Bình#2, Linh #2, Liễu #3. Chunk mịn làm câu *phương thức* và câu *số tiền* tách rời |
| 3 | Phí vận chuyển (có filter) | Bình, Vũ, Đăng, Linh (#1)                | 5/5                                      | Yếu tố quyết định là**filter**, không phải chunker — xem A/B bên dưới               |
| 4 | Đồ cổ / hàng cấm          | **Chỉ Bình (`ClauseChunker`, #2)** | **1/5**                            | **4/5 người trượt hẳn khỏi top-3.** Câu phân biệt duy nhất trong cả bộ              |
| 5 | Khiếu nại 7 ngày            | **Cả 5 người đều #1**             | 5/5                                      | Câu dễ, số liệu nằm cùng câu văn                                                              |

Đọc theo cột dọc thì thấy rõ: **4/5 câu không phân biệt được ai với ai** — cả nhóm cùng #1 hoặc chênh một bậc. Toàn bộ khác biệt điểm số tập trung vào **Q4**, và ở tầng agent. Đây là giới hạn của bộ 5 câu hỏi: quá ít câu "khó" để phân loại chiến lược. Nếu làm lại, nhóm sẽ thiết kế thêm câu nhắm vào danh sách liệt kê và câu có đáp án trải trên nhiều câu văn.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

| Câu 3                                                       | Top-3 tài liệu trả về                                       | Hạng chunk chứa gold |
| ------------------------------------------------------------ | --------------------------------------------------------------- | ---------------------- |
| **CÓ** `metadata_filter={"customer_role":"seller"}` | `shipping-fee-discount-program` × 3                          | **#1** ✅        |
| **KHÔNG** filter                                      | `return-shipping-fee`, `shipping-fee-discount-program` × 2 | **#2**           |

> **Có, và nhóm đã phải thiết kế lại câu hỏi mới chứng minh được điều đó.** Bản đầu của câu 3 hỏi *"Gian hàng cần đáp ứng điều kiện gì để tham gia chương trình ưu đãi phí vận chuyển?"* — vì câu đã nêu thẳng chữ "gian hàng" nên embedding tự khoá vào tài liệu người bán, và A/B cho kết quả **giống hệt nhau dù có hay không filter**: filter hoàn toàn vô dụng.
>
> Nhóm đổi thành *"Phí vận chuyển được tính và xử lý như thế nào?"* — **cố tình không nêu người hỏi là ai**, trong khi corpus có hai tài liệu cùng chủ đề nhưng khác đối tượng và khác đáp án: `return-shipping-fee` (buyer, hoàn 25.000/40.000 Xu) và `shipping-fee-discount-program` (seller, phí 6% tối đa 50.000 VNĐ). Lúc này không lọc thì **top-1 rơi vào tài liệu người mua** và agent trả lời sai đối tượng; bật filter thì cả 3 slot đều đúng vai và gold lên #1.
>
> Bài học: một câu hỏi chỉ thực sự "cần filter" khi nó **mơ hồ về đối tượng** *và* corpus có hai đáp án khác nhau cho hai đối tượng. Nếu chỉ đơn giản gắn filter vào một câu hỏi đã rõ đối tượng thì filter không loại được gì và không chứng minh được giá trị của metadata.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Kịch bản demo 6–8 phút

| Phút      | Ai                                    | Nội dung                                                                                                                                                           | Chuẩn bị sẵn                                                       |
| ---------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| 0:00–1:00 | Đăng*(data curator)*              | Phạm vi corpus, nguồn, schema metadata. Nhấn: chọn tài liệu**cả hai phía** buyer/seller là có chủ đích để `customer_role` lọc được thật | Chạy`python scripts/kiem_tra_corpus.py` → 10/10 OK                |
| 1:00–3:00 | Cả 5 người, mỗi người ~25 giây | Mỗi người nói**một câu** chiến lược của mình + **một câu** đánh đổi. Không đọc số, số để ở slide bảng                         | Bảng so sánh 5 người ở Mục 2                                    |
| 3:00–4:30 | Bình*(demo coordinator)*           | So sánh: 4/5 câu không phân biệt được ai với ai,**toàn bộ khác biệt nằm ở Q4** mà 4/5 người trượt                                         | Bảng thứ hạng Q1–Q5                                               |
| 4:30–5:30 | Vũ*(benchmark owner)*              | A/B metadata filter ở câu 3 + failure case filter dạng list bị vô hiệu im lặng                                                                               | Output`bench.py` phần "A/B metadata filter"                        |
| 5:30–7:00 | Linh + Liễu                          | Ablation bỏ tiêu đề (8/10 → 4/10) và bài học*retrieval đúng ≠ trả lời đúng*                                                                        | Bảng sweep 12 cấu hình                                             |
| 7:00–8:00 | Bất kỳ ai                           | Chạy live 1 query, hoặc chiếu output đã chuẩn bị                                                                                                             | Terminal mở sẵn`$env:EMBEDDING_PROVIDER="local"; python bench.py` |

**Ba câu hỏi giám khảo hay hỏi và cách trả lời (dựa trên số liệu đã đo):**

1. *"Chiến lược nào tái dùng được khi đổi domain?"* — `ClauseChunker` tái dùng được cho mọi văn bản có cấu trúc mục/điều/khoản (quy chế, điều khoản, FAQ, tài liệu pháp lý), vì nó bám **dấu hiệu cấu trúc đầu dòng** chứ không bám nội dung Shopee. Ngược lại `FixedSize` tái dùng được ở mọi nơi nhưng không bao giờ tốt ở đâu.
2. *"Filter giảm nhiễu ở đâu, đánh đổi recall thế nào?"* — Ở câu 3, filter đẩy gold từ #2 lên #1 và làm cả 3 slot đều đúng vai. Nhưng ở câu 5 thì **filter suýt phản tác dụng**: tài liệu gold có vai `both`, nếu lọc cứng `buyer` sẽ mất luôn đáp án — đúng ca "đánh đổi precision lấy recall".
3. *"Sao không ai trả lời đúng quá 3/5 dù truy xuất tốt?"* — Vì nút thắt nằm ở **tầng sinh câu trả lời**, không phải tầng truy xuất. LLM giả lập chỉ trích **một câu**; khi đáp án trải trên hai câu liền nhau là hỏng. Với LLM thật, con số này sẽ khác.

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Chấm ở mức chunk khác hẳn chấm ở mức `doc_id`.** Ở Q2, cả 3 slot top-3 đều thuộc đúng tài liệu gold — chấm theo `doc_id` sẽ ra "thành công tuyệt đối". Nhưng chunk #1 chỉ nói *"Người mua tự sắp xếp vận chuyển và trả phí trước; Shopee sẽ hoàn phí lại sau"*, **không có con số nào**, trong khi câu hỏi hỏi thẳng "bao nhiêu". Thêm nữa Q2 có **score cao nhất cả bộ (0.8653)** mà vẫn mất điểm — **score cao là tín hiệu xếp hạng, không phải bằng chứng nội dung đúng.**
2. **Ngữ cảnh tiêu đề quan trọng hơn việc chọn kiểu chunker.** Bỏ tiền tố tiêu đề khiến cùng một chunker rơi từ 8/10 xuống 3/10 — chênh lệch lớn hơn nhiều so với khoảng cách giữa các chiến lược khác nhau (8 vs 7 vs 6).
3. **Mịn hơn không phải tốt hơn.** `RecursiveChunker(120)` mịn nhất (143 chunk) nhưng tệ nhất (1/10). Cái quyết định là **cắt có tôn trọng ranh giới ngữ nghĩa hay không**, không phải kích thước.

**Bài học rút ra khi so sánh trong nhóm:**

> Cùng corpus, cùng 5 câu hỏi, chỉ khác chiến lược chunking mà chênh nhau tới **7 điểm** (từ 1/10 đến 8/10). Khác biệt không nằm ở "chunk to hay nhỏ" mà ở **chunk có khớp đơn vị ngữ nghĩa của văn bản hay không**: với văn bản chính sách, đơn vị đó là **điều/khoản**, và danh sách liệt kê phải được cắt theo **từng mục**.
>
> Bài học thứ hai đắt giá hơn: **retrieval đúng không đảm bảo câu trả lời đúng.** Mọi chiến lược tốt đều đưa chunk liên quan vào top-3 ở 4–5 câu, nhưng không cấu hình nào cho agent trả lời đúng quá 3/5. Trần điểm hiện nằm ở **tầng sinh câu trả lời**, không phải tầng truy xuất.

**Phân tích lỗi (failure case) — có bằng chứng từ top-k:**

**Ca 1 — Q4: câu hỏi hai vế làm truy xuất bị xé đôi giữa hai tài liệu.**
Câu hỏi gồm hai phần: *"có được bán đồ cổ không"* + *"vi phạm bị xử lý ra sao"*.

```
top1 score=0.7690 doc=seller-listing-rules        <- SAI TÀI LIỆU
top2 score=0.7604 doc=restricted-products-policy  <== CHUNK CHỨA GOLD
```

Chênh lệch chỉ **0,0086**. Đoạn *"Vi phạm các quy định trên có thể dẫn đến: gỡ sản phẩm, tạm khóa/khóa vĩnh viễn tài khoản…"* trong `seller-listing-rules` khớp rất mạnh với **vế thứ hai**, đẩy tài liệu đúng xuống #2. Agent vì thế trả lời được phần chế tài nhưng **không trả lời được phần đồ cổ**.
*Đề xuất:* tách câu hỏi hai vế thành hai truy vấn rồi hợp kết quả. Lưu ý `metadata_filter={"category":"seller-policy"}` **không cứu được** vì cả hai tài liệu đều thuộc `seller-policy` — cần metadata mịn hơn ở mức chủ đề.

**Ca 2 — Q4 với ba chunker có sẵn: trượt hoàn toàn khỏi top-3.**
"Đồ cổ và tác phẩm nghệ thuật" chỉ là **một dòng trong danh sách 20 nhóm hàng cấm**. Chunk 400–500 ký tự nuốt trọn cả danh sách, vector bị trung bình hoá trên 20 chủ đề nên không khớp riêng "đồ cổ".
*Đề xuất:* với tài liệu có danh sách liệt kê, bắt buộc cắt theo từng mục — đây là lý do cấu trúc để chọn chunker theo điều/khoản cho văn bản chính sách.

**Ca 3 — 4/5 store không hỗ trợ filter dạng list, filter bị âm thầm vô hiệu.**
Câu 5 cần lọc `{"customer_role": ["buyer", "both"]}` vì tài liệu gold có vai `both` — lọc cứng `"buyer"` sẽ **mất luôn tài liệu chứa đáp án**. Nhưng `search_with_filter` của 4/5 thành viên so khớp bằng `==` nên `"both" == ["buyer","both"]` cho `False` ở mọi bản ghi → **trả về rỗng**, không báo lỗi gì:

```
[cảnh báo] Trần Chí Vũ    — Q5: store không hỗ trợ filter dạng list, đã bỏ filter
[cảnh báo] Trịnh Hải Đăng — Q5: store không hỗ trợ filter dạng list, đã bỏ filter
[cảnh báo] Đỗ Văn Linh    — Q5: store không hỗ trợ filter dạng list, đã bỏ filter
[cảnh báo] Đỗ Thu Liễu    — Q5: store không hỗ trợ filter dạng list, đã bỏ filter
```

Đây là **failure im lặng** nguy hiểm nhất nhóm gặp: không exception, không cảnh báo, chỉ là "không tìm thấy gì" — rất khó truy nếu không đối chứng.
*Đề xuất:* cho `search_with_filter` nhận giá trị dạng list (khớp nếu thuộc tập), hoặc thiết kế corpus sao cho mỗi câu hỏi chỉ cần một giá trị vai duy nhất. Nhóm chọn cách một vì `both` là giá trị hợp lệ theo K4 nên chuyện này sẽ còn lặp lại.

**Ca 4 — chọn sai embedder làm hỏng toàn bộ kết luận.**
Số liệu chạy bằng `MockEmbedder` cho kết quả **gần như ngẫu nhiên**: cặp câu đồng nghĩa được 0,0752 trong khi cặp "chính sách đổi trả" vs "con mèo ngủ trên mái nhà" lại được 0,0801 — cao hơn. Với embedder thật, hai con số đó là **0,7623** và **−0,0705**. Một thành viên chạy benchmark bằng mock và được 0/5 câu, không phải do code sai.
*Đề xuất:* bắt buộc `EMBEDDING_PROVIDER=local` trước khi ghi bất kỳ kết luận nào về chiến lược.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> 1. **Đồng bộ corpus lên gốc repo ngay từ đầu.** Ban đầu mỗi người giữ một bản dữ liệu riêng nên kết quả không so sánh được — đúng điều đề bài cảnh báo. Mất thời gian gộp lại.
> 2. **Thêm metadata mịn hơn `category`.** Ca 1 cho thấy `category: seller-policy` gộp cả quy định đăng bán lẫn danh sách hàng cấm nên filter không tách được. Cần thêm trường kiểu `policy_type: listing-rule / prohibited-list / fee-schedule`.
> 3. **Bổ sung tài liệu `seller` cho mảng đổi trả.** Cả 3 tài liệu `returns` hiện đều là `customer_role: buyer`, trong khi nghĩa vụ hoàn phí của người bán lại nằm trong tài liệu vai `buyer`. Câu hỏi lọc `seller` về đổi trả sẽ không truy được đáp án.
> 4. **Chuẩn hoá cách viết front matter từ đầu** — không để giá trị trong nháy kép, và đặt `doc_id` trùng tên file, để không phải sửa lại khi chạy script chấm của đề.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                   | Điểm tự đánh giá                   |
| -------------------------------------------- | ---------------------------------------- |
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10                                   |
| Thiết kế chiến lược (Strategy Design)   | 14 / 15                                  |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10                                   |
| Thuyết trình (Demo)                        | 5/ 5                                     |
| **Tổng phần nhóm**                  | **31 / 35** *(chưa tính demo)* |

**Căn cứ tự chấm:**

- *Lựa chọn tài liệu **9/10**:* đạt CHECKPOINT 2 sạch, 10 tài liệu nguồn công khai có provenance đầy đủ, `customer_role` đủ 3 giá trị (4 buyer / 3 seller / 3 both) nên filter thật sự lọc được. Tự trừ 1 vì corpus chỉ từ **một sàn (Shopee)** — đa dạng nguồn còn hạn chế, và cả 2 tài liệu `returns` đều vai `buyer`.
- *Thiết kế chiến lược **13/15**:* 5 thành viên dùng **5 chiến lược khác nhau** (custom theo điều/khoản, recursive, fixed 500/50, fixed 250/100, sentence), đo trên **cùng corpus + cùng query + cùng embedder**, có bảng so sánh đầy đủ và ablation chứng minh cơ chế. Tự trừ 1 vì phần lý do thiết kế của 4 thành viên hiện là **bản nháp do nhóm soạn**, chưa được chính chủ chỉnh lại và xác nhận.
- *Chất lượng truy xuất **8/10**:* điểm cao nhất nhóm đo thật bằng `python bench.py` (2+1+2+1+2). Điểm 5 người: 8 / 7 / 6 / 5 / 4.

> **Việc còn lại trước khi nộp:** 4 thành viên xác nhận (hoặc đổi) tham số chiến lược của mình và tự viết phần *"Mô tả & lý do chọn"*; Đăng và Linh chạy lại báo cáo cá nhân với `EMBEDDING_PROVIDER=local` trên corpus chung. Số liệu benchmark trong báo cáo này đã sẵn sàng, không phải chạy lại.
