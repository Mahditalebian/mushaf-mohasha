const form = document.getElementById("form");
const input = document.getElementById("q");
const out = document.getElementById("out");
const statusEl = document.getElementById("status");
const submitButton = document.getElementById("submitButton");
const submitLabel = document.getElementById("submitLabel");
const resultKind = document.getElementById("resultKind");
const resultTitle = document.getElementById("resultTitle");
const resultSubtitle = document.getElementById("resultSubtitle");
const pageMeta = document.getElementById("pageMeta");
const healthBadge = document.getElementById("healthBadge");
const healthText = document.getElementById("healthText");
const sidebarHealth = document.getElementById("sidebarHealth");
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");
const menuButton = document.getElementById("menuButton");
const toast = document.getElementById("toast");
const toastText = document.getElementById("toastText");

let activeRequest = null;
let toastTimer = null;

const ICONS = {
  sparkle: '<path d="m12 3 1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3Zm6 11 .8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14Z" />',
  stop: '<path d="M8 3h8l5 5v8l-5 5H8l-5-5V8l5-5Zm4 5v5" />',
  link: '<path d="m9 15 6-6m-8.5 9.5-1 1a3.5 3.5 0 0 1-5-5l3-3a3.5 3.5 0 0 1 5 0m9-6 1-1a3.5 3.5 0 1 1 5 5l-3 3a3.5 3.5 0 0 1-5 0" />',
  play: '<path d="M8 5v14l11-7L8 5Z" />',
  warning: '<path d="M12 8v5m0 4h.01M4.5 20h15a2 2 0 0 0 1.7-3L13.7 4a2 2 0 0 0-3.4 0L2.8 17a2 2 0 0 0 1.7 3Z" />',
  book: '<path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H12v17H7a3 3 0 0 0-3 3V5.5ZM20 5.5A3.5 3.5 0 0 0 16.5 2H12v17h5a3 3 0 0 1 3 3V5.5Z" />',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Zm-3-10 2 2 4-4" />',
  info: '<path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Zm0-11v6m0-10h.01" />',
  chevron: '<path d="m6 9 6 6 6-6" />',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5m-18 4 9 5 9-5" />',
};

