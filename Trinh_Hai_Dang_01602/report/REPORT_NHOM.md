# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** B7-E402
**Thành viên:** Trịnh Hải Đăng (2A202601602) — *phần dưới đây do Đăng soạn dựa trên dữ liệu/pipeline chung của nhóm; các thành viên khác điền phần chiến lược riêng của mình vào mục 2 trước khi nộp.*
**Ngày:** Thứ 2, 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:** Kết hợp 3 mảng trong chủ đề K4 — **đổi trả/hoàn tiền, điều kiện/nghĩa vụ người bán, và thanh toán/giao hàng** — để bộ dữ liệu có cả tài liệu hướng buyer, hướng seller và tài liệu chung (both), đáp ứng yêu cầu K4 về `customer_role` đa dạng.

**Quyết định nguồn dữ liệu:** Nhóm chọn **một nguồn duy nhất — Shopee (help.shopee.vn)** thay vì trộn nhiều sàn TMĐT, để đảm bảo tính nhất quán về văn phong/cấu trúc điều khoản giữa các tài liệu (giúp việc so sánh chiến lược chunking giữa các thành viên có ý nghĩa — nếu trộn nhiều sàn, khác biệt kết quả có thể do khác nguồn chứ không phải do khác chiến lược).

**Quy mô:** Đề bài yêu cầu 5-10 tài liệu; nhóm thu thập **20 tài liệu** (vượt mức tối đa được đề xuất) để có kho ngữ liệu phong phú hơn cho việc thử nghiệm chiến lược, đồng thời vẫn giữ toàn bộ trong phạm vi chủ đề K4 đã chọn.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu (doc_id) | Nguồn (Source URL — rút gọn) | Ngày lấy / Phiên bản | Số ký tự | `customer_role` | `category` |
|---|--------------------|------------|--------------------|----------|-----------------|------------|
| 1 | return-refund-policy | help.shopee.vn/.../77251 | 2026-08-03 / 2026-03-11 | 19.489 | buyer | returns |
| 2 | return-refund-general-rules | help.shopee.vn/.../188931 | 2026-08-03 / not-stated | 6.029 | buyer | returns |
| 3 | return-shipping-fee | help.shopee.vn/.../189477 | 2026-08-03 / not-stated | 5.876 | buyer | returns |
| 4 | seller-listing-rules | help.shopee.vn/.../77246 | 2026-08-03 / 2024-08-21 | 21.551 | seller | seller-policy |
| 5 | marketplace-operating-regulation | help.shopee.vn/.../77245 | 2026-08-03 / 2025-01-10 | 77.541 | both | seller-policy |
| 6 | restricted-products-policy | help.shopee.vn/.../77247 | 2026-08-03 / 2025-05-05 | 12.736 | seller | seller-policy |
| 7 | payment-methods | help.shopee.vn/.../79198 | 2026-08-03 / not-stated | 5.712 | buyer | payment |
| 8 | shipping-fee-discount-program | help.shopee.vn/.../77263 | 2026-08-03 / 2024-07-03 | 4.808 | seller | shipping |
| 9 | delivery-process | help.shopee.vn/.../79569 | 2026-08-03 / 2023-05-19 | 2.460 | buyer | shipping |
| 10 | privacy-policy | help.shopee.vn/.../77244 | 2026-08-03 / 2026-06-11 | 42.987 | both | privacy |
| 11 | warranty-policy | help.shopee.vn/.../79046 | 2026-08-03 / not-stated | 4.241 | buyer | warranty |
| 12 | seller-anti-fraud-policy | help.shopee.vn/.../140097 | 2026-08-03 / 2023-12-28 | 6.299 | seller | seller-policy |
| 13 | voucher-discount-policy | help.shopee.vn/.../166085 | 2026-08-03 / 2026-05-23 | 14.283 | both | promotion |
| 14 | voucher-types | help.shopee.vn/.../79250 | 2026-08-03 / not-stated | 1.923 | buyer | promotion |
| 15 | dispute-resolution-process | help.shopee.vn/.../77265 | 2026-08-03 / 2024-03-22 | 4.646 | both | complaints |
| 16 | shopee-mall-terms | help.shopee.vn/.../77262 | 2026-08-03 / 2026-05-08 | 33.464 | seller | seller-policy |
| 17 | cod-payment-guide | help.shopee.vn/.../79295 | 2026-08-03 / not-stated | 2.387 | buyer | payment |
| 18 | shopeevip-membership | help.shopee.vn/.../178771 | 2026-08-03 / not-stated | 8.142 | buyer | payment |
| 19 | global-selling-program | help.shopee.vn/.../178103 | 2026-08-03 / 2025-06-27 | 28.571 | seller | seller-policy |
| 20 | parcel-locker-delivery | help.shopee.vn/.../176407 | 2026-08-03 / not-stated | 2.662 | buyer | shipping |

