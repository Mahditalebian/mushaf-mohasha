#!/usr/bin/env python3
"""جستجوی آیه و استخراج علائم وقف."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "quran-uthmani.txt"

MARKS = {
    "ۘ": "لازم (م) — وصل معنا را خراب می‌کند",
    "ۙ": "ممنوع (لا) — وقف معنا را خراب می‌کند",
    "ۗ": "قلی — وقف بهتر است",
    "ۖ": "صلی — وصل بهتر است",
    "ۚ": "جایز (ج)",
    "ۛ": "معانقه — فقط یکی از دو جا",
    "ۜ": "سکت",
}

SURAH_ALIASES = {
    "فاتحه": 1,
    "حمد": 1,
    "بقره": 2,
    "آل عمران": 3,
    "ال عمران": 3,
    "نساء": 4,
    "مائده": 5,
    "انعام": 6,
    "اعراف": 7,
    "انفال": 8,
    "توبه": 9,
    "یونس": 10,
    "يونس": 10,
    "هود": 11,
    "یوسف": 12,
    "يوسف": 12,
    "رعد": 13,
    "ابراهیم": 14,
    "حجر": 15,
    "نحل": 16,
    "اسراء": 17,
    "کهف": 18,
    "مریم": 19,
    "طه": 20,
    "انبیاء": 21,
    "حج": 22,
    "مؤمنون": 23,
    "نور": 24,
    "فرقان": 25,
    "شعراء": 26,
    "نمل": 27,
    "قصص": 28,
    "عنکبوت": 29,
    "روم": 30,
    "لقمان": 31,
    "سجده": 32,
    "احزاب": 33,
    "سبا": 34,
    "فاطر": 35,
    "یس": 36,
    "يس": 36,
    "صافات": 37,
    "ص": 38,
    "زمر": 39,
    "غافر": 40,
    "فصلت": 41,
    "شوری": 42,
    "شورى": 42,
    "زخرف": 43,
    "دخان": 44,
    "جاثیه": 45,
    "احقاف": 46,
    "محمد": 47,
    "فتح": 48,
    "حجرات": 49,
    "ق": 50,
    "ذاریات": 51,
    "طور": 52,
    "نجم": 53,
    "قمر": 54,
    "الرحمن": 55,
    "واقعه": 56,
    "حدید": 57,
    "مجادله": 58,
    "حشر": 59,
    "ممتحنه": 60,
    "صف": 61,
    "جمعه": 62,
    "منافقون": 63,
    "تغابن": 64,
    "طلاق": 65,
    "تحریم": 66,
    "ملک": 67,
    "قلم": 68,
    "حاقه": 69,
    "معارج": 70,
    "نوح": 71,
    "جن": 72,
    "مزمل": 73,
    "مدثر": 74,
    "قیامت": 75,
    "انسان": 76,
    "مرسلات": 77,
    "نبأ": 78,
    "نازعات": 79,
    "عبس": 80,
    "تکویر": 81,
    "انفطار": 82,
    "مطففین": 83,
    "انشقاق": 84,
    "بروج": 85,
    "طارق": 86,
    "اعلی": 87,
    "غاشیه": 88,
    "فجر": 89,
    "بلد": 90,
    "شمس": 91,
    "لیل": 92,
    "ضحی": 93,
    "شرح": 94,
    "تین": 95,
    "علق": 96,
    "قدر": 97,
    "بینه": 98,
    "زلزله": 99,
    "عادیات": 100,
    "قارعه": 101,
    "تکاثر": 102,
    "عصر": 103,
    "همزه": 104,
    "فیل": 105,
    "قریش": 106,
    "ماعون": 107,
    "کوثر": 108,
    "کافرون": 109,
    "نصر": 110,
    "مسد": 111,
    "اخلاص": 112,
    "فلق": 113,
    "ناس": 114,
}


def load_index() -> dict[tuple[int, int], str]:
    out: dict[tuple[int, int], str] = {}
    for line in DATA.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "|" not in line:
            continue
        s, a, text = line.split("|", 2)
        out[(int(s), int(a))] = text
    return out


def parse_ref(args: list[str]) -> tuple[int, int]:
    if len(args) == 1 and ":" in args[0]:
        s, a = args[0].split(":", 1)
        return int(s), int(a)
    if len(args) != 2:
        raise SystemExit("استفاده: lookup.py 2 26   یا   lookup.py بقره 26   یا   lookup.py 2:26")
    s, a = args
    if s.isdigit():
        return int(s), int(a)
    key = s.strip()
    if key not in SURAH_ALIASES:
        raise SystemExit(f"نام سوره شناخته نشد: {s}")
    return SURAH_ALIASES[key], int(a)


def describe_marks(text: str) -> list[str]:
    found = []
    for ch, meaning in MARKS.items():
        n = text.count(ch)
        if n:
            found.append(f"{ch} ×{n} — {meaning}")
    return found


def main() -> None:
    if not DATA.exists():
        raise SystemExit(f"فایل متن نیست: {DATA}")
    surah, ayah = parse_ref(sys.argv[1:])
    idx = load_index()
    text = idx.get((surah, ayah))
    if text is None:
        raise SystemExit(f"آیه پیدا نشد: {surah}:{ayah}")
    print(f"{surah}:{ayah}")
    print(text)
    marks = describe_marks(text)
    print()
    if marks:
        print("علائم:")
        for line in marks:
            print(" ", line)
    else:
        print("علائم میانی ندارد (رأس آیه جداگانه بررسی شود).")


if __name__ == "__main__":
    main()
