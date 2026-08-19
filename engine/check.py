"""بررسی اینکه بعد از کلون، همهٔ داده و موتور سر جایش است."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from .paths import AYAT_DIR, DATA_FILE, DOCS_DIR, ROOT, WEB_DIR


MIN_PY = (3, 10)


@dataclass
class Report:
    ok: bool = True
    lines: list[str] = field(default_factory=list)

    def add(self, ok: bool, text: str) -> None:
        mark = "✓" if ok else "✗"
        self.lines.append(f"{mark}  {text}")
        if not ok:
            self.ok = False


def verify() -> Report:
    r = Report()
    py = sys.version_info
    r.add(
        py >= MIN_PY,
        f"پایتون {py.major}.{py.minor}.{py.micro}  (حداقل ۳.۱۰)",
    )

    r.add(DATA_FILE.is_file(), f"متن عثمانی: {DATA_FILE.relative_to(ROOT)}")
    pages = ROOT / "data" / "pages.tsv"
    r.add(pages.is_file(), f"صفحات: {pages.relative_to(ROOT)}")
    jadval_dir = ROOT / "data" / "jadval_raw"
    jsonl = list(jadval_dir.glob("*.jsonl")) if jadval_dir.is_dir() else []
    r.add(len(jsonl) >= 1, f"جدول محشی: {len(jsonl)} فایل jsonl")
    docs = list(DOCS_DIR.glob("*.md")) if DOCS_DIR.is_dir() else []
    r.add(len(docs) >= 5, f"اسناد: {len(docs)} فایل")
    r.add((WEB_DIR / "index.html").is_file(), "صفحهٔ HTML")
    r.add((WEB_DIR / "app.js").is_file(), "app.js")
    r.add(AYAT_DIR.is_dir(), "پوشهٔ ayat/")

    if not r.ok:
        return r

    from . import jadval, quran
    from .ask import ask
    from .pages import load_pages

    verses = quran.load_verses()
    r.add(len(verses) == 6236, f"تعداد آیات: {len(verses)} (باید ۶۲۳۶)")
    pages_map = load_pages()
    r.add(len(pages_map) == 6236, f"تعداد صفحات ثبت‌شده: {len(pages_map)}")
    rows = jadval.load_rows()
    r.add(len(rows) >= 800, f"سطر جدول محشی: {len(rows)}")

    pack = ask("بقره ۹۱")
    v = pack.verses[0] if pack.verses else None
    ok_v = bool(v and v.surah == 2 and v.ayah == 91)
    r.add(ok_v, "نمونهٔ پرسش «بقره ۹۱»")
    if v:
        page = v.to_dict().get("page")
        r.add(page == 14, f"صفحهٔ بقره ۹۱ = {page} (باید ۱۴)")
        r.add(any(m.symbol == "ۗ" for m in v.marks), "قلی روی معهم در بقره ۹۱")
    r.add(bool(pack.jadval), "جدول محشی برای بقره ۹۱")
    r.add(bool(pack.explanation and pack.explanation.get("waqf")), "استدلال چهاربخشی ساخته شد")
    return r


def main(argv: list[str] | None = None) -> int:
    report = verify()
    print("بررسی موتور محلی مصحف محشی")
    print(f"پوشه: {ROOT}")
    print()
    for line in report.lines:
        print(line)
    print()
    if report.ok:
        print("آماده است. از همین پوشه:")
        print("  python3 -m engine serve")
        print("  python3 -m engine «بقره ۹۱»")
        print()
        print("صفحهٔ HTML: http://127.0.0.1:8765")
        print("سؤال در ریپو ذخیره نمی‌شود.")
        return 0
    print("چیزی ناقص است. دوباره کلون کن یا git pull بزن.")
    print("  git clone https://github.com/Mahditalebian/mushaf-mohasha.git")
    return 1
