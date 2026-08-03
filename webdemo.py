"""
webdemo.py — giao diện web để demo trực tiếp hệ RAG của nhóm.

Chạy hệ THẬT: đúng gói `src/` của từng thành viên, đúng corpus `data/k4_ecommerce`,
đúng embedder đa ngữ. Người dùng nhập câu hỏi tự do, đổi chiến lược chunking và
bật/tắt bộ lọc metadata ngay trên giao diện rồi xem top-3 đổi thế nào.

Chỉ dùng thư viện chuẩn của Python (http.server) — không cần cài thêm gì.

Chạy:
    $env:EMBEDDING_PROVIDER="local"
    python webdemo.py                 # rồi mở http://127.0.0.1:8000
    python webdemo.py --port 8080
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from bench import BENCHMARK, DATA_DIR, _chuan_hoa, llm_trich_xuat  # noqa: E402
from ingest import chunk_document, load_documents  # noqa: E402
from main import _select_embedder  # noqa: E402

# Năm chiến lược của năm thành viên. Khoá là giá trị gửi lên từ giao diện.
CHIEN_LUOC = {
    "clause": ("Bình — ClauseChunker(1 câu)", "Nguyen-Thanh-Binh-2A202601274", "ClauseChunker", dict(max_sentences_per_clause=1)),
    "clause-nohead": ("Bình — ClauseChunker BỎ tiêu đề", "Nguyen-Thanh-Binh-2A202601274", "ClauseChunker", dict(max_sentences_per_clause=1, keep_heading=False)),
    "recursive": ("Vũ — RecursiveChunker(400)", "Tran-Chi-Vu-2A202601044", "RecursiveChunker", dict(chunk_size=400)),
    "fixed500": ("Đăng — FixedSizeChunker(500, 50)", "Trinh-Hai-Dang-2A202601602", "FixedSizeChunker", dict(chunk_size=500, overlap=50)),
    "fixed250": ("Liễu — FixedSizeChunker(250, 100)", "Do-Thu-Lieu-2A202601898", "FixedSizeChunker", dict(chunk_size=250, overlap=100)),
    "sentence": ("Linh — SentenceChunker(3 câu)", "Do-Van-Linh-2A202601190", "SentenceChunker", dict(max_sentences_per_chunk=3)),
}

_embedder = None
_cache: dict[str, tuple] = {}  # khoá chiến lược -> (store, agent, module src)


def _nap_src(thu_muc: str):
    for ten in [m for m in list(sys.modules) if m == "src" or m.startswith("src.")]:
        del sys.modules[ten]
    sys.path.insert(0, str(REPO_ROOT / thu_muc))
    try:
        return importlib.import_module("src")
    finally:
        sys.path.pop(0)


def lay_store(khoa: str):
    """Dựng (hoặc lấy từ cache) store + agent cho một chiến lược."""
    if khoa in _cache:
        return _cache[khoa]

    _, thu_muc, ten_chunker, tham_so = CHIEN_LUOC[khoa]
    src = _nap_src(thu_muc)
    chunker = getattr(src, ten_chunker)(**tham_so)

    chunk_docs = []
    for doc in load_documents(DATA_DIR):
        for c in chunk_document(doc, chunker):
            chunk_docs.append(src.Document(id=c.id, content=c.content, metadata=c.metadata))

    store = src.EmbeddingStore(collection_name=f"web-{khoa}", embedding_fn=_embedder)
    store.add_documents(chunk_docs)
    agent = src.KnowledgeBaseAgent(store=store, llm_fn=llm_trich_xuat)
    _cache[khoa] = (store, agent)
    print(f"  [đã nạp] {CHIEN_LUOC[khoa][0]} — {store.get_collection_size()} đoạn")
    return _cache[khoa]


def tim_gold(query: str) -> dict | None:
    """Nếu câu hỏi trùng một trong 5 câu benchmark thì trả về đáp án chuẩn để đối chiếu."""
    q = _chuan_hoa(query)
    for item in BENCHMARK:
        if _chuan_hoa(item["query"]) == q:
            return item
    return None


def xu_ly_tim(payload: dict) -> dict:
    query = (payload.get("query") or "").strip()
    khoa = payload.get("strategy") or "clause"
    dung_loc = bool(payload.get("use_filter"))
    vai = payload.get("role") or "seller"

    if not query:
        return {"error": "Chưa nhập câu hỏi."}
    if khoa not in CHIEN_LUOC:
        return {"error": f"Không có chiến lược '{khoa}'."}

    store, agent = lay_store(khoa)
    loc = {"customer_role": vai} if dung_loc else None

    bat_dau = time.perf_counter()
    ket_qua = store.search_with_filter(query, top_k=3, metadata_filter=loc)
    try:
        tra_loi = agent.answer(query, top_k=3, metadata_filter=loc)
    except TypeError:
        tra_loi = agent.answer(query, top_k=3)
    mili_giay = round((time.perf_counter() - bat_dau) * 1000)

    item = tim_gold(query)
    snippet = item["gold_snippet"] if item else None

    chunks = []
    for i, r in enumerate(ket_qua, start=1):
        noi_dung = r.get("content", "")
        chunks.append({
            "rank": i,
            "score": round(float(r.get("score", 0.0)), 4),
            "doc_id": (r.get("metadata") or {}).get("doc_id", "?"),
            "role": (r.get("metadata") or {}).get("customer_role", "?"),
            "category": (r.get("metadata") or {}).get("category", "?"),
            "content": noi_dung,
            "is_gold": bool(snippet and _chuan_hoa(snippet) in _chuan_hoa(noi_dung)),
        })

    return {
        "query": query,
        "strategy": CHIEN_LUOC[khoa][0],
        "total_chunks": store.get_collection_size(),
        "filter": loc,
        "elapsed_ms": mili_giay,
        "chunks": chunks,
        "answer": tra_loi,
        "gold": {"answer": item["gold"], "snippet": snippet, "doc": item["gold_doc"]} if item else None,
        "answer_ok": bool(snippet and _chuan_hoa(snippet) in _chuan_hoa(tra_loi)),
    }


TRANG = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demo truy xuất — Lab 7 K4</title>
<style>
:root{--bg:#eff2f1;--fg:#101a1b;--muted:#5d6b6a;--line:#cfd8d6;--panel:#fff;--panel2:#e5eae8;
--teal:#0f5d54;--gold:#8f6613;--clay:#a34a3a;
--sans:system-ui,"Segoe UI",Roboto,Arial,sans-serif;--mono:"Cascadia Mono",ui-monospace,Consolas,monospace}
@media(prefers-color-scheme:dark){:root{--bg:#0b1213;--fg:#e6ecea;--muted:#93a3a1;--line:#24312f;
--panel:#121b1c;--panel2:#182324;--teal:#4fb8a5;--gold:#d9a441;--clay:#e08471}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);line-height:1.55}
.wrap{width:min(1060px,94vw);margin:0 auto;padding:2.2rem 0 4rem;display:flex;flex-direction:column;gap:1.4rem}
h1{font-size:clamp(1.5rem,3vw,2.1rem);font-weight:800;letter-spacing:-.02em;margin:0}
.sub{color:var(--muted);margin:0;font-size:.95rem}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:var(--teal);font-weight:600}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:1.1rem 1.2rem;
display:flex;flex-direction:column;gap:.85rem}
label{font-family:var(--mono);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:.35rem}
textarea,select{font:inherit;width:100%;padding:.6rem .7rem;border-radius:4px;border:1px solid var(--line);
background:var(--bg);color:var(--fg)}
textarea{min-height:4.6rem;resize:vertical}
.row{display:grid;grid-template-columns:1fr auto auto;gap:.85rem;align-items:end}
.chk{display:flex;align-items:center;gap:.45rem;font-size:.9rem;white-space:nowrap}
button{font:inherit;font-family:var(--mono);font-size:.85rem;padding:.62rem 1.15rem;border-radius:4px;
cursor:pointer;border:1px solid var(--teal);background:var(--teal);color:var(--bg);font-weight:600}
button.ghost{background:transparent;color:var(--teal)}
button:disabled{opacity:.5;cursor:progress}
button:focus-visible,textarea:focus-visible,select:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.samples{display:flex;flex-wrap:wrap;gap:.4rem}
.samples button{font-size:.76rem;padding:.34rem .6rem;background:var(--panel2);color:var(--fg);border-color:var(--line);font-weight:500}
.hit{display:flex;flex-wrap:wrap;gap:.5rem 1.4rem;font-family:var(--mono);font-size:.8rem;color:var(--muted)}
.chunk{border:1px solid var(--line);border-left:3px solid var(--muted);border-radius:5px;padding:.8rem .9rem;
background:var(--panel);display:flex;flex-direction:column;gap:.45rem}
.chunk.gold{border-left-color:var(--gold);background:color-mix(in srgb,var(--gold) 8%,var(--panel))}
.chead{display:flex;flex-wrap:wrap;gap:.4rem .9rem;align-items:baseline;font-family:var(--mono);font-size:.78rem}
.rk{font-weight:700;color:var(--teal)}
.sc{color:var(--muted);font-variant-numeric:tabular-nums}
.pill{font-size:.7rem;padding:.1rem .4rem;border-radius:3px;background:var(--panel2);color:var(--muted)}
.pill.g{background:color-mix(in srgb,var(--gold) 22%,transparent);color:var(--gold);font-weight:650}
.ctext{font-size:.9rem;white-space:pre-wrap}
.ans{border-left:3px solid var(--teal);padding:.15rem 0 .15rem 1rem;font-size:1rem}
.ans.bad{border-left-color:var(--clay)}
.gold-box{font-size:.88rem;color:var(--muted);border-top:1px dashed var(--line);padding-top:.7rem}
mark{background:color-mix(in srgb,var(--gold) 35%,transparent);color:inherit;padding:0 .12em;border-radius:2px}
.err{color:var(--clay);font-weight:600}
@media(max-width:680px){.row{grid-template-columns:1fr}}
</style></head><body><div class="wrap">

<div>
  <p class="eyebrow">Lab 7 · K4 · Chính sách thương mại điện tử</p>
  <h1>Thử truy xuất trực tiếp</h1>
  <p class="sub">Chạy trên hệ thật của nhóm: corpus 10 tài liệu Shopee, embedder đa ngữ, và đúng mã nguồn của từng thành viên. Đổi chiến lược để xem thứ hạng thay đổi thế nào.</p>
</div>

<div class="panel">
  <div>
    <label for="q">Câu hỏi</label>
    <textarea id="q" placeholder="Ví dụ: Người bán bị xử lý thế nào nếu đăng bán hàng cấm?"></textarea>
  </div>
  <div>
    <label>Hoặc chọn nhanh một câu đánh giá của nhóm</label>
    <div class="samples" id="samples"></div>
  </div>
  <div class="row">
    <div>
      <label for="s">Chiến lược chia nhỏ</label>
      <select id="s"></select>
    </div>
    <div class="chk">
      <input type="checkbox" id="f"><label for="f" style="margin:0;text-transform:none;letter-spacing:0;font-family:var(--sans);font-size:.9rem;color:var(--fg)">Lọc metadata</label>
      <select id="r" style="width:auto"><option value="seller">seller</option><option value="buyer">buyer</option><option value="both">both</option></select>
    </div>
    <button id="go">Tìm</button>
  </div>
</div>

<div id="out"></div>

</div><script>
const CL = __CHIEN_LUOC__, MAU = __CAU_MAU__;
const $ = id => document.getElementById(id);

CL.forEach(([k, ten]) => { const o = document.createElement('option'); o.value = k; o.textContent = ten; $('s').appendChild(o); });
MAU.forEach((q, i) => {
  const b = document.createElement('button');
  b.textContent = 'Câu ' + (i + 1);
  b.title = q;
  b.onclick = () => { $('q').value = q; $('f').checked = (i === 2); tim(); };
  $('samples').appendChild(b);
});

function esc(s){ return s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
function toDau(text, snippet){
  if(!snippet) return esc(text);
  const i = text.toLowerCase().indexOf(snippet.toLowerCase());
  if(i < 0) return esc(text);
  return esc(text.slice(0,i)) + '<mark>' + esc(text.slice(i, i+snippet.length)) + '</mark>' + esc(text.slice(i+snippet.length));
}

async function tim(){
  const q = $('q').value.trim();
  if(!q){ $('out').innerHTML = '<p class="err">Chưa nhập câu hỏi.</p>'; return; }
  $('go').disabled = true; $('go').textContent = 'Đang tìm…';
  $('out').innerHTML = '<p class="sub">Đang nhúng câu hỏi và xếp hạng… (lần đầu đổi chiến lược sẽ lâu hơn vì phải nhúng lại toàn bộ corpus)</p>';
  try{
    const res = await fetch('/api/search', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({query:q, strategy:$('s').value, use_filter:$('f').checked, role:$('r').value})
    });
    ve(await res.json());
  }catch(e){
    $('out').innerHTML = '<p class="err">Lỗi gọi máy chủ: ' + esc(String(e)) + '</p>';
  }finally{
    $('go').disabled = false; $('go').textContent = 'Tìm';
  }
}

function ve(d){
  if(d.error){ $('out').innerHTML = '<p class="err">' + esc(d.error) + '</p>'; return; }
  const snip = d.gold ? d.gold.snippet : null;
  let h = '<div class="panel"><div class="hit">'
    + '<span>' + esc(d.strategy) + '</span>'
    + '<span>' + d.total_chunks + ' đoạn trong kho</span>'
    + '<span>' + d.elapsed_ms + ' ms</span>'
    + '<span>' + (d.filter ? 'lọc ' + esc(JSON.stringify(d.filter)) : 'không lọc') + '</span>'
    + '</div>';

  h += '<div class="ans' + (d.gold && !d.answer_ok ? ' bad' : '') + '"><strong>Tác tử trả lời:</strong> ' + esc(d.answer) + '</div>';

  if(d.gold){
    h += '<div class="gold-box"><strong>Đáp án chuẩn:</strong> ' + esc(d.gold.answer)
      + ' <span class="pill">' + esc(d.gold.doc) + '</span> — '
      + (d.answer_ok ? '<span style="color:var(--teal);font-weight:650">tác tử trả lời đúng</span>'
                     : '<span style="color:var(--clay);font-weight:650">tác tử chưa nêu được đáp án</span>')
      + '</div>';
  }
  h += '</div>';

  d.chunks.forEach(c => {
    h += '<div class="chunk' + (c.is_gold ? ' gold' : '') + '" style="margin-top:.7rem">'
      + '<div class="chead"><span class="rk">#' + c.rank + '</span>'
      + '<span class="sc">score ' + c.score.toFixed(4) + '</span>'
      + '<span class="pill">' + esc(c.doc_id) + '</span>'
      + '<span class="pill">' + esc(c.role) + '</span>'
      + '<span class="pill">' + esc(c.category) + '</span>'
      + (c.is_gold ? '<span class="pill g">chứa đáp án</span>' : '')
      + '</div><div class="ctext">' + toDau(c.content, c.is_gold ? snip : null) + '</div></div>';
  });

  if(!d.chunks.length) h += '<p class="err" style="margin-top:.7rem">Bộ lọc không giữ lại đoạn nào. Thử tắt lọc hoặc đổi vai.</p>';
  $('out').innerHTML = h;
}

$('go').onclick = tim;
$('q').addEventListener('keydown', e => { if(e.key === 'Enter' && (e.ctrlKey || e.metaKey)) tim(); });
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # bớt log rác ra terminal khi demo
        pass

    def _gui(self, code: int, body: bytes, kieu: str):
        self.send_response(code)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            return self._gui(404, b"not found", "text/plain; charset=utf-8")
        trang = TRANG.replace(
            "__CHIEN_LUOC__", json.dumps([[k, v[0]] for k, v in CHIEN_LUOC.items()], ensure_ascii=False)
        ).replace(
            "__CAU_MAU__", json.dumps([i["query"] for i in BENCHMARK], ensure_ascii=False)
        )
        self._gui(200, trang.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/search":
            return self._gui(404, b"not found", "text/plain; charset=utf-8")
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
            ket_qua = xu_ly_tim(payload)
        except Exception as loi:  # noqa: BLE001 — demo: trả lỗi ra giao diện thay vì sập
            ket_qua = {"error": f"{type(loi).__name__}: {loi}"}
        self._gui(200, json.dumps(ket_qua, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")


def main() -> int:
    global _embedder
    parser = argparse.ArgumentParser(description="Web demo truy xuất Lab 7 K4")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--warm", default="clause", help="Chiến lược nạp sẵn lúc khởi động")
    args = parser.parse_args()

    print("Đang nạp embedder…")
    _embedder = _select_embedder()
    backend = getattr(_embedder, "_backend_name", _embedder.__class__.__name__)
    print(f"Backend: {backend}")
    if backend == "mock embeddings fallback":
        print("CẢNH BÁO: đang dùng mock — đặt EMBEDDING_PROVIDER=local để demo có ý nghĩa.")

    print(f"Đang nạp corpus {DATA_DIR}…")
    lay_store(args.warm)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"\n  Mở trình duyệt tại  http://{args.host}:{args.port}\n  Ctrl+C để dừng.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