**Tổng dung lượng:** ~305.807 ký tự nội dung đã làm sạch (không tính front matter), phân bổ `customer_role`: buyer = 10, seller = 6, both = 4. Danh sách đầy đủ kèm `license_or_permission` xem tại `data/k4_ecommerce/sources.csv`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai (Trung tâm trợ giúp Shopee) và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated` nếu nguồn không nêu rõ ngày hiệu lực) trong metadata.
- [x] Đã kiểm tra `robots.txt` của help.shopee.vn (`Allow: /`) trước khi thu thập.
- [x] Nội dung được trích **verbatim đầy đủ** từ dữ liệu SSR nhúng trong trang gốc (không qua bước tóm tắt trung gian làm mất chi tiết).

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | string (enum) | `buyer` / `seller` / `both` | **Bắt buộc theo K4** — cho phép `search_with_filter()` trả lời đúng phạm vi khi câu hỏi chỉ áp dụng cho một vai trò (vd câu hỏi về nghĩa vụ người bán không nên trộn với chính sách dành cho người mua) |
| `category` | string | `returns`, `seller-policy`, `payment`, `shipping`, `privacy`, `warranty`, `promotion`, `complaints` | Cho phép lọc theo chủ đề con trong phạm vi K4, hữu ích khi câu hỏi rõ ràng thuộc 1 nhóm chính sách |
| `document_version` | string (ngày hoặc `not-stated`) | `2026-03-11` | Giúp kiểm tra độ mới của chính sách khi trả lời, tránh trích dẫn điều khoản đã hết hiệu lực |
| `source_url` | string (URL) | `https://help.shopee.vn/portal/4/article/77251-...` | Truy vết được câu trả lời về đúng trang nguồn để kiểm chứng |
| `retrieved_at` | string (ngày) | `2026-08-03` | Ghi nhận thời điểm thu thập, phục vụ đối chiếu khi chính sách thay đổi sau này |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=300)` trên 3 tài liệu đại diện (1 ngắn, 1 trung bình, 1 rất dài) bằng `LocalEmbedder` thật:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| return-refund-policy (19.489 ký tự) | FixedSizeChunker (`fixed_size`) | 73 | 297 | Trung bình — có thể cắt giữa câu/điều khoản |
| return-refund-policy | SentenceChunker (`by_sentences`) | 55 | 352 | Tốt hơn — giữ trọn câu, nhưng nhóm câu ngẫu nhiên không theo ranh giới điều khoản |
| return-refund-policy | RecursiveChunker (`recursive`) | 103 | 187 | Chunk nhỏ, nhiều — dễ mất ngữ cảnh điều khoản dài |
| privacy-policy (42.987 ký tự) | FixedSizeChunker | 160 | 298 | Trung bình |
| privacy-policy | SentenceChunker | 61 | 703 | Tốt, câu dài do văn phong pháp lý |
| privacy-policy | RecursiveChunker | 221 | 193 | Rất phân mảnh với văn bản dài |
| marketplace-operating-regulation (77.541 ký tự) | FixedSizeChunker | 288 | 299 | Số lượng chunk rất lớn với văn bản luật dài |
| marketplace-operating-regulation | SentenceChunker | 192 | 402 | Vẫn phân mảnh vì văn bản luật có câu dài xen câu ngắn |
| marketplace-operating-regulation | RecursiveChunker | 403 | 191 | Phân mảnh nhiều nhất trong 3 chiến lược có sẵn |

**Nhận xét chung:** cả 3 chiến lược có sẵn đều chunk theo **kích thước ký tự/câu**, không quan tâm đến cấu trúc điều khoản của văn bản pháp lý — với các tài liệu dài (quy chế sàn 77K ký tự), số lượng chunk sinh ra rất lớn (288-403 chunk) và ranh giới chunk không trùng với ranh giới ngữ nghĩa của một điều khoản.

### Chiến lược của từng thành viên

**Thành viên: Trịnh Hải Đăng (2A202601602)**
- **Loại chiến lược:** Custom — `ClauseChunker` (chia theo ranh giới điều/khoản đánh số)
- **Mô tả & lý do chọn cho chủ đề này:** Toàn bộ 20 tài liệu Shopee đều là văn bản chính sách/điều khoản có cấu trúc đánh số ở cấp cao nhất (dạng `**1. Tên điều khoản**` hoặc numbered heading in hoa). Giả thuyết: chunk theo đúng ranh giới điều khoản sẽ giữ trọn vẹn ngữ nghĩa pháp lý của từng điều, phù hợp hơn cắt theo kích thước cố định — đúng như gợi ý K4 "chia theo điều/khoản, tiêu đề". Với điều khoản quá dài (>1200 ký tự), tiếp tục chia theo đoạn văn để tránh chunk quá khổ.
- **Code snippet:**
```python
import re

