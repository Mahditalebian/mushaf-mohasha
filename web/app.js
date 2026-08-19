const form = document.getElementById("form");
const input = document.getElementById("q");
const out = document.getElementById("out");
const welcome = document.getElementById("welcome");
const statusEl = document.getElementById("status");
const submitButton = document.getElementById("submitButton");
const submitLabel = submitButton.querySelector(".submit-button__label");
const clearSearch = document.getElementById("clearSearch");
const themeToggle = document.getElementById("themeToggle");
const healthBadge = document.getElementById("healthBadge");
const healthText = document.getElementById("healthText");
const backToTop = document.getElementById("backToTop");

let activeRequest = null;

const ICONS = {
  sparkle: '<path d="m12 3 1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3Zm6 11 .8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14Z" />',
  table: '<path d="M4 5h16v14H4V5Zm0 5h16M9 5v14" />',
  warning: '<path d="M12 8v5m0 4h.01M4.5 20h15a2 2 0 0 0 1.7-3L13.7 4a2 2 0 0 0-3.4 0L2.8 17a2 2 0 0 0 1.7 3Z" />',
  stop: '<path d="M8 3h8l5 5v8l-5 5H8l-5-5V8l5-5Zm4 5v5" />',
  link: '<path d="m9 15 6-6m-8.5 9.5-1 1a3.5 3.5 0 0 1-5-5l3-3a3.5 3.5 0 0 1 5 0m9-6 1-1a3.5 3.5 0 1 1 5 5l-3 3a3.5 3.5 0 0 1-5 0" />',
  play: '<path d="M8 5v14l11-7L8 5Z" />',
  book: '<path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H12v17H7a3 3 0 0 0-3 3V5.5ZM20 5.5A3.5 3.5 0 0 0 16.5 2H12v17h5a3 3 0 0 1 3 3V5.5Z" />',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5m-18 4 9 5 9-5" />',
  info: '<path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Zm0-11v6m0-10h.01" />',
  chevron: '<path d="m9 18 6-6-6-6" />',
};

