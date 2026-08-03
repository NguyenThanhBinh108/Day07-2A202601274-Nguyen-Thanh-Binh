const ROLE_COLOR = {
  buyer: "var(--series-buyer)",
  seller: "var(--series-seller)",
  both: "var(--series-both)",
};

const ICON_SUN = '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>';
const ICON_MOON = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';

const STAGE_ICONS = {
  doc: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
  ingest: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
  chunk: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>',
  embed: '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/>',
  store: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
  agent: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
  arrow: '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
  check: '<polyline points="20 6 9 17 4 12"/>',
  x: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
};

function svg(path, cls) {
  return `<svg class="${cls || ""}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${path}</svg>`;
}

function el(html) {
  const div = document.createElement("div");
  div.innerHTML = html.trim();
  return div.firstElementChild;
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

/* ---------------- theme toggle ---------------- */
function initTheme() {
  const root = document.documentElement;
  const iconEl = document.getElementById("theme-icon");
  const stored = localStorage.getItem("demo-theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  let isDark = stored ? stored === "dark" : prefersDark;

  function apply() {
    root.setAttribute("data-theme", isDark ? "dark" : "light");
    iconEl.innerHTML = isDark ? ICON_SUN : ICON_MOON;
  }
  apply();

  document.getElementById("theme-toggle").addEventListener("click", () => {
    isDark = !isDark;
    localStorage.setItem("demo-theme", isDark ? "dark" : "light");
    apply();
  });
}

/* ---------------- pipeline diagram ---------------- */
function renderPipeline() {
  const stages = [
    ["doc", "data/*.md", "Front matter + nội dung verbatim đầy đủ"],
    ["ingest", "ingest.py", "Parse metadata, gắn vào từng chunk"],
    ["chunk", "chunking.py", "FixedSizeChunker / ClauseChunker (custom)"],
    ["embed", "LocalEmbedder", "sentence-transformers đa ngữ"],
    ["store", "EmbeddingStore", "search() / search_with_filter()"],
    ["agent", "KnowledgeBaseAgent", "retrieve → answer"],
  ];
  const box = document.getElementById("pipeline");
  box.innerHTML = "";
  stages.forEach(([icon, title, desc], i) => {
    box.appendChild(el(`
      <div class="stage">
        <div class="icon">${svg(STAGE_ICONS[icon])}</div>
        <h3>${title}</h3>
        <p>${desc}</p>
      </div>
    `));
    if (i < stages.length - 1) {
      box.appendChild(el(`<div class="arrow">${svg(STAGE_ICONS.arrow)}</div>`));
    }
  });
}

/* ---------------- readiness ---------------- */
async function waitUntilReady() {
  for (;;) {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      if (data.ready) {
        const banner = document.getElementById("loading-banner");
        if (banner) banner.remove();
        return;
      }
    } catch (e) { /* server chưa lên hẳn, thử lại */ }
    await new Promise((r) => setTimeout(r, 1500));
  }
}

/* ---------------- stats ---------------- */
function renderStats(stats) {
  const heroValues = document.querySelectorAll("#hero-stats .value");
  heroValues[0].textContent = stats.doc_count;
  heroValues[1].textContent = stats.chunk_counts.fixed_size.toLocaleString("vi-VN");

  const tiles = document.getElementById("stat-tiles");
  const tileData = [
    [stats.doc_count, "tài liệu"],
    [stats.chunk_counts.fixed_size, "chunk (FixedSizeChunker)"],
    [stats.chunk_counts.clause, "chunk (ClauseChunker)"],
    [stats.total_chars.toLocaleString("vi-VN"), "ký tự nội dung"],
  ];
  tiles.innerHTML = "";
  for (const [value, label] of tileData) {
    tiles.appendChild(el(`<div class="tile"><div class="value">${value}</div><div class="label">${label}</div></div>`));
  }

  const roleOrder = ["buyer", "seller", "both"];
  const maxCount = Math.max(...roleOrder.map((r) => stats.role_counts[r] || 0));
  const chart = document.getElementById("role-chart");
  chart.innerHTML = '<div class="viz-title">Phân bố tài liệu theo customer_role</div>';
  for (const role of roleOrder) {
    const count = stats.role_counts[role] || 0;
    const row = el(`
      <div class="hbar-row">
        <div>${role}</div>
        <div class="hbar-track"><div class="hbar-fill" style="width:0%;background:${ROLE_COLOR[role]}"></div></div>
        <div class="hbar-count">${count}</div>
      </div>
    `);
    chart.appendChild(row);
    const pct = maxCount ? (count / maxCount) * 100 : 0;
    requestAnimationFrame(() => { row.querySelector(".hbar-fill").style.width = pct + "%"; });
  }
}

/* ---------------- query demo ---------------- */
const EXAMPLE_QUESTIONS = [
  "Người mua có thể trả hàng trong bao lâu?",
  "Shopee hỗ trợ những phương thức thanh toán nào?",
  "Phí ưu đãi vận chuyển cho người bán là bao nhiêu?",
  "Shopee thu thập dữ liệu cá nhân gì?",
];

function renderExampleChips() {
  const box = document.getElementById("example-chips");
  box.innerHTML = "";
  EXAMPLE_QUESTIONS.forEach((q) => {
    const chip = el(`<button type="button" class="chip">${escapeHtml(q)}</button>`);
    chip.addEventListener("click", () => {
      document.getElementById("question").value = q;
      runQuery();
    });
    box.appendChild(chip);
  });
}

function roleLabel(role) {
  return role ? `<span class="role-pill" style="background:${ROLE_COLOR[role] || "var(--text-muted)"}">${role}</span>` : "";
}

function renderResults(data) {
  const answerBox = document.getElementById("answer-container");
  answerBox.innerHTML = "";
  answerBox.appendChild(el(`
    <div class="answer-box">
      <span class="tag">${data.answer_is_generated ? "Câu trả lời (LLM)" : "Ngữ cảnh trích xuất — không có LLM key"}</span>
      <div>${escapeHtml(data.answer)}</div>
    </div>
  `));

  const resultsBox = document.getElementById("results-container");
  resultsBox.innerHTML = "";
  const maxScore = Math.max(...data.results.map((r) => r.score), 0.0001);
  data.results.forEach((r, i) => {
    const pct = Math.max(0, Math.min(100, (r.score / maxScore) * 100));
    const card = el(`
      <div class="result-card">
        <div class="meta">
          <span class="rank">${i + 1}</span>
          <span class="doc-id">${escapeHtml(r.doc_id)}</span>
          ${roleLabel(r.customer_role)}
          <span class="score-label">score ${r.score.toFixed(4)}</span>
        </div>
        <div class="score-bar-track"><div class="score-bar-fill" style="width:0%"></div></div>
        <div class="content">${escapeHtml(r.content)}</div>
        <span class="expand-hint">Xem đầy đủ</span>
      </div>
    `);
    const contentEl = card.querySelector(".content");
    const hintEl = card.querySelector(".expand-hint");
    const toggle = () => {
      const expanded = contentEl.classList.toggle("expanded");
      hintEl.textContent = expanded ? "Thu gọn" : "Xem đầy đủ";
    };
    contentEl.addEventListener("click", toggle);
    hintEl.addEventListener("click", toggle);
    resultsBox.appendChild(card);
    requestAnimationFrame(() => { card.querySelector(".score-bar-fill").style.width = pct + "%"; });
  });
}

async function runQuery() {
  const question = document.getElementById("question").value.trim();
  if (!question) return;
  const strategy = document.getElementById("strategy").value;
  const role = document.getElementById("role").value;
  const btn = document.getElementById("btn-search");
  btn.disabled = true;
  const originalLabel = btn.textContent;
  btn.textContent = "Đang tìm…";
  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, strategy, customer_role: role || null, top_k: 3 }),
    });
    const data = await res.json();
    if (data.error) {
      alert(data.error);
      return;
    }
    renderResults(data);
  } finally {
    btn.disabled = false;
    btn.textContent = originalLabel;
  }
}

