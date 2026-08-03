# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Điền tên nhóm]
**Thành viên:** Nguyễn Thanh Bình (2A202601274) · Trần Chí Vũ (2A202601044) · Trịnh Hải Đăng (2A202601602) · Đỗ Văn Linh (2A202601190) · Đỗ Thu Liễu (2A202601898)
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

> ⚠️ **Trạng thái bản này:** Mục 1 và Mục 3 đã hoàn tất. Mục 2 và Mục 4 mới điền phần của Nguyễn Thanh Bình cùng số liệu đo được; **bốn thành viên còn lại cần chốt chiến lược, chạy `bench.py` và điền khối của mình** (xem ô đánh dấu `[CẦN ĐIỀN]`).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng.

**Phạm vi cụ thể nhóm tập trung:**
> Chính sách vận hành sàn Shopee nhìn từ **hai phía** — nghĩa vụ của người mua (đổi trả, hoàn phí, giao hàng, thanh toán) và nghĩa vụ của người bán (đăng bán, hàng cấm, phí dịch vụ). Chọn hai phía có chủ đích để trường `customer_role` thực sự phân biệt được tài liệu, nếu không thì query có filter sẽ không chứng minh được gì.

### Danh sách tài liệu (Data Inventory)

Corpus dùng chung: `data/k4_ecommerce/` — **10 tài liệu**, toàn bộ lấy từ trang trợ giúp công khai của Shopee, ngày lấy 03/08/2026.

| # | doc_id | Tên tài liệu | customer_role | category | Số ký tự |
|---|---|---|---|---|---|
| 1 | `return-refund-policy` | Chính sách trả hàng và hoàn tiền | buyer | returns | 1.490 |
| 2 | `return-shipping-fee` | Phương thức gửi hàng hoàn trả và phí hoàn trả | buyer | returns | 836 |
| 3 | `payment-methods` | Các phương thức thanh toán Shopee hỗ trợ | buyer | payment | 946 |
| 4 | `delivery-process` | Đơn vị vận chuyển giao hàng như thế nào | buyer | shipping | 1.095 |
| 5 | `seller-listing-rules` | Quy định về đăng bán sản phẩm | seller | seller-policy | 1.094 |
| 6 | `restricted-products-policy` | Chính sách cấm/hạn chế sản phẩm | seller | seller-policy | 1.189 |
| 7 | `shipping-fee-discount-program` | Điều khoản chương trình ưu đãi phí vận chuyển | seller | shipping | 1.113 |
| 8 | `marketplace-operating-regulation` | Quy chế hoạt động sàn Shopee.vn | both | seller-policy | 1.259 |
| 9 | `privacy-policy` | Chính sách bảo mật | both | privacy | 1.887 |
| 10 | `voucher-discount-policy` | Chính sách voucher và ưu đãi giảm giá | both | promotion | 1.447 |