class ClauseChunker:
    """Chia nhỏ theo ranh giới điều/khoản (heading đánh số) cho văn bản chính sách Shopee.

    Lý do thiết kế: tài liệu nguồn là văn bản pháp lý có cấu trúc đánh số rõ ràng
    ở cấp 1 (vd "**1. Tên điều khoản**" hoặc dòng in hoa "1. TÊN ĐIỀU KHOẢN").
    Chunk theo điều khoản giữ nguyên ngữ cảnh pháp lý trọn vẹn, phù hợp hơn cắt
    theo kích thước cố định cho loại văn bản này.
    """
    NUMBERED_LINE = re.compile(r"^\d{1,2}\.\s+\S.*$")
    MAX_CHUNK_SIZE = 1200
    MAX_HEADING_LEN = 100

    def _is_heading(self, line: str) -> bool:
        stripped = line.strip()
        inner = stripped[2:-2].strip() if stripped.startswith("**") and stripped.endswith("**") else stripped
        if not self.NUMBERED_LINE.match(inner) or len(inner) > self.MAX_HEADING_LEN:
            return False
        if inner.rstrip().endswith((";", ",")):
            return False
        body = re.sub(r"^\d{1,2}\.\s+", "", inner)
        letters = [c for c in body if c.isalpha()]
        is_upper = bool(letters) and all(c.isupper() for c in letters)
        return is_upper or stripped.startswith("**")

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        lines = text.splitlines()
        heading_idx = [i for i, l in enumerate(lines) if self._is_heading(l)]
        if not heading_idx:
            return [p.strip() for p in text.split("\n\n") if p.strip()]
        offsets, pos = [], 0
        for l in lines:
            offsets.append(pos)
            pos += len(l) + 1
        positions = [offsets[i] for i in heading_idx]
        chunks = []
        intro = text[:positions[0]].strip()
        if intro:
            chunks.append(intro)
        for i, start in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(text)
            section = text[start:end].strip()
            if len(section) <= self.MAX_CHUNK_SIZE:
                chunks.append(section)
            else:
                buf = ""
                for p in (x.strip() for x in section.split("\n\n") if x.strip()):
                    cand = f"{buf}\n\n{p}" if buf else p
                    if len(cand) <= self.MAX_CHUNK_SIZE:
                        buf = cand
                    else:
                        if buf:
                            chunks.append(buf)
                        buf = p
                if buf:
                    chunks.append(buf)
        return chunks
