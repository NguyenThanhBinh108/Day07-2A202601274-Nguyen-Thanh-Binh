"""
ClauseChunker — chiến lược chunking tùy chỉnh cho chủ đề chính sách TMĐT Shopee (K4).

Ý tưởng thiết kế: các tài liệu chính sách/điều khoản Shopee đều được viết theo cấu trúc
điều khoản đánh số ở cấp cao nhất, dạng "**1. Tên điều khoản**" hoặc "## 1. Tên điều khoản".
Việc chunk theo ranh giới điều khoản (thay vì theo kích thước ký tự cố định) giữ nguyên
trọn vẹn ngữ nghĩa của từng điều khoản — mỗi chunk là một đơn vị pháp lý hoàn chỉnh,
đúng với cách người dùng thực tế tra cứu ("Điều 3 nói gì?", "mục nào quy định phí hoàn trả?").

Với các đoạn con quá dài trong một điều khoản, tiếp tục chia theo đoạn văn (\n\n) để
không tạo ra chunk quá khổ vượt embedding context hiệu quả.

Dùng trong `report/REPORT_NHOM.md` Mục 2 (so sánh chiến lược) và trong `demo/server.py`
để cho phép demo trực tiếp so sánh baseline vs custom lúc thuyết trình.
"""
from __future__ import annotations

import re


class ClauseChunker:
    """Chia nhỏ theo ranh giới điều/khoản (heading đánh số) cho văn bản chính sách Shopee.

    Lý do thiết kế: tài liệu nguồn là văn bản pháp lý/điều khoản có cấu trúc đánh số rõ
    ràng ở cấp 1 (vd "**1. Tên điều khoản**"). Chunk theo điều khoản giữ nguyên ngữ cảnh
    pháp lý trọn vẹn, phù hợp hơn cắt theo kích thước cố định cho loại văn bản này.
    """

    NUMBERED_LINE = re.compile(r"^\d{1,2}\.\s+\S.*$")
    MAX_CHUNK_SIZE = 1200
    MAX_HEADING_LEN = 100

    def _is_heading(self, line: str) -> bool:
        stripped = line.strip()
        if stripped.startswith("**") and stripped.endswith("**"):
            inner = stripped[2:-2].strip()
        else:
            inner = stripped
        if not self.NUMBERED_LINE.match(inner):
            return False
        if len(inner) > self.MAX_HEADING_LEN:
            return False
        # Loại trừ mục con dạng liệt kê (thường kết thúc bằng dấu câu ; hoặc ,)
        if inner.rstrip().endswith((";", ",")):
            return False
        body = re.sub(r"^\d{1,2}\.\s+", "", inner)
        letters = [c for c in body if c.isalpha()]
        if not letters:
            return False
        is_upper = all(c.isupper() for c in letters)
        is_bold = stripped.startswith("**")
        return is_upper or is_bold

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        lines = text.splitlines()
        heading_line_indices = [i for i, l in enumerate(lines) if self._is_heading(l)]
        if not heading_line_indices:
            return [p.strip() for p in text.split("\n\n") if p.strip()]

        # Chuyển chỉ số dòng heading thành vị trí ký tự trong text
        line_offsets = []
        pos = 0
        for l in lines:
            line_offsets.append(pos)
            pos += len(l) + 1  # +1 cho ký tự xuống dòng
        heading_positions = [line_offsets[i] for i in heading_line_indices]

        chunks: list[str] = []
        intro = text[: heading_positions[0]].strip()
        if intro:
            chunks.append(intro)

        for i, start in enumerate(heading_positions):
            end = heading_positions[i + 1] if i + 1 < len(heading_positions) else len(text)
            section = text[start:end].strip()
            if not section:
                continue
            if len(section) <= self.MAX_CHUNK_SIZE:
                chunks.append(section)
            else:
                # Điều khoản quá dài -> chia tiếp theo đoạn văn, gộp tới MAX_CHUNK_SIZE
                paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
                buffer = ""
                for p in paragraphs:
                    candidate = f"{buffer}\n\n{p}" if buffer else p
                    if len(candidate) <= self.MAX_CHUNK_SIZE:
                        buffer = candidate
                    else:
                        if buffer:
                            chunks.append(buffer)
                        buffer = p
                if buffer:
                    chunks.append(buffer)

        return chunks
