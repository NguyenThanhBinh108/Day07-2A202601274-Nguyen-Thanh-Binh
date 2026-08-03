const ROLE_COLOR = {
  buyer: "var(--series-buyer)",
  seller: "var(--series-seller)",
  both: "var(--series-both)",
};

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

async function waitUntilReady() {
  const banner = document.getElementById("loading-banner");
  for (;;) {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      if (data.ready) {
        banner.remove();
        return;
      }
    } catch (e) {
      // server chưa lên hẳn, thử lại
    }
    await new Promise((r) => setTimeout(r, 1500));
  }
}

function renderStats(stats) {
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
  chart.innerHTML = "<div style=\"font-size:0.8rem;color:var(--text-muted);margin-bottom:10px;\">Phân bố tài liệu theo customer_role</div>";
  for (const role of roleOrder) {
    const count = stats.role_counts[role] || 0;
    const pct = maxCount ? (count / maxCount) * 100 : 0;
    chart.appendChild(el(`
      <div class="hbar-row">
        <div>${role}</div>
        <div class="hbar-track"><div class="hbar-fill" style="width:${pct}%;background:${ROLE_COLOR[role]}"></div></div>
        <div class="hbar-count">${count}</div>
      </div>
    `));
  }
}

function roleLabel(role) {
  return role ? `<span class="role-pill" style="background:${ROLE_COLOR[role] || "var(--text-muted)"}">${role}</span>` : "";
}

function renderResults(data) {
  const answerBox = document.getElementById("answer-container");
  answerBox.innerHTML = "";
  answerBox.appendChild(el(`
    <div class="answer-box">
      <span class="tag">${data.answer_is_generated ? "Câu trả lời (LLM)" : "Ngữ cảnh trích xuất (extractive — không có LLM key)"}</span>
      ${escapeHtml(data.answer)}
    </div>
  `));

  const resultsBox = document.getElementById("results-container");
  resultsBox.innerHTML = "";
  const maxScore = Math.max(...data.results.map((r) => r.score), 0.0001);
  data.results.forEach((r, i) => {
    const pct = Math.max(0, Math.min(100, (r.score / maxScore) * 100));
    resultsBox.appendChild(el(`
      <div class="result-card">
        <div class="meta">
          <span class="doc-id">#${i + 1} · ${escapeHtml(r.doc_id)}</span>
          ${roleLabel(r.customer_role)}
          <span style="font-variant-numeric:tabular-nums;color:var(--text-secondary);font-size:0.8rem;">score ${r.score.toFixed(4)}</span>
        </div>
        <div class="score-bar-track"><div class="score-bar-fill" style="width:${pct}%"></div></div>
        <div class="content">${escapeHtml(r.content)}</div>
      </div>
    `));
  });
}

async function runQuery() {
  const question = document.getElementById("question").value.trim();
  if (!question) return;
  const strategy = document.getElementById("strategy").value;
  const role = document.getElementById("role").value;
  const btn = document.getElementById("btn-search");
  btn.disabled = true;
  btn.textContent = "Đang tìm...";
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
    btn.textContent = "Tìm kiếm";
  }
}

function renderBenchmark(payload) {
  const box = document.getElementById("benchmark-container");
  const rows = payload.results
    .map((row, i) => {
      const fixed = row.strategies.fixed_size;
      const clause = row.strategies.clause;
      const iconFor = (s) => (s.correct
        ? '<span class="status-icon status-good">✓</span>'
        : '<span class="status-icon status-critical">✗</span>');
      return `
        <tr>
          <td>${i + 1}</td>
          <td>${escapeHtml(row.question)}${row.customer_role ? ` <span class="role-pill" style="background:${ROLE_COLOR[row.customer_role]}">${row.customer_role}</span>` : ""}</td>
          <td>${iconFor(fixed)} ${escapeHtml(fixed.top1_doc_id || "")} (${fixed.top1_score})</td>
          <td>${iconFor(clause)} ${escapeHtml(clause.top1_doc_id || "")} (${clause.top1_score})</td>
        </tr>`;
    })
    .join("");

  const totalFixed = payload.results.filter((r) => r.strategies.fixed_size.correct).length;
  const totalClause = payload.results.filter((r) => r.strategies.clause.correct).length;

  box.innerHTML = `
    <table class="bench">
      <thead><tr><th>#</th><th>Câu hỏi</th><th>FixedSizeChunker</th><th>ClauseChunker (custom)</th></tr></thead>
      <tbody>${rows}</tbody>
      <tfoot><tr>
        <td colspan="2"><strong>Tổng đúng top-1</strong></td>
        <td><strong>${totalFixed} / 5</strong></td>
        <td><strong>${totalClause} / 5</strong></td>
      </tr></tfoot>
    </table>
    <p class="note">Không có <code>OPENAI_API_KEY</code>: bảng trên so sánh độ chính xác truy xuất (top-1 đúng tài liệu kỳ vọng), không đo chất lượng câu trả lời sinh tự động.</p>
  `;
}

async function main() {
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
