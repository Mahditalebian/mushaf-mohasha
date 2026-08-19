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

function prose(s) {
  return esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^### (.+)$/gm, "<strong>$1</strong>")
    .replace(/^- /gm, "• ")
    .replace(/\n/g, "<br>");
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

function renderExplain(ex) {
  if (!ex) return "";
  const meta = [
    ex.page ? `صفحه ${ex.page} مصحف ۶۰۴صفحه‌ای` : "",
    ex.juz ? `جزء ${ex.juz}` : "",
  ]
    .filter(Boolean)
    .join(" · ");
  let table = "";
  if (ex.table && ex.table.length) {
    const rows = ex.table
      .map(
        (r) => `<tr>
          <td>${esc(r.tag || "—")}</td>
          <td class="waqf">${esc(r.on || "—")}</td>
          <td class="ibtida">${esc(r.from || "—")}</td>
          <td>${esc(r.why || "")}</td>
        </tr>`
      )
      .join("");
    table = `<table>
      <thead><tr><th>نوع</th><th>وقف روی</th><th>ابتدا از</th><th>چرا</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  }
  let best = "";
  if (ex.best && ex.best.length) {
    const rows = ex.best
      .map(
        (b) => `<tr class="${String(b.source || "").startsWith("تأیید دو منبع") ? "agree" : ""}">
          <td>${esc(b.rank)}</td>
          <td>${esc(b.score)}</td>
          <td class="waqf">${esc(b.waqf_on || "—")}</td>
          <td class="ibtida">${esc(b.ibtida_from || "—")}</td>
          <td>${esc(b.source || "—")}</td>
        </tr>`
      )
      .join("");
    best = `<h3>بهترین مواضع (ترکیب محشی + علائم چاپی)</h3>
    <table>
      <thead><tr><th>رتبه</th><th>امتیاز</th><th>وقف روی</th><th>ابتدا از</th><th>منبع</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    <p class="meta">جایی که محشی و علامت چاپی همرأی‌اند «تأیید دو منبع» است — مطمئن‌ترین جای وقف.</p>`;
  }
  return `<section class="card explain">
    <h2>${esc(ex.title || "استدلال معنایی")}</h2>
    ${meta ? `<p class="meta">${esc(meta)}</p>` : ""}
    ${ex.intro ? `<div class="prose ayah">${prose(ex.intro)}</div>` : ""}
    ${table}
    ${best}
    ${ex.waqf ? `<h3>۱) دلیل وقف</h3><div class="prose">${prose(ex.waqf)}</div>` : ""}
    ${ex.wasl ? `<h3>۲) دلیل وصل</h3><div class="prose">${prose(ex.wasl)}</div>` : ""}
    ${ex.ibtida ? `<h3>۳) دلیل ابتدا</h3><div class="prose">${prose(ex.ibtida)}</div>` : ""}
    ${ex.wrong ? `<h3>۴) حالات اشتباه</h3><div class="prose">${prose(ex.wrong)}</div>` : ""}
    ${ex.disclaimer ? `<p class="meta">${esc(ex.disclaimer)}</p>` : ""}
  </section>`;
}

function render(data) {
  const bits = [];
  bits.push(renderExplain(data.explanation));
  (data.warnings || []).forEach((w) => bits.push(`<p>${esc(w)}</p>`));
  if (data.verses && data.verses.length) {
    bits.push("<h2>علائم چاپی آیه</h2>");
    data.verses.forEach((v) => bits.push(renderVerse(v)));
  }
  if (data.neighbors && data.neighbors.length) {
    bits.push("<h2>آیه قبل و بعد</h2>");
    data.neighbors.forEach((v) => {
      bits.push(`<p class="ayah"><span class="meta">${v.surah}:${v.ayah}</span> ${esc(v.text)}</p>`);
    });
  }
  (data.cards || []).forEach((c) => bits.push(`<section class="card"><pre>${esc(c)}</pre></section>`));
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
    setStatus(
      (err.message || String(err)) +
        " — اگر فایل HTML را مستقیم باز کرده‌ای، اول از پوشهٔ ریپو بزن: python3 -m engine serve"
    );
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

fetch("/api/health")
  .then((r) => r.json())
  .then((h) => {
    if (h && h.ok === false) setStatus("داده ناقص است. python3 -m engine check", true);
  })
  .catch(() => {});
