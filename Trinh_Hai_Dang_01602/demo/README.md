# Demo trực tiếp (dùng khi thuyết trình)

Giao diện web chạy **pipeline RAG thật** từ `src/` (không phải dữ liệu tĩnh giả lập): `LocalEmbedder` + `EmbeddingStore` + `KnowledgeBaseAgent`, trên bộ 20 tài liệu Shopee đã thu thập ở `data/k4_ecommerce/`. So sánh trực tiếp 2 chiến lược chunking (`FixedSizeChunker` baseline vs `ClauseChunker` tùy chỉnh) trên cùng một câu hỏi.

## Cài đặt (một lần)

```bash
cd Trinh_Hai_Dang_01602
pip install -r requirements.txt
pip install -r requirements-local.txt        # bắt buộc — cần LocalEmbedder thật
pip install -r demo/requirements-demo.txt    # Flask
```

## Chạy trước buổi thuyết trình

```bash
python demo/server.py
```

**Lần đầu chạy** sẽ tải model đa ngữ (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, ~20-40s) rồi nhúng vector cho ~1.900 chunk theo cả 2 chiến lược (~1-2 phút, chỉ CPU) — kết quả nhúng được **lưu cache** vào `demo/.cache/*.pkl`.

**Các lần chạy sau** (dữ liệu không đổi): chỉ mất **~30-35 giây** — hầu như toàn bộ thời gian là tải lại model (không thể cache phần này vì cần model để nhúng câu hỏi mới lúc demo trực tiếp), phần nạp ~1900 chunk từ cache chỉ mất dưới 1 giây thay vì phải nhúng lại từ đầu.

Cache tự động **vô hiệu hóa nếu bạn sửa/thêm/xóa** bất kỳ file nào trong `data/k4_ecommerce/` (dựa trên hash tên file + thời điểm sửa đổi) — không lo phục vụ dữ liệu cũ.

Khi thấy dòng:

```
[demo] San sang. Mo http://127.0.0.1:5000
```

→ mở trình duyệt tại **http://127.0.0.1:5000**.

> Nên khởi động server **trước** khi vào phòng thuyết trình vài phút để không phải chờ trực tiếp trên lớp. Nếu đã chạy ít nhất 1 lần trước đó trên cùng máy, lần khởi động tiếp theo sẽ rất nhanh nhờ cache.

> **Nếu server không khởi động được vì cổng 5000 đã bị chiếm:** có thể một tiến trình `python demo/server.py` cũ từ lần chạy trước chưa tắt hẳn. Tìm và dừng nó (Windows: `tasklist` tìm `python.exe` rồi `taskkill /F /PID <pid>`; macOS/Linux: `lsof -i :5000` rồi `kill <pid>`), sau đó chạy lại.

## Có gì trong trang demo

1. **Kiến trúc pipeline** — sơ đồ các bước từ dữ liệu thô đến câu trả lời.
2. **Dữ liệu** — số liệu tổng quan (20 tài liệu, số chunk theo từng chiến lược, phân bố `customer_role`).
3. **Truy vấn trực tiếp** — ô nhập câu hỏi bất kỳ, chọn chiến lược chunking + lọc `customer_role`, bấm tìm kiếm → gọi thẳng `EmbeddingStore.search()`/`search_with_filter()` thật, hiển thị top-3 kết quả kèm điểm số.
4. **Benchmark 5 câu hỏi** — bảng so sánh sẵn giữa `FixedSizeChunker` (5/5 đúng) và `ClauseChunker` (3/5 đúng), tính lại mỗi lần khởi động server.

> Không có `OPENAI_API_KEY` trong môi trường này nên "câu trả lời" hiển thị là đoạn ngữ cảnh đã truy xuất (extractive), không phải văn bản do LLM sinh — giao diện có ghi chú rõ điều này, không giả vờ là câu trả lời sinh tự động.

## Dừng server

`Ctrl+C` trong terminal đang chạy.