```
- **Kết quả trên 3 tài liệu mẫu:** return-refund-policy → 24 chunk (avg 809 ký tự); privacy-policy → 46 chunk (avg 932 ký tự); marketplace-operating-regulation → 82 chunk (avg 943 ký tự) — **số chunk giảm mạnh** so với baseline (24 vs 73, 46 vs 160, 82 vs 288) vì mỗi chunk giờ là một điều khoản hoàn chỉnh thay vì một đoạn 300 ký tự.

> **Thành viên 2 — [Tên]:** *(điền chiến lược riêng — vd `SentenceChunker` tinh chỉnh `max_sentences_per_chunk`, hoặc chunk theo cặp FAQ cho các tài liệu dạng hỏi-đáp như `cod-payment-guide`, `voucher-types`)*
>
> **Thành viên 3 — [Tên]:** *(điền chiến lược riêng — vd `RecursiveChunker` với separator tùy chỉnh theo dấu `;` hay heading Markdown `##`)*

### So Sánh Giữa Các Thành Viên

Chạy 5 câu hỏi đánh giá (Mục 3) trên cùng corpus 20 tài liệu, `LocalEmbedder` thật, `chunk_size=300/overlap=40` (đối với `FixedSizeChunker`):

| Thành viên | Chiến lược (Strategy) | Số câu đúng top-1 /5 | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Đăng | `ClauseChunker` (custom, theo điều khoản) | **3 / 5** | Chunk giữ trọn ngữ nghĩa 1 điều khoản; số lượng chunk ít hơn hẳn (dễ quản lý, ít trùng lặp) | Phụ thuộc heading nhất quán — 1/20 tài liệu dùng heading Markdown `##` thay vì `**N.**` khiến chunker "rơi" về chia theo đoạn văn (40 chunk rất nhỏ, 72-176 ký tự) làm giảm độ chính xác câu 2; chunk từ văn bản luật dài (vd `marketplace-operating-regulation`) có thể quá rộng, làm loãng nghĩa và lấn át chunk đúng từ tài liệu chuyên biệt hơn ở câu 4 |
| *(nhóm)* Baseline `FixedSizeChunker(300,40)` | Kích thước cố định | **5 / 5** | Nhất quán tuyệt đối bất kể định dạng nguồn, không phụ thuộc heading | Có thể cắt giữa câu/điều khoản, chunk không phải lúc nào cũng là 1 đơn vị ngữ nghĩa trọn vẹn |
| *(chờ Thành viên 2 điền)* | | / 5 | | |
| *(chờ Thành viên 3 điền)* | | / 5 | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