Nguồn đầy đủ (URL gốc, ngày lấy, phiên bản, căn cứ sử dụng) trong `data/k4_ecommerce/sources.csv`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa **trang trợ giúp công khai của Shopee**, không có dữ liệu cá nhân, thông tin đăng nhập hay tài liệu nội bộ. Không đăng nhập, không vượt CAPTCHA, không crawl toàn website.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at` (2026-08-03), `document_version` trong metadata; `sources.csv` khớp **một–một** với 10 file.

**Kết quả CHECKPOINT 2** (`python scripts/kiem_tra_corpus.py`):

```
10/10 file OK   |   so file: 10 (can 5-10)   |   csv: khop
customer_role : {'buyer': 4, 'seller': 3, 'both': 3}
```

Hai việc nhóm đã phải sửa để đạt checkpoint:
1. **Đổi tên 2 file cho khớp `doc_id`** — script chấm của đề so `doc_id` với tên file, `returns-policy.md` (doc_id `return-refund-policy`) và `seller-listing.md` (doc_id `seller-listing-rules`) bị báo `THIEU METADATA` dù metadata đủ. Đã đổi tên file và cập nhật `file_path` trong `sources.csv`.
2. **Thay toàn bộ dữ liệu khởi động** — 2 file mẫu của repo còn `source_url: https://example.com/...` và câu *"Nhóm phải bổ sung nguồn chính sách công khai"*, không dùng để chấm được.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất? |
|---|---|---|---|
| `doc_id` | str | `return-shipping-fee` | Khoá truy vết: mọi chunk đều mang `doc_id` của file gốc, nhờ đó `delete_document()` xoá đúng và câu trả lời chỉ được về đúng nguồn |
| `customer_role` | str | `buyer` / `seller` / `both` | **Trường bắt buộc của K4.** Corpus có hai tài liệu cùng chủ đề "phí vận chuyển" nhưng khác đối tượng và **khác đáp án**; không có trường này thì câu hỏi mơ hồ sẽ trả lời sai đối tượng (xem A/B ở Mục 3) |
| `category` | str | `returns` / `seller-policy` / `shipping` / `payment` / `privacy` | Thu hẹp theo chủ đề khi `customer_role` chưa đủ — 3 tài liệu `seller-policy` vẫn cạnh tranh nhau ở câu hỏi về hàng cấm |
| `source_url` | str | `https://help.shopee.vn/...` | Truy vết nguồn khi agent trả lời; agent in kèm URL trong ngữ cảnh đánh số `[n]` |
| `retrieved_at` | date | `2026-08-03` | Kiểm tra độ mới của chính sách — chính sách TMĐT thay đổi thường xuyên |
| `document_version` | str | `2026.1` / `not-stated` | Phân biệt phiên bản chính sách khi cùng một trang được cập nhật |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=400)` trên 3 tài liệu (đã bỏ front matter, chỉ đo phần thân):

| Tài liệu | Chiến lược | Số chunk | Độ dài TB | Giữ được ngữ cảnh không? |
|---|---|---|---|---|
| `return-refund-policy` (1.490 ký tự) | `fixed_size` | 5 | 330,0 | Không — cắt giữa câu, mốc "15 ngày" và điều kiện đi kèm bị tách |
| | `by_sentences` | 4 | 370,3 | Có — mỗi chunk trọn câu |
| | `recursive` | 7 | 211,3 | Có — cắt ở ranh giới đoạn trước |
| `restricted-products-policy` (1.189) | `fixed_size` | 4 | 327,3 | Không — danh sách 20 nhóm hàng cấm bị cắt ngang |
| | `by_sentences` | 2 | 593,0 | Kém — 2 chunk quá to, gộp nhiều nhóm hàng vào một vector |
| | `recursive` | 4 | 296,3 | Trung bình |
| `shipping-fee-discount-program` (1.113) | `fixed_size` | 3 | 397,7 | Không |
| | `by_sentences` | 4 | 275,8 | Có |
| | `recursive` | 4 | 276,8 | Có |

Tổng số chunk trên toàn corpus 10 tài liệu:

| Chiến lược | Số chunk |
|---|---|
| `FixedSizeChunker(500, 50)` | 32 |
| `SentenceChunker(3 câu)` | 38 |
| `RecursiveChunker(400)` | 45 |
| `ClauseChunker(1 câu)` | 108 |

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

**Thành viên 2 — Trần Chí Vũ (2A202601044)**
- **Loại chiến lược:** `RecursiveChunker` — *[CẦN ĐIỀN: chốt tham số `chunk_size` / `separators`]*
- **Mô tả & lý do chọn:** *[CẦN ĐIỀN]*
- **Kết quả benchmark:** *[CẦN ĐIỀN — chạy `bench.py` với `EMBEDDING_PROVIDER=local`]*

**Thành viên 3 — Trịnh Hải Đăng (2A202601602)**
- **Loại chiến lược:** `FixedSizeChunker` có overlap — hiện dùng `chunk_size=300, overlap=40`
- **Mô tả & lý do chọn:** *[CẦN ĐIỀN]*
- **Kết quả benchmark:** *[CẦN ĐIỀN — bản hiện tại chạy bằng `_mock_embed` nên được 0/5; phải chạy lại với `EMBEDDING_PROVIDER=local`]*

**Thành viên 4 — Đỗ Văn Linh (2A202601190)**
- **Loại chiến lược:** `SentenceChunker` — *[CẦN ĐIỀN: chốt `max_sentences_per_chunk`]*
- **Mô tả & lý do chọn:** *[CẦN ĐIỀN]*
- **Kết quả benchmark:** *[CẦN ĐIỀN — bản hiện tại chạy bằng mock trên corpus riêng; phải chạy lại trên `data/k4_ecommerce` ở gốc với local embedder]*

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược | #chunk | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|---|---|---|---|---|---|
| Nguyễn Thanh Bình | `ClauseChunker(1 câu)` | 108 | **8** | Duy nhất với được Q4 (danh sách hàng cấm); tiêu đề làm chunk tự đủ nghĩa | Chunk quá mịn nên đáp án và ngữ cảnh tách rời (Q2 mất số liệu) |
| Trần Chí Vũ | `RecursiveChunker` | 45 | *[CẦN ĐIỀN]* | Tôn trọng ranh giới đoạn | Trượt Q4 |
| Trịnh Hải Đăng | `FixedSizeChunker` có overlap | 31 | *[CẦN ĐIỀN]* | Ít chunk, overlap giữ liên kết | Cắt ngang câu; trượt Q4 |
| Đỗ Văn Linh | `SentenceChunker` | 38 | *[CẦN ĐIỀN]* | Chunk luôn trọn câu | Không tôn trọng ranh giới mục |

*(Cột "Điểm truy xuất" của Bình lấy từ `python bench.py`; ba bạn còn lại điền sau khi chạy.)*

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với dữ liệu hiện có, **`ClauseChunker` dẫn đầu (8/10)**, `FixedSizeChunker(500,50)` và `RecursiveChunker(400)` cùng 7/10. Nhưng khoảng cách chỉ đến từ **một câu duy nhất — Q4**, nên chưa thể kết luận dứt khoát.
>
> Điều nhóm tự tin kết luận là **cơ chế**, không phải bảng xếp hạng: chiến lược thắng ở Q4 vì nó cắt **danh sách liệt kê theo từng mục**. Khi 20 nhóm hàng cấm nằm chung một chunk, vector của chunk đó là trung bình của 20 chủ đề nên không khớp riêng "đồ cổ"; tách mỗi mục thành một chunk thì dòng đó mới có vector riêng. Đây là đặc điểm **cấu trúc của văn bản chính sách**, tái dùng được sang domain khác có cùng dạng (quy chế, điều khoản, FAQ).
>
> Bằng chứng mạnh nhất lại là ablation chứ không phải so sánh: bỏ tiền tố tiêu đề khiến **cùng một chunker, cùng 109 chunk** rơi từ **8/10 xuống 3/10** (trượt 2 câu, agent sai cả 5). Ngữ cảnh tiêu đề đóng góp nhiều hơn hẳn việc chọn kiểu chunker nào.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

Mỗi `gold_snippet` là cụm trích **nguyên văn** từ corpus và đã được `grep` xác minh **chỉ khớp đúng 1 tài liệu**, nên chấm được tự động ở **mức chunk**.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|---|---|---|
| 1 | Đơn vị vận chuyển liên hệ người mua mấy lần để giao hàng, và nếu không liên hệ được thì người mua được yêu cầu giao lại trong thời hạn bao lâu? | Liên hệ 2–3 lần; người mua có thể yêu cầu giao lại trong **không quá 5 ngày kể từ lần liên hệ đầu tiên** | `delivery-process` |
| 2 | Tôi trả hàng bằng cách tự sắp xếp vận chuyển cho đơn khác tỉnh/thành thì Shopee hoàn lại phí vận chuyển hoàn trả bao nhiêu và bằng hình thức gì? | Hoàn bằng Shopee Xu trong 3–5 ngày làm việc: 25.000 Xu cùng tỉnh/thành, **40.000 Shopee Xu nếu khác tỉnh/thành** | `return-shipping-fee` |
| 3 | **Phí vận chuyển được tính và xử lý như thế nào?** *(cần `metadata_filter={"customer_role":"seller"}`)* | Với người bán: phí dịch vụ của chương trình là **6%, tối đa 50.000 VNĐ trên giá bán của mỗi sản phẩm** | `shipping-fee-discount-program` |
| 4 | Người bán có được đăng bán đồ cổ và tác phẩm nghệ thuật trên Shopee không, và nếu vi phạm chính sách sản phẩm cấm thì bị xử lý ra sao? | Không được — **"Đồ cổ và tác phẩm nghệ thuật chưa được cấp phép"** thuộc nhóm bị cấm; vi phạm bị xóa sản phẩm, khóa tài khoản, tịch thu số dư | `restricted-products-policy` |
| 5 | Người mua gửi khiếu nại đơn hàng ở đâu trên ứng dụng và Shopee đưa ra quyết định trong bao lâu đối với khiếu nại thông thường? | Khiếu nại qua mục "Đơn Mua"; quyết định trong **7 ngày làm việc đối với khiếu nại thông thường** | `marketplace-operating-regulation` |

Năm câu phủ 5 kiểu hỏi khác nhau: **thời hạn** (Q1) · **số liệu/phí** (Q2, Q3) · **điều kiện đối tượng** (Q3) · **danh mục cấm + chế tài** (Q4) · **quy trình** (Q5).

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (`docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan **và** agent trả lời đúng (2); có liên quan nhưng không ở top-1 hoặc trả lời thiếu (1); không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---|---|---|---|
| 1 | Thời hạn giao lại | Mọi chiến lược trừ nhóm chunk quá mịn | ✅ #1 với hầu hết | Câu dễ nhất — đáp án nằm gọn trong một câu |
| 2 | Phí hoàn trả khác tỉnh | `FixedSize(500,50)`, `Recursive(400)` (#1) | ✅ | `ClauseChunker` chỉ #2: câu nêu *phương thức* và câu nêu *số tiền* bị tách hai chunk |
| 3 | Phí vận chuyển (có filter) | Mọi chiến lược | ✅ #1 | Filter là yếu tố quyết định, không phải chunker — xem A/B bên dưới |
| 4 | Đồ cổ / hàng cấm | **Chỉ `ClauseChunker` (#2)** | ⚠️ 3 chunker có sẵn **trượt hẳn** | Câu phân biệt duy nhất giữa 8/10 và 7/10 |
| 5 | Khiếu nại 7 ngày | Mọi chiến lược | ✅ #1 | Câu dễ, số liệu nằm cùng câu văn |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

| Câu 3 | Top-3 tài liệu trả về | Hạng chunk chứa gold |
|---|---|---|
| **CÓ** `metadata_filter={"customer_role":"seller"}` | `shipping-fee-discount-program` × 3 | **#1** ✅ |
| **KHÔNG** filter | `return-shipping-fee`, `shipping-fee-discount-program` × 2 | **#2** |

> **Có, và nhóm đã phải thiết kế lại câu hỏi mới chứng minh được điều đó.** Bản đầu của câu 3 hỏi *"Gian hàng cần đáp ứng điều kiện gì để tham gia chương trình ưu đãi phí vận chuyển?"* — vì câu đã nêu thẳng chữ "gian hàng" nên embedding tự khoá vào tài liệu người bán, và A/B cho kết quả **giống hệt nhau dù có hay không filter**: filter hoàn toàn vô dụng.
>
> Nhóm đổi thành *"Phí vận chuyển được tính và xử lý như thế nào?"* — **cố tình không nêu người hỏi là ai**, trong khi corpus có hai tài liệu cùng chủ đề nhưng khác đối tượng và khác đáp án: `return-shipping-fee` (buyer, hoàn 25.000/40.000 Xu) và `shipping-fee-discount-program` (seller, phí 6% tối đa 50.000 VNĐ). Lúc này không lọc thì **top-1 rơi vào tài liệu người mua** và agent trả lời sai đối tượng; bật filter thì cả 3 slot đều đúng vai và gold lên #1.
>
> Bài học: một câu hỏi chỉ thực sự "cần filter" khi nó **mơ hồ về đối tượng** *và* corpus có hai đáp án khác nhau cho hai đối tượng. Nếu chỉ đơn giản gắn filter vào một câu hỏi đã rõ đối tượng thì filter không loại được gì và không chứng minh được giá trị của metadata.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

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

**Ca 3 — chọn sai embedder làm hỏng toàn bộ kết luận.**
Số liệu chạy bằng `MockEmbedder` cho kết quả **gần như ngẫu nhiên**: cặp câu đồng nghĩa được 0,0752 trong khi cặp "chính sách đổi trả" vs "con mèo ngủ trên mái nhà" lại được 0,0801 — cao hơn. Với embedder thật, hai con số đó là **0,7623** và **−0,0705**. Một thành viên chạy benchmark bằng mock và được 0/5 câu, không phải do code sai.
*Đề xuất:* bắt buộc `EMBEDDING_PROVIDER=local` trước khi ghi bất kỳ kết luận nào về chiến lược.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> 1. **Đồng bộ corpus lên gốc repo ngay từ đầu.** Ban đầu mỗi người giữ một bản dữ liệu riêng nên kết quả không so sánh được — đúng điều đề bài cảnh báo. Mất thời gian gộp lại.
> 2. **Thêm metadata mịn hơn `category`.** Ca 1 cho thấy `category: seller-policy` gộp cả quy định đăng bán lẫn danh sách hàng cấm nên filter không tách được. Cần thêm trường kiểu `policy_type: listing-rule / prohibited-list / fee-schedule`.
> 3. **Bổ sung tài liệu `seller` cho mảng đổi trả.** Cả 3 tài liệu `returns` hiện đều là `customer_role: buyer`, trong khi nghĩa vụ hoàn phí của người bán lại nằm trong tài liệu vai `buyer`. Câu hỏi lọc `seller` về đổi trả sẽ không truy được đáp án.
> 4. **Chuẩn hoá cách viết front matter từ đầu** — không để giá trị trong nháy kép, và đặt `doc_id` trùng tên file, để không phải sửa lại khi chạy script chấm của đề.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|---|---|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | *[CẦN ĐIỀN sau khi 3 thành viên chạy xong]* / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 |
| Thuyết trình (Demo) | *[CẦN ĐIỀN sau buổi demo]* / 5 |
| **Tổng phần nhóm** | **/ 40** |

**Căn cứ tự chấm:**
- *Lựa chọn tài liệu 9/10:* đạt CHECKPOINT 2 sạch, 10 tài liệu nguồn công khai có provenance đầy đủ, `customer_role` có đủ 3 giá trị. Tự trừ 1 vì corpus chỉ từ **một sàn (Shopee)** — đa dạng nguồn còn hạn chế, và 3 tài liệu `returns` đều cùng một vai.
- *Chất lượng truy xuất 8/10:* điểm đo thật của thành viên đạt cao nhất (`python bench.py` → 2+1+2+1+2). Sẽ cập nhật thành điểm trung bình nhóm khi ba bạn còn lại chạy xong.