/* ---------------- benchmark ---------------- */
function statusPill(correct) {
  return correct
    ? `<span class="status-pill good">${svg(STAGE_ICONS.check)} đúng</span>`
    : `<span class="status-pill critical">${svg(STAGE_ICONS.x)} sai</span>`;
}

function renderBenchmark(payload) {
  const box = document.getElementById("benchmark-container");
  const rows = payload.results
    .map((row, i) => {
      const fixed = row.strategies.fixed_size;
      const clause = row.strategies.clause;
      return `
        <tr>
          <td>${i + 1}</td>
          <td>${escapeHtml(row.question)}${row.customer_role ? ` <span class="role-pill" style="background:${ROLE_COLOR[row.customer_role]}">${row.customer_role}</span>` : ""}</td>
          <td>${statusPill(fixed.correct)}<br><span style="color:var(--text-muted);font-size:0.78rem;">${escapeHtml(fixed.top1_doc_id || "")} · ${fixed.top1_score}</span></td>
          <td>${statusPill(clause.correct)}<br><span style="color:var(--text-muted);font-size:0.78rem;">${escapeHtml(clause.top1_doc_id || "")} · ${clause.top1_score}</span></td>
        </tr>`;
    })
    .join("");

  const totalFixed = payload.results.filter((r) => r.strategies.fixed_size.correct).length;
  const totalClause = payload.results.filter((r) => r.strategies.clause.correct).length;

  const heroValues = document.querySelectorAll("#hero-stats .value");
  heroValues[3].textContent = `${totalFixed}/5`;

  box.innerHTML = `
    <div class="table-scroll">
      <table class="bench">
        <thead><tr><th>#</th><th>Câu hỏi</th><th>FixedSizeChunker</th><th>ClauseChunker (custom)</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot><tr>
          <td colspan="2">Tổng đúng top-1</td>
          <td>${totalFixed} / 5</td>
          <td>${totalClause} / 5</td>
        </tr></tfoot>
      </table>
    </div>
    <p class="note">
      ${svg(STAGE_ICONS.embed)}
      Không có <code>OPENAI_API_KEY</code>: bảng trên so sánh độ chính xác truy xuất (top-1 đúng tài liệu kỳ vọng), không đo chất lượng câu trả lời sinh tự động.
    </p>
  `;
}

async function main() {
  initTheme();
  renderPipeline();
  renderExampleChips();
  await waitUntilReady();
  const [statsRes, benchRes] = await Promise.all([fetch("/api/stats"), fetch("/api/benchmark")]);
  renderStats(await statsRes.json());
  renderBenchmark(await benchRes.json());

  const btn = document.getElementById("btn-search");
  btn.disabled = false;
  btn.addEventListener("click", runQuery);
  document.getElementById("question").addEventListener("keydown", (e) => {
    if (e.key === "Enter") runQuery();
  });
}

main();