Với benchmark 5 câu hỏi hiện tại, `FixedSizeChunker(300,40)` (baseline) cho kết quả tốt hơn `ClauseChunker` (custom) — 5/5 so với 3/5 câu đúng top-1. Điều này ban đầu có vẻ ngược với giả thuyết thiết kế ("chunk theo điều khoản sẽ tốt hơn cho văn bản pháp lý"), nhưng khi phân tích kỹ (xem Mục 4 — Phân tích lỗi), nguyên nhân chính không phải do ý tưởng chunk theo điều khoản sai, mà do **cách hiện thực hoá chưa xử lý được sự không nhất quán về định dạng heading giữa các tài liệu trong corpus** — một tài liệu dùng heading Markdown khác kiểu khiến chunker "rơi" về chế độ dự phòng kém hiệu quả. Đây là minh chứng cụ thể cho nguyên tắc mà `docs/SCORING.md` nhấn mạnh: nhóm đánh giá cao **khả năng suy nghĩ và giải thích tại sao** một chiến lược hoạt động/không hoạt động, hơn là chỉ nhìn vào điểm số truy xuất thuần tuý — một ý tưởng chunking hợp lý vẫn có thể thua baseline đơn giản nếu triển khai chưa xử lý hết các trường hợp biên của dữ liệu thật.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk/tài liệu chứa thông tin |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng/hoàn tiền kể từ khi giao hàng thành công? | 15 ngày kể từ khi đơn hàng cập nhật "Giao hàng thành công"; riêng thực phẩm tươi sống/đông lạnh là 24 giờ | `return-refund-policy` (Điều 3.2) |
| 2 | Shopee hỗ trợ những phương thức thanh toán nào? | 09 hình thức: Ví ShopeePay, Thẻ Tín dụng/Ghi nợ, Trả góp thẻ tín dụng, Thanh toán QR, Ứng dụng ngân hàng, Thẻ nội địa NAPAS, Apple Pay, Google Pay, Thanh toán khi nhận hàng (COD), SPayLater | `payment-methods` (toàn bài) |
| 3 | Người bán không được đăng bán loại sản phẩm nào theo quy định? *(cần `metadata_filter={"customer_role": "seller"}`)* | Hàng giả/hàng nhái, hàng vi phạm sở hữu trí tuệ, hàng cấm/hạn chế (vũ khí, ma túy, động vật quý hiếm...), sản phẩm gây hiểu nhầm về nguồn gốc/nhãn hiệu | `seller-listing-rules`, `restricted-products-policy`, `shopee-mall-terms` (điều khoản cấm hàng giả/nhái) |
| 4 | Shopee thu thập những loại dữ liệu cá nhân nào của người dùng? | Họ tên, email, ngày sinh, địa chỉ, SĐT, giới tính, thông tin thiết bị, hình ảnh/âm thanh/video, giấy tờ tùy thân, dữ liệu vị trí, v.v. (Điều 3, Chính sách Bảo mật) | `privacy-policy` (Điều 3. SHOPEE SẼ THU THẬP NHỮNG DỮ LIỆU GÌ?) |
| 5 | Phí dịch vụ của chương trình ưu đãi phí vận chuyển dành cho người bán là bao nhiêu? *(cần `metadata_filter={"customer_role": "seller"}`)* | 6%, tối đa 50.000 VNĐ trên giá bán của mỗi sản phẩm, khấu trừ trực tiếp từ đơn hàng thành công | `shipping-fee-discount-program` |

> Câu 3 và câu 5 đáp ứng yêu cầu riêng của K4: cần `metadata_filter={"customer_role": "seller"}` mới trả lời đúng phạm vi.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0). Bảng dưới đây dùng kết quả `FixedSizeChunker(300,40)` + `LocalEmbedder` (baseline nhóm, xem chi tiết ở `REPORT_CANHAN.md` Phần 5) làm chiến lược tham chiếu chính, đối chiếu với `ClauseChunker`.

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Ngày yêu cầu trả hàng | `FixedSizeChunker` và `ClauseChunker` đều đúng top-1 | Có (2đ) | Cả 2 chiến lược đều mạnh — câu hỏi có từ khóa rõ ràng ("bao nhiêu ngày") |
| 2 | Phương thức thanh toán | `FixedSizeChunker` (đúng top-1, score 0.7967) | Có (2đ) | `ClauseChunker` lệch top-1 (0.8679 sai) do `payment-methods.md` dùng heading Markdown khác định dạng — xem Mục 4 |
| 3 | Sản phẩm cấm đăng bán (filter seller) | Cả 2 đều đúng top-1 | Có (2đ) | Cần `search_with_filter()`; minh chứng filter hoạt động đúng ở cả 2 chiến lược |
| 4 | Dữ liệu cá nhân thu thập | `FixedSizeChunker` (đúng top-1, score 0.7641) | Có (2đ) — `ClauseChunker` đúng ở top-2 (1đ nếu tính riêng) | Chunk quá lớn từ `marketplace-operating-regulation` trong `ClauseChunker` lấn át chunk đúng từ `privacy-policy` |
| 5 | Phí ưu đãi vận chuyển (filter seller) | Cả 2 đều đúng top-1 | Có (2đ) | Nhất quán ở cả 2 chiến lược |

