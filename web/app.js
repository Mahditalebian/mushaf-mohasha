const form = document.getElementById("form");
const input = document.getElementById("q");
const out = document.getElementById("out");
const statusEl = document.getElementById("status");

function setStatus(text, show = true) {
  statusEl.hidden = !show;
  statusEl.textContent = text || "";
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderVerse(v) {
  const marks = (v.marks || [])
    .map(
      (m) => `<tr>
        <td class="waqf">وقف روی «${esc(m.waqf_on)}»</td>
        <td>${esc(m.letter)} / ${esc(m.name)} ${esc(m.symbol)}</td>
        <td class="ibtida">ابتدا از «${esc(m.ibtida_from || "آیهٔ بعد")}»</td>
        <td>${esc(m.rule)}</td>
      </tr>`
    )
    .join("");
  const table = marks
    ? `<table>
        <thead><tr><th>وقف روی</th><th>علامت</th><th>ابتدا از</th><th>معنا</th></tr></thead>
        <tbody>${marks}</tbody>
      </table>`
    : "<p>علامت میانی ندارد. وقف رأس آیه سنت است. ابتدا از اول آیهٔ بعد.</p>";
  const page = v.page ? `صفحه ${v.page} · جزء ${v.juz}` : "";
  return `<article class="card">
    <p class="meta">${esc(v.surah_name)} ${v.ayah} <span dir="ltr">(${v.surah}:${v.ayah})</span> · ${esc(page)}</p>
    <p class="ayah">${esc(v.text)}</p>
    ${table}
  </article>`;
}

function render(data) {
  const bits = [];
  bits.push(`<p class="meta">نوع پرسش: ${esc(data.kind)}</p>`);
  (data.warnings || []).forEach((w) => bits.push(`<p>${esc(w)}</p>`));
  (data.verses || []).forEach((v) => bits.push(renderVerse(v)));
  (data.cards || []).forEach((c) => bits.push(`<section class="card"><pre>${esc(c)}</pre></section>`));
  if (data.neighbors && data.neighbors.length) {
    bits.push("<h2>آیه قبل و بعد</h2>");
    data.neighbors.forEach((v) => {
      bits.push(`<p class="ayah"><span class="meta">${v.surah}:${v.ayah}</span> ${esc(v.text)}</p>`);
    });
  }
  if (data.jadval && data.jadval.length) {
    bits.push("<h2>جدول مصحف محشی</h2>");
    data.jadval.forEach((row) => {
      const pairs = [];
      const n = Math.max((row.waqf || []).length, (row.ibtida || []).length);
      for (let i = 0; i < n; i++) {
        const w = (row.waqf || [])[i] || {};
        const b = (row.ibtida || [])[i] || {};
        const tag = w.tag || b.tag || "";
        pairs.push(`<tr>
          <td>${esc(tag)}</td>
          <td class="waqf">${esc(w.on || "—")}</td>
          <td class="ibtida">${esc(b.from || "—")}</td>
        </tr>`);
      }
      bits.push(`<article class="card"><table>
        <thead><tr><th>نوع</th><th>وقف روی</th><th>ابتدا از</th></tr></thead>
        <tbody>${pairs.join("")}</tbody>
      </table></article>`);
    });
  }
  (data.notes || []).forEach((n) => {
    bits.push(`<h2>یادداشت ریپو</h2><p class="meta">${esc(n.path)}</p><div class="note">${esc(n.text)}</div>`);
  });
  if (data.docs && data.docs.length) {
    bits.push("<h2>از دانش‌نامه</h2>");
    data.docs.forEach((d) => {
      bits.push(`<article class="card"><strong>${esc(d.title)}</strong><p>${esc(d.snippet)}</p></article>`);
    });
  }
  out.innerHTML = bits.join("\n");
}

async function run(q) {
  if (!q) return;
  input.value = q;
  setStatus("می‌خوانم…");
  out.innerHTML = "";
  try {
    const res = await fetch("/api/ask?q=" + encodeURIComponent(q));
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "خطا");
    setStatus("", false);
    render(data);
  } catch (err) {
    setStatus(err.message || String(err));
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  run(input.value.trim());
});

document.getElementById("chips").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-q]");
  if (btn) run(btn.dataset.q);
});

const first = new URLSearchParams(location.search).get("q");
if (first) run(first);