function icon(name, className = "") {
  return `<svg class="${className}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ICONS.info}</svg>`;
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
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function isTableDivider(line) {
  if (!line || !line.includes("|")) return false;
  return tableCells(line).every((cell) => /^:?-{3,}:?$/.test(cell));
}

function prose(value) {
  const lines = String(value ?? "").replace(/\r\n?/g, "\n").split("\n");
  const html = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    if (line.includes("|") && isTableDivider(lines[index + 1])) {
      const headings = tableCells(line);
      const rows = [];
      index += 2;
      while (index < lines.length && lines[index].includes("|") && lines[index].trim()) {
        rows.push(tableCells(lines[index]));
        index += 1;
      }
      html.push(`<div class="table-wrap"><table><thead><tr>${headings
        .map((cell) => `<th>${inlineMarkdown(cell)}</th>`)
        .join("")}</tr></thead><tbody>${rows
        .map((row) => `<tr>${row.map((cell) => `<td>${inlineMarkdown(cell)}</td>`).join("")}</tr>`)
        .join("")}</tbody></table></div>`);
      continue;
    }

    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length <= 2 ? "h4" : "h5";
      html.push(`<${level}>${inlineMarkdown(heading[2])}</${level}>`);
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

function setStatus(text = "", type = "info") {
  statusEl.hidden = !text;
  statusEl.textContent = text;
  statusEl.className = `system-message${type === "error" ? " system-message--error" : ""}`;
}

function setLoading(loading) {
  form.setAttribute("aria-busy", String(loading));
  submitButton.disabled = loading;
  submitButton.classList.toggle("is-loading", loading);
  submitLabel.textContent = loading ? "در حال تحلیل" : "تحلیل آیه";
}

function loadingTemplate() {
  return `<div class="skeleton" aria-hidden="true">
    <div class="skeleton__title"></div>
    <div class="skeleton__card"></div>
    <div class="skeleton__line"></div>
    <div class="skeleton__line skeleton__line--short"></div>
  </div>`;
}

function sectionHeading(iconName, title, description = "") {
  return `<div class="section-heading">
    <span class="section-heading__icon">${icon(iconName)}</span>
    <div><h2>${esc(title)}</h2>${description ? `<p>${esc(description)}</p>` : ""}</div>
  </div>`;
}

function renderBest(best) {
  if (!best || !best.length) return "";

  const cards = best
    .map((item, position) => {
      const rank = Number(item.rank || position + 1);
      const agreed = String(item.source || "").startsWith("تأیید دو منبع");
      const classes = ["best-card", rank === 1 ? "best-card--first" : "", agreed ? "best-card--agreed" : ""]
        .filter(Boolean)
        .join(" ");
      return `<article class="${classes}">
        <div class="best-card__head">
          <span class="rank-badge"><b>${faDigits(rank)}</b> انتخاب ${rank === 1 ? "برتر" : `شمارهٔ ${faDigits(rank)}`}</span>
          <span class="score-pill">اطمینان ${faDigits(item.score || 0)}٪</span>
        </div>
        <div class="stop-start">
          <div class="stop-start__item stop-start__item--stop">
            <span>وقف روی</span>
            <strong>${esc(item.waqf_on || "—")}</strong>
          </div>
          <div class="stop-start__item stop-start__item--start">
            <span>ابتدا از</span>
            <strong>${esc(item.ibtida_from || "—")}</strong>
          </div>
        </div>
        <p class="best-card__source">${agreed ? "✓ " : ""}${esc(item.source || "منبع نامشخص")}</p>
        ${item.note ? `<p class="best-card__note">${esc(item.note)}</p>` : ""}
      </article>`;
    })
    .join("");

  return `<section class="result-block">
    <div class="block-heading">
      <div class="block-heading__title">
        <span class="block-heading__icon">${icon("sparkle")}</span>
        <div><h3>بهترین مواضع برای وقف</h3><p>رتبه‌بندی بر پایهٔ جدول محشی و علائم چاپی مصحف</p></div>
      </div>
    </div>
    <div class="best-grid">${cards}</div>
  </section>`;
}

function renderDecisionTable(rows) {
  if (!rows || !rows.length) return "";
  const body = rows
    .map(
      (row) => `<tr>
        <td><span class="source-pill">${esc(row.tag || "—")}</span></td>
        <td class="waqf">${esc(row.on || "—")}</td>
        <td class="ibtida">${esc(row.from || "—")}</td>
        <td>${esc(row.why || "")}</td>
      </tr>`
    )
    .join("");

  return `<section class="result-block">
    <div class="block-heading">
      <div class="block-heading__title">
        <span class="block-heading__icon">${icon("table")}</span>
        <div><h3>جدول وقف و ابتدا</h3><p>وقف روی هر عبارت و محل درست آغاز دوباره</p></div>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>نوع</th><th>وقف روی</th><th>ابتدا از</th><th>دلیل</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>
  </section>`;
}

function renderNahy(items) {
  if (!items || !items.length) return "";
  const cards = items
    .map(
      (item) => `<article class="nahy-item">
        <span class="nahy-item__mark">${esc(item.on || "—")}</span>
        <div>
          <div class="nahy-item__head">
            <strong>${esc(item.kind || "وقف نادرست")}</strong>
            <span class="severity-pill">${esc(item.severity || "ممنوع")}</span>
          </div>
          <p>${esc(item.reason || "")}</p>
        </div>
      </article>`
    )
    .join("");

  return `<section class="result-block">
    <div class="block-heading">
      <div class="block-heading__title">
        <span class="block-heading__icon" style="background:var(--danger-soft);color:var(--danger)">${icon("warning")}</span>
        <div><h3>کجا نباید وقف کرد؟</h3><p>تحلیل کلمه‌به‌کلمهٔ مواضعی که معنا را ناقص یا منحرف می‌کنند</p></div>
      </div>
    </div>
    <div class="nahy-list">${cards}</div>
  </section>`;
}

function renderInsights(explanation) {
  const items = [
    { key: "waqf", number: "۰۱", title: "دلیل وقف", icon: "stop" },
    { key: "wasl", number: "۰۲", title: "دلیل وصل", icon: "link" },
    { key: "ibtida", number: "۰۳", title: "دلیل ابتدا", icon: "play" },
    { key: "wrong", number: "۰۴", title: "حالات اشتباه", icon: "warning", danger: true },
  ].filter((item) => explanation[item.key]);

  if (!items.length) return "";

  return `<section class="result-block">
    <div class="block-heading">
      <div class="block-heading__title">
        <span class="block-heading__icon">${icon("layers")}</span>
        <div><h3>استدلال معنایی</h3><p>چهار وجه اصلی برای یک تلاوت معنا‌محور</p></div>
      </div>
    </div>
    <div class="insights-grid">${items
      .map(
        (item) => `<article class="insight-card${item.danger ? " insight-card--wrong" : ""}">
          <div class="insight-card__heading">
            <span class="insight-card__icon">${icon(item.icon)}</span>
            <div><span class="insight-card__number">${item.number}</span><h3>${item.title}</h3></div>
          </div>
          <div class="prose">${prose(explanation[item.key])}</div>
        </article>`
      )
      .join("")}</div>
  </section>`;
}

function renderExplain(explanation, data) {
  if (!explanation) return "";
  const isVerse = ["verse", "range"].includes(data.kind);
  const best = explanation.best || data.best || [];
  const nahy = explanation.nahy || data.nahy || [];
  const intro = explanation.intro || "";

  return `<article class="analysis-card">
    ${isVerse && intro ? `<div class="verse-showcase"><div class="verse-showcase__text">${prose(intro)}</div></div>` : ""}
    <div class="analysis-body">
      ${!isVerse && intro ? `<div class="prose">${prose(intro)}</div>` : ""}
      ${renderBest(best)}
      ${renderDecisionTable(explanation.table)}
      ${renderNahy(nahy)}
      ${renderInsights(explanation)}
      ${
        explanation.disclaimer
          ? `<p class="disclaimer">${icon("info")}<span>${esc(explanation.disclaimer)}</span></p>`
          : ""
      }
    </div>
  </article>`;
}

function renderVerse(verse) {
  const marks = (verse.marks || [])
    .map(
      (mark) => `<article class="mark-card">
        <span class="mark-card__symbol">${esc(mark.letter || mark.symbol)}${mark.symbol ? ` ${esc(mark.symbol)}` : ""}</span>
        <div class="mark-card__body">
          <div class="mark-card__name">${esc(mark.name || "علامت وقف")}</div>
          <div class="mark-card__path">
            <span>وقف: «${esc(mark.waqf_on || "—")}»</span>
            <span>ابتدا: «${esc(mark.ibtida_from || "آیهٔ بعد")}»</span>
          </div>
          <p class="mark-card__rule">${esc(mark.rule || "")}</p>
        </div>
      </article>`
    )
    .join("");

  const meta = [verse.page ? `صفحهٔ ${faDigits(verse.page)}` : "", verse.juz ? `جزء ${faDigits(verse.juz)}` : ""]
    .filter(Boolean)
    .join(" · ");

  return `<article class="verse-card">
    <header class="verse-card__head">
      <div class="verse-card__identity">
        <span class="verse-number">${faDigits(verse.ayah)}</span>
        <strong>سورهٔ ${esc(verse.surah_name)}</strong>
      </div>
      <span class="verse-card__meta"><span dir="ltr">${esc(verse.surah)}:${esc(verse.ayah)}</span>${meta ? ` · ${meta}` : ""}</span>
    </header>
    <p class="verse-card__text">${esc(verse.text)}</p>
    ${marks ? `<div class="marks-list">${marks}</div>` : '<p class="no-marks">این آیه علامت میانی ندارد؛ وقف بر رأس آیه سنت است و ابتدا از آیهٔ بعد خواهد بود.</p>'}
  </article>`;
}

function renderNeighbors(neighbors, currentVerse) {
  if (!neighbors || !neighbors.length) return "";
  const cards = neighbors
    .map((verse) => {
      let label = "آیهٔ هم‌جوار";
      if (currentVerse && verse.surah === currentVerse.surah) {
        if (verse.ayah < currentVerse.ayah) label = "آیهٔ قبل";
        if (verse.ayah > currentVerse.ayah) label = "آیهٔ بعد";
      }
      return `<article class="context-card">
        <div class="context-card__label"><span>${label}</span><span>${esc(verse.surah_name)} ${faDigits(verse.ayah)}</span></div>
        <p class="ayah">${esc(verse.text)}</p>
      </article>`;
    })
    .join("");
  return `${sectionHeading("book", "آیات هم‌جوار", "برای دیدن پیوستگی معنایی در سیاق آیه")}<div class="context-grid">${cards}</div>`;
}

function renderWarnings(warnings) {
  return (warnings || [])
    .map((warning) => `<div class="warning-card">${icon("warning")}<span>${esc(warning)}</span></div>`)
    .join("");
}

function kindLabel(kind) {
  return {
    verse: "تحلیل یک آیه",
    range: "تحلیل بازهٔ آیات",
    marks: "فهرست علائم",
    topic: "پاسخ دانش‌نامه",
  }[kind] || "نتیجهٔ جست‌وجو";
}

function render(data) {
  const explanation = data.explanation || {};
  const firstVerse = data.verses && data.verses[0];
  const title = explanation.title || data.query || "نتیجهٔ تحلیل";
  const meta = [
    explanation.page ? `صفحهٔ ${faDigits(explanation.page)}` : "",
    explanation.juz ? `جزء ${faDigits(explanation.juz)}` : "",
    data.verses && data.verses.length > 1 ? `${faDigits(data.verses.length)} آیه` : "",
  ].filter(Boolean);

  const bits = [
    `<header class="result-title">
      <div><span class="section-kicker">${kindLabel(data.kind)}</span><h2>${faDigits(esc(title))}</h2></div>
      <div class="result-title__context">${meta.map((item) => `<span class="meta-pill">${item}</span>`).join("")}</div>
    </header>`,
    renderWarnings(data.warnings),
    renderExplain(explanation, data),
  ];

  if (data.verses && data.verses.length) {
    bits.push(sectionHeading("book", "متن و علائم چاپی", "نمایش علائم وقف در متن عثمانی همین مخزن"));
    bits.push(`<div class="verse-list">${data.verses.map(renderVerse).join("")}</div>`);
  }

  bits.push(renderNeighbors(data.neighbors, firstVerse));

  if (data.cards && data.cards.length) {
    bits.push(
      data.cards
        .map(
          (card, index) => `<details class="raw-card"><summary>نمایش کارت تطبیق فنی${data.cards.length > 1 ? ` ${faDigits(index + 1)}` : ""}</summary><pre>${esc(card)}</pre></details>`
        )
        .join("")
    );
  }

  const result = bits.filter(Boolean).join("\n");
  out.innerHTML = result || '<div class="empty-result"><strong>نتیجه‌ای پیدا نشد</strong>نام سوره و شمارهٔ آیه را دوباره بررسی کنید.</div>';
  welcome.hidden = true;
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
  clearSearch.hidden = false;
  welcome.hidden = true;
  out.innerHTML = loadingTemplate();
  setStatus("در حال خواندن داده‌ها و تحلیل مواضع…");
  setLoading(true);

  try {
    const response = await fetch(`/api/ask?q=${encodeURIComponent(query)}`, {
      signal: request.signal,
      headers: { Accept: "application/json" },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "پاسخی از موتور دریافت نشد.");
    setStatus();
    render(data);
    if (options.scroll !== false) {
      requestAnimationFrame(() => out.scrollIntoView({ behavior: "smooth", block: "start" }));
    }
  } catch (error) {
    if (error.name === "AbortError") return;
    out.innerHTML = '<div class="empty-result"><strong>تحلیل انجام نشد</strong>ارتباط با موتور محلی را بررسی و دوباره تلاش کنید.</div>';
    setStatus(
      `${error.message || String(error)} — مطمئن شوید برنامه با دستور python3 -m engine serve اجرا شده است.`,
      "error"
    );
  } finally {
    if (activeRequest === request) {
      setLoading(false);
      activeRequest = null;
    }
  }
}

function updateClearButton() {
  clearSearch.hidden = !input.value;
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  themeToggle.setAttribute("aria-label", theme === "dark" ? "فعال کردن حالت روشن" : "فعال کردن حالت تیره");
  themeToggle.title = theme === "dark" ? "حالت روشن" : "حالت تیره";
  try {
    localStorage.setItem("mushaf-theme", theme);
  } catch (_) {
    // The visual preference is optional; private browsing may disable storage.
  }
}

function initialTheme() {
  try {
    const saved = localStorage.getItem("mushaf-theme");
    if (saved === "light" || saved === "dark") return saved;
  } catch (_) {
    // Fall back to the operating-system preference.
  }
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  run(input.value);
});

input.addEventListener("input", updateClearButton);
input.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && input.value) {
    input.value = "";
    updateClearButton();
  }
});

clearSearch.addEventListener("click", () => {
  input.value = "";
  updateClearButton();
  input.focus();
});

document.getElementById("chips").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-q]");
  if (button) run(button.dataset.q);
});

themeToggle.addEventListener("click", () => {
  setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
});

backToTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
window.addEventListener(
  "scroll",
  () => {
    backToTop.hidden = window.scrollY < 700;
  },
  { passive: true }
);

setTheme(initialTheme());
updateClearButton();

const firstQuery = new URLSearchParams(location.search).get("q");
if (firstQuery) run(firstQuery, { scroll: false });

fetch("/api/health", { headers: { Accept: "application/json" } })
  .then(async (response) => ({ response, body: await response.json() }))
  .then(({ response, body }) => {
    const ready = response.ok && body && body.ok;
    healthBadge.className = `health-badge ${ready ? "health-badge--ready" : "health-badge--error"}`;
    healthText.textContent = ready ? "موتور آماده است" : "داده‌ها نیاز به بررسی دارند";
  })
  .catch(() => {
    healthBadge.className = "health-badge health-badge--error";
    healthText.textContent = "موتور در دسترس نیست";
  });