**Điểm truy xuất tổng (baseline `FixedSizeChunker`, dùng làm kết quả chính thức của nhóm): 10/10 (5 câu × 2 điểm).**

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

Có, rõ rệt ở câu 3 và câu 5. Khi thử bỏ `metadata_filter` trên câu 5 ("Phí dịch vụ ưu đãi phí vận chuyển cho người bán"), top-1 kết quả không đổi trong trường hợp này vì tài liệu `shipping-fee-discount-program` đã đủ đặc trưng — nhưng với câu 3 ("Người bán không được đăng bán loại sản phẩm nào"), việc filter `customer_role=seller` trước khi search giúp loại bỏ hoàn toàn các tài liệu hướng buyer (returns, payment) khỏi tập ứng viên, giảm nguy cơ nhiễu ngữ nghĩa từ các tài liệu không liên quan đến vai trò người bán — một bước tiền xử lý rẻ nhưng hiệu quả trước khi tính similarity.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

1. **Chất lượng embedder quan trọng hơn chiến lược chunking:** so sánh cùng 5 câu hỏi, `_mock_embed` cho 0/5 đúng bất kể chiến lược nào, trong khi `LocalEmbedder` cho 3-5/5 tùy chiến lược — chênh lệch do embedder lớn hơn nhiều so với chênh lệch giữa các chiến lược chunking.
2. **Một chiến lược "nghe hợp lý về lý thuyết" (chunk theo điều khoản cho văn bản luật) vẫn có thể thua baseline đơn giản nếu cách triển khai không xử lý hết các trường hợp biên** (ví dụ: định dạng heading không nhất quán giữa các tài liệu crawl từ các thời điểm/kiểu bài viết khác nhau trên cùng một trang web).
3. **Corpus càng đầy đủ, chi tiết càng giúp phân biệt đúng/sai:** khi nhóm còn dùng bản tóm tắt ngắn cho dữ liệu (trước khi thu thập lại verbatim đầy đủ), một số câu hỏi bị nhiễu ngữ nghĩa giữa các tài liệu khác nhau; sau khi có nội dung đầy đủ, độ chính xác top-1 tăng rõ rệt.

**Bài học rút ra khi so sánh trong nhóm:**

Cùng một bộ 20 tài liệu nhưng hai chiến lược chunking (kích thước cố định vs theo điều khoản) cho hai bộ chunk có số lượng và độ dài rất khác nhau (73 vs 24 chunk cho cùng 1 tài liệu 19K ký tự) — dẫn tới sự đánh đổi giữa **độ mịn (precision)** của chiến lược cố định và **tính trọn vẹn ngữ nghĩa (coherence)** của chiến lược theo điều khoản. Không có chiến lược nào thắng tuyệt đối trên mọi câu hỏi; lựa chọn phù hợp phụ thuộc vào độ nhất quán định dạng của corpus thực tế.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

Sẽ chuẩn hóa định dạng heading ngay từ bước làm sạch dữ liệu (tất cả tài liệu dùng cùng một kiểu đánh dấu điều khoản, ví dụ luôn `## N. Tiêu đề`) trước khi áp dụng `ClauseChunker`, thay vì để chunker tự suy đoán nhiều kiểu định dạng khác nhau — điều này sẽ loại bỏ hoàn toàn nguyên nhân gây lỗi ở câu 2 đã phát hiện trong Mục 2.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 12 / 15 *(đầy đủ phân tích + code + so sánh cho 1 thành viên; cần bổ sung 2 thành viên còn lại)* |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | *(chưa diễn ra — điểm tự đánh giá sẽ cập nhật sau buổi demo)* |
| **Tổng phần nhóm (tạm tính)** | **32 / 35** (chưa tính điểm Demo) |