function icon(name) {
  return `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ICONS.info}</svg>`;
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function faDigits(value) {
  return String(value ?? "").replace(/\d/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);
}

function inlineMarkdown(value) {
  return esc(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function tableCells(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
}

function isTableDivider(line) {
  return Boolean(line && line.includes("|") && tableCells(line).every((cell) => /^:?-{3,}:?$/.test(cell)));
}

function prose(value) {
  const lines = String(value ?? "").replace(/\r\n?/g, "\n").split("\n");
  const html = [];
  let index = 0;

  while (index < lines.length) {
    const trimmed = lines[index].trim();
    if (!trimmed) {
      index += 1;
      continue;
    }

    if (lines[index].includes("|") && isTableDivider(lines[index + 1])) {
      const headings = tableCells(lines[index]);
      const rows = [];
      index += 2;
      while (index < lines.length && lines[index].trim() && lines[index].includes("|")) {
        rows.push(tableCells(lines[index]));
        index += 1;
      }
      html.push(`<div class="table-scroll"><table><thead><tr>${headings.map((cell) => `<th>${inlineMarkdown(cell)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${inlineMarkdown(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`);
      continue;
    }

    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      html.push(`<h4>${inlineMarkdown(heading[2])}</h4>`);
      index += 1;
      continue;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      const items = [];
      while (index < lines.length && /^\s*[-*]\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*[-*]\s+/, ""));
        index += 1;
      }
      html.push(`<ul>${items.map((item) => `<li>${inlineMarkdown(item)}</li>`).join("")}</ul>`);
      continue;
    }

    if (/^\d+[.)]\s+/.test(trimmed)) {
      const items = [];
      while (index < lines.length && /^\s*\d+[.)]\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*\d+[.)]\s+/, ""));
        index += 1;
      }
      html.push(`<ol>${items.map((item) => `<li>${inlineMarkdown(item)}</li>`).join("")}</ol>`);
      continue;
    }

    if (/^>\s?/.test(trimmed)) {
      html.push(`<blockquote>${inlineMarkdown(trimmed.replace(/^>\s?/, ""))}</blockquote>`);
      index += 1;
      continue;
    }

    const paragraph = [trimmed];
    index += 1;
    while (
      index < lines.length &&
      lines[index].trim() &&
      !/^(#{1,6})\s+/.test(lines[index].trim()) &&
      !/^\s*[-*]\s+/.test(lines[index]) &&
      !/^\s*\d+[.)]\s+/.test(lines[index]) &&
      !/^>\s?/.test(lines[index].trim()) &&
      !(lines[index].includes("|") && isTableDivider(lines[index + 1]))
    ) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    html.push(`<p>${paragraph.map(inlineMarkdown).join("<br>")}</p>`);
  }
  return html.join("");
}

function showToast(message) {
  toastText.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2800);
}

function setStatus(message = "", type = "info") {
  statusEl.hidden = !message;
  statusEl.textContent = message;
  statusEl.className = `system-message${type === "error" ? " error" : ""}`;
}

function setLoading(loading) {
  form.setAttribute("aria-busy", String(loading));
  submitButton.disabled = loading;
  submitButton.classList.toggle("loading", loading);
  submitLabel.textContent = loading ? "در حال تحلیل" : "تحلیل آیه";
}

function closeMenu() {
  sidebar.classList.remove("open");
  overlay.classList.remove("show");
  menuButton.setAttribute("aria-expanded", "false");
}

function loadingTemplate() {
  return `<div class="skeleton-dashboard" aria-hidden="true">
    <div class="skeleton-stack"><div class="skeleton-block large"></div><div class="skeleton-block"></div><div class="skeleton-block large"></div></div>
    <div class="skeleton-block side"></div>
  </div>`;
}

function renderPrintedMarks(verse) {
  const marks = verse.marks || [];
  if (!marks.length) return '<p class="no-mark">این آیه علامت میانی ندارد؛ وقف بر رأس آیه سنت است و ابتدا از آیهٔ بعد خواهد بود.</p>';
  return `<div class="printed-marks">${marks.map((mark) => `<article class="printed-mark">
    <span class="printed-mark__symbol">${esc(mark.letter || mark.symbol)}${mark.symbol ? ` ${esc(mark.symbol)}` : ""}</span>
    <div>
      <strong>${esc(mark.name || "علامت وقف")}</strong>
      <div class="printed-mark__path"><span class="stop">وقف: «${esc(mark.waqf_on || "—")}»</span><span class="start">ابتدا: «${esc(mark.ibtida_from || "آیهٔ بعد")}»</span></div>
      <p>${esc(mark.rule || "")}</p>
    </div>
  </article>`).join("")}</div>`;
}

function renderVerse(verse) {
  const markCount = (verse.marks || []).length;
  return `<article class="card ayah-card">
    <header class="ayah-head">
      <div class="ayah-id">
        <span class="ayah-number">${faDigits(verse.ayah)}</span>
        <div><strong>سورهٔ ${esc(verse.surah_name)}</strong><small>${esc(verse.surah)}:${esc(verse.ayah)}</small></div>
      </div>
      <div class="ayah-location">${verse.page ? `<span>صفحهٔ ${faDigits(verse.page)}</span>` : ""}${verse.juz ? `<span>جزء ${faDigits(verse.juz)}</span>` : ""}</div>
    </header>
    <p class="ayah-text">${esc(verse.text)}</p>
    <details class="marks-details">
      <summary><span>${icon("layers")} ${markCount ? `${faDigits(markCount)} علامت وقف چاپی در این آیه` : "وضعیت وقف میانی این آیه"}</span>${icon("chevron")}</summary>
      ${renderPrintedMarks(verse)}
    </details>
  </article>`;
}

function renderBest(best) {
  if (!best || !best.length) return "";
  return `<section class="card section-card">
    <header class="section-head">
      <div class="section-title"><span class="section-icon">${icon("sparkle")}</span><div><h2>بهترین مواضع وقف</h2><p>رتبه‌بندی بر پایهٔ جدول محشی و علائم چاپی</p></div></div>
      <span class="view-all">${faDigits(best.length)} پیشنهاد</span>
    </header>
    <div class="best-list">${best.map((item, position) => {
      const score = Math.max(0, Math.min(100, Number(item.score || 0)));
      const rank = Number(item.rank || position + 1);
      return `<article class="best-row${rank === 1 ? " primary" : ""}">
        <span class="rank">${faDigits(rank)}</span>
        <div class="point stop"><small>وقف روی</small><strong>${esc(item.waqf_on || "—")}</strong><span class="best-source">${esc(item.source || "")}</span></div>
        <span class="flow-arrow"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-5-5 5 5-5 5" /></svg></span>
        <div class="point start"><small>ابتدا از</small><strong>${esc(item.ibtida_from || "—")}</strong><span class="best-source">${esc(item.note || "")}</span></div>
        <span class="confidence">اطمینان ${faDigits(score)}٪<small>${esc(item.tag || "")}</small></span>
      </article>`;
    }).join("")}</div>
  </section>`;
}

const ANALYSIS_PARTS = [
  { key: "waqf", title: "دلیل وقف", icon: "stop" },
  { key: "wasl", title: "دلیل وصل", icon: "link" },
  { key: "ibtida", title: "دلیل ابتدا", icon: "play" },
  { key: "wrong", title: "حالات اشتباه", icon: "warning", danger: true },
];

function renderSummaryPanel(explanation) {
  const parts = ANALYSIS_PARTS.filter((part) => explanation[part.key]);
  if (!parts.length) return '<div class="empty-state"><strong>خلاصه‌ای در دسترس نیست</strong>پرسش دیگری را امتحان کنید.</div>';
  return `<div class="analysis-grid">${parts.map((part) => {
    const text = String(explanation[part.key]);
    const wide = text.length > 900 ? " wide" : "";
    return `<article class="analysis-item${part.danger ? " danger" : ""}${wide}">
      <div class="analysis-item__head"><span>${icon(part.icon)}</span><strong>${part.title}</strong></div>
      <div class="prose">${prose(text)}</div>
    </article>`;
  }).join("")}</div>`;
}

function renderRulesPanel(explanation) {
  const rows = explanation.table || [];
  if (!rows.length) return '<div class="empty-state"><strong>جدول مستقلی برای این پرسش نیست</strong>جزئیات حکم در بخش خلاصهٔ تحلیل آمده است.</div>';
  return `<div class="rules-list">${rows.map((row) => `<article class="rule-row">
    <span class="rule-label">${esc(row.tag || "موضع وقف")}</span>
    <strong class="rule-stop">وقف: ${esc(row.on || "—")}</strong>
    <strong class="rule-start">ابتدا: ${esc(row.from || "—")}</strong>
    ${row.why ? `<p class="rule-explanation">${esc(row.why)}</p>` : ""}
  </article>`).join("")}</div>`;
}

function renderDangerPanel(explanation, nahy) {
  const items = nahy || [];
  const cards = items.length ? `<div class="danger-list">${items.map((item) => `<article class="danger-item">
    <strong>${esc(item.on || "—")} <span>${esc(item.kind || "وقف نادرست")} · ${esc(item.severity || "ممنوع")}</span></strong>
    <p>${esc(item.reason || "")}</p>
  </article>`).join("")}</div>` : "";
  const detail = explanation.wrong ? `<div class="analysis-item danger danger-detail"><div class="analysis-item__head"><span>${icon("warning")}</span><strong>توضیح خطاهای معنایی</strong></div><div class="prose">${prose(explanation.wrong)}</div></div>` : "";
  return cards || detail ? `${cards}${detail}` : '<div class="empty-state"><strong>موضع ممنوعی گزارش نشده است</strong>برای حکم دقیق، یک آیهٔ مشخص را جست‌وجو کنید.</div>';
}

function renderSourcePanel(explanation, docs) {
  const disclaimer = explanation.disclaimer ? `<div class="disclaimer-box">${icon("info")}<span>${esc(explanation.disclaimer)}</span></div>` : "";
  const sources = (docs || []).length ? `<div class="source-list">${docs.slice(0, 6).map((doc) => `<article class="source-item"><strong>${esc(doc.title || doc.path || "سند")}</strong>${doc.snippet ? `<p>${esc(doc.snippet)}</p>` : ""}</article>`).join("")}</div>` : "";
  return `${disclaimer}${sources}` || '<div class="empty-state"><strong>منبع جداگانه‌ای نمایش داده نشد</strong>نتیجه از داده‌های محلی همین مخزن ساخته شده است.</div>';
}

function renderTabs(explanation, data) {
  if (!explanation) return "";
  return `<section class="card tabs-card">
    <div class="tabs" role="tablist" aria-label="بخش‌های تحلیل">
      <button class="tab active" type="button" data-tab="summary" role="tab" aria-selected="true">خلاصهٔ تحلیل</button>
      <button class="tab" type="button" data-tab="rules" role="tab" aria-selected="false">وقف و ابتدا</button>
      <button class="tab" type="button" data-tab="danger" role="tab" aria-selected="false">مواضع ممنوع</button>
      <button class="tab" type="button" data-tab="source" role="tab" aria-selected="false">منبع و روش</button>
    </div>
    <div class="tab-panel active" data-panel="summary" role="tabpanel">${renderSummaryPanel(explanation)}</div>
    <div class="tab-panel" data-panel="rules" role="tabpanel">${renderRulesPanel(explanation)}</div>
    <div class="tab-panel" data-panel="danger" role="tabpanel">${renderDangerPanel(explanation, explanation.nahy || data.nahy)}</div>
    <div class="tab-panel" data-panel="source" role="tabpanel">${renderSourcePanel(explanation, data.docs)}</div>
  </section>`;
}

function renderNeighbors(neighbors, current) {
  if (!neighbors || !neighbors.length) return "";
  return `<section class="card document-card">
    <header class="document-card__head"><span class="section-icon">${icon("book")}</span><div><h2>آیات هم‌جوار</h2><p>برای بررسی پیوستگی معنایی آیه در سیاق</p></div></header>
    <div class="neighbor-list">${neighbors.map((verse) => {
      let label = "آیهٔ هم‌جوار";
      if (current && current.surah === verse.surah) label = verse.ayah < current.ayah ? "آیهٔ قبل" : "آیهٔ بعد";
      return `<article class="neighbor"><div class="neighbor__head"><span>${label}</span><span>${esc(verse.surah_name)} ${faDigits(verse.ayah)}</span></div><p>${esc(verse.text)}</p></article>`;
    }).join("")}</div>
  </section>`;
}

function renderCards(cards) {
  return (cards || []).map((card, index) => `<details class="card raw-details"><summary>نمایش کارت تطبیق فنی${cards.length > 1 ? ` ${faDigits(index + 1)}` : ""}</summary><pre>${esc(card)}</pre></details>`).join("");
}

function renderWarnings(warnings) {
  return (warnings || []).map((warning) => `<div class="warning-box">${icon("warning")}<span>${esc(warning)}</span></div>`).join("");
}

function renderSummaryAside(data) {
  const verses = data.verses || [];
  const best = data.best || [];
  const nahy = data.nahy || [];
  const marks = verses.reduce((total, verse) => total + (verse.marks || []).length, 0);
  const score = best.length ? Math.max(0, Math.min(100, Number(best[0].score || 0))) : 0;
  return `<section class="card summary-card">
    <h2>خلاصهٔ این تحلیل</h2>
    <div class="stats">
      <div class="stat"><span>مواضع پیشنهادی</span><strong>${faDigits(best.length)} <small>موضع</small></strong></div>
      <div class="stat"><span>مواضع ممنوع</span><strong>${faDigits(nahy.length)} <small>موضع</small></strong></div>
      <div class="stat"><span>علائم چاپی</span><strong>${faDigits(marks)} <small>علامت</small></strong></div>
      <div class="stat"><span>آیات نتیجه</span><strong>${faDigits(verses.length)} <small>آیه</small></strong></div>
    </div>
    ${best.length ? `<div class="quality"><span class="quality-ring" data-score="${faDigits(score)}" style="background:conic-gradient(var(--green) 0 ${score}%,#cfe4dc ${score}%)"></span><div><strong>اطمینان پیشنهاد اول</strong><small>${esc(best[0].source || "بر پایهٔ داده‌های محلی")}</small></div></div>` : ""}
  </section>`;
}

function renderMarksAside() {
  return `<section class="card marks-card">
    <h2>راهنمای سریع علائم</h2>
    <div class="mark-list">
      <div class="mark-row"><span class="mark-symbol">م</span><div><strong>وقف لازم</strong><small>باید ایستاد</small></div></div>
      <div class="mark-row"><span class="mark-symbol">لا</span><div><strong>وقف ممنوع</strong><small>نباید ایستاد</small></div></div>
      <div class="mark-row"><span class="mark-symbol">قلی</span><div><strong>وقف اولی</strong><small>ایستادن بهتر است</small></div></div>
      <div class="mark-row"><span class="mark-symbol">صلی</span><div><strong>وصل اولی</strong><small>ادامه دادن بهتر است</small></div></div>
      <div class="mark-row"><span class="mark-symbol">ج</span><div><strong>وقف جایز</strong><small>هر دو حالت درست است</small></div></div>
    </div>
  </section>`;
}

function renderPrivacyAside() {
  return `<div class="privacy-card"><span>${icon("shield")}</span><div><strong>تحلیل خصوصی و محلی</strong><p>این پرسش در مرورگر یا مخزن ذخیره نمی‌شود.</p></div></div>`;
}

function render(data) {
  const explanation = data.explanation || {};
  const verses = data.verses || [];
  const firstVerse = verses[0];
  const best = explanation.best || data.best || [];
  const nahy = explanation.nahy || data.nahy || [];
  data.best = best;
  data.nahy = nahy;

  const labels = {
    verse: "تحلیل یک آیه",
    range: "تحلیل بازهٔ آیات",
    marks: "فهرست علائم وقف",
    topic: "پاسخ دانش‌نامه",
  };
  resultKind.textContent = labels[data.kind] || "نتیجهٔ جست‌وجو";
  resultTitle.textContent = faDigits(explanation.title || data.query || "نتیجهٔ تحلیل");
  resultSubtitle.textContent = data.kind === "topic"
    ? "پاسخ از دانش‌نامه و اسناد محلی همین مخزن ساخته شده است."
    : "مواضع وقف، محل ابتدا و خطاهای معنایی این نتیجه را بررسی کنید.";

  const meta = [
    explanation.page ? `صفحهٔ ${faDigits(explanation.page)}` : "",
    explanation.juz ? `جزء ${faDigits(explanation.juz)}` : "",
    verses.length ? `${faDigits(verses.length)} آیه` : "",
  ].filter(Boolean);
  pageMeta.innerHTML = meta.map((item, index) => `<span class="meta-chip">${index === 0 ? icon("book") : ""}${esc(item)}</span>`).join("");

  const main = [
    renderWarnings(data.warnings),
    verses.length ? `<div class="verse-stack">${verses.map(renderVerse).join("")}</div>` : "",
    renderBest(best),
    renderTabs(explanation, data),
    renderNeighbors(data.neighbors, firstVerse),
    renderCards(data.cards),
  ].filter(Boolean).join("");

  out.innerHTML = `<div class="dashboard">
    <div class="stack">${main || '<div class="card empty-state"><strong>نتیجه‌ای پیدا نشد</strong>نام سوره و شمارهٔ آیه را دوباره بررسی کنید.</div>'}</div>
    <aside class="side-stack">${renderSummaryAside(data)}${renderMarksAside()}${renderPrivacyAside()}</aside>
  </div>`;
}

async function run(rawQuery, options = {}) {
  const query = String(rawQuery || "").trim();
  if (!query) {
    setStatus("لطفاً نام سوره و شمارهٔ آیه یا پرسش خود را وارد کنید.", "error");
    input.focus();
    return;
  }

  if (activeRequest) activeRequest.abort();
  const request = new AbortController();
  activeRequest = request;
  input.value = query;
  out.innerHTML = loadingTemplate();
  setStatus("در حال خواندن داده‌ها و ساخت تحلیل…");
  setLoading(true);
  closeMenu();

  try {
    const response = await fetch(`/api/ask?q=${encodeURIComponent(query)}`, {
      signal: request.signal,
      headers: { Accept: "application/json" },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "پاسخی از موتور دریافت نشد.");
    render(data);
    setStatus();
    if (options.scroll) requestAnimationFrame(() => out.scrollIntoView({ behavior: "smooth", block: "start" }));
  } catch (error) {
    if (error.name === "AbortError") return;
    out.innerHTML = '<div class="dashboard"><div class="stack"><div class="card empty-state"><strong>تحلیل انجام نشد</strong>ارتباط با موتور محلی را بررسی و دوباره تلاش کنید.</div></div></div>';
    setStatus(`${error.message || String(error)} — برنامه را با دستور python3 -m engine serve اجرا کنید.`, "error");
  } finally {
    if (activeRequest === request) {
      activeRequest = null;
      setLoading(false);
    }
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  run(input.value, { scroll: true });
});

document.addEventListener("click", (event) => {
  const queryButton = event.target.closest("[data-query]");
  if (queryButton) {
    run(queryButton.dataset.query, { scroll: true });
    return;
  }

  const tab = event.target.closest(".tab[data-tab]");
  if (tab) {
    const tabsCard = tab.closest(".tabs-card");
    tabsCard.querySelectorAll(".tab").forEach((item) => {
      const active = item === tab;
      item.classList.toggle("active", active);
      item.setAttribute("aria-selected", String(active));
    });
    tabsCard.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === tab.dataset.tab));
  }
});

menuButton.addEventListener("click", () => {
  const open = !sidebar.classList.contains("open");
  sidebar.classList.toggle("open", open);
  overlay.classList.toggle("show", open);
  menuButton.setAttribute("aria-expanded", String(open));
});
overlay.addEventListener("click", closeMenu);

document.getElementById("helpButton").addEventListener("click", () => {
  showToast("نام سوره و شمارهٔ آیه را بنویسید؛ مثال: بقره ۹۱");
  input.focus();
});

const firstQuery = new URLSearchParams(location.search).get("q") || "بقره ۹۱";
run(firstQuery, { scroll: false });

fetch("/api/health", { headers: { Accept: "application/json" } })
  .then(async (response) => ({ ok: response.ok, data: await response.json() }))
  .then(({ ok, data }) => {
    const ready = ok && data && data.ok;
    healthBadge.className = `local-status ${ready ? "" : "health-error"}`;
    healthText.textContent = ready ? "موتور آماده است" : "داده‌ها نیاز به بررسی دارند";
    sidebarHealth.textContent = ready ? "موتور محلی آماده است" : "موتور نیاز به بررسی دارد";
  })
  .catch(() => {
    healthBadge.className = "local-status health-error";
    healthText.textContent = "موتور در دسترس نیست";
    sidebarHealth.textContent = "موتور در دسترس نیست";
  });
