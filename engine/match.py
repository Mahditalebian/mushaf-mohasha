"""کارت تطبیق دقیق آیه با مصحف محشی.

علامت‌ها از متن عثمانی همین ریپوست؛ همان نظامی که مصحف محشی
(مرکز طبع و نشر) روی آن حاشیه نوشته. عین جملهٔ حاشیه را نداریم؛
این کارت می‌گوید کجا را در کتاب باز کنی و هر علامت را چطور معنا کنی.
"""

from __future__ import annotations

import re

from . import quran
from .models import MARKS, Verse
from .pages import page_of

# اگر تکه‌ای بی‌علامت از این تعداد کلمه بیشتر باشد، محشی معمولاً نقطهٔ اضطراری می‌گوید
LONG_WORDS = 11


def segments(text: str) -> list[tuple[str, str | None]]:
    """تکه‌های بین علائم: (متن, علامتِ پایان یا None)."""
    marks = "".join(map(re.escape, MARKS))
    parts = re.split(f"([{marks}])", text)
    out: list[tuple[str, str | None]] = []
    i = 0
    while i < len(parts):
        chunk = parts[i]
        mark = None
        if i + 1 < len(parts) and parts[i + 1] in MARKS:
            mark = parts[i + 1]
            i += 2
        else:
            i += 1
        cleaned = _words(chunk)
        if cleaned or mark:
            out.append((cleaned, mark))
    return out


def _words(text: str) -> str:
    t = re.sub(r"[۞۩۟]", "", text)
    return " ".join(t.split())


def word_count(text: str) -> int:
    return len(text.split()) if text.strip() else 0


def alignment_card(verse: Verse) -> str:
    page, juz = page_of(verse.surah, verse.ayah)
    segs = segments(verse.text)
    lines: list[str] = []
    lines.append(f"## کارت تطبیق — {verse.surah_name} {verse.ayah}")
    if page:
        lines.append(f"مصحف ۶۰۴صفحه‌ای: **صفحه {page}**  ·  جزء {juz}")
        lines.append("کتاب محشی را روی همین صفحه باز کن و علائم را یکی‌یکی چک کن.")
    lines.append("")
    lines.append("متن:")
    lines.append(verse.text)
    lines.append("")

    lines.append("### چک‌لیست علائم چاپی")
    n = 0
    for chunk, mark in segs:
        if not mark:
            continue
        n += 1
        meta = MARKS[mark]
        last = " ".join(chunk.split()[-5:])
        nxt = ""
        for later_chunk, _ in segs[segs.index((chunk, mark)) + 1 :]:
            if later_chunk.strip():
                nxt = " ".join(later_chunk.split()[:6])
                break
        lines.append(
            f"{n}. وقف روی «{last}» — علامت **{meta['letter']} / {meta['name']}** {mark}"
        )
        if nxt:
            lines.append(f"   ابتدا از: «{nxt}»")
        lines.append(f"   کار در محشی: {meta['rule']}")
        lines.append(f"   در کتاب: همین علامت باید روی همین کلمه باشد.")
    if n == 0:
        lines.append("این آیه علامت میانی ندارد. فقط رأس آیه محل وقف سنت است.")
        lines.append("اگر آیه بلند است، حاشیهٔ محشی بهترین نقطهٔ اضطراری را می‌گوید.")
    lines.append("")

    long_ones = [
        (chunk, mark) for chunk, mark in segs if word_count(chunk) >= LONG_WORDS
    ]
    lines.append("### تکه‌های بی‌علامتِ بلند (کار ویژهٔ محشی)")
    if long_ones:
        lines.append(
            "مستفید: گاهی چند سطر علامت ندارد ولی یک نفس نمی‌رسد. "
            "محشی همین‌جا در حاشیه بهترین نقطه را می‌گوید."
        )
        for i, (chunk, mark) in enumerate(long_ones, 1):
            preview = chunk if len(chunk) < 180 else chunk[:177] + "…"
            end = f"تا علامت {MARKS[mark]['letter']}" if mark else "تا پایان آیه"
            lines.append(f"{i}. {word_count(chunk)} کلمه {end}: {preview}")
            lines.append("   در حاشیهٔ همان صفحه دنبال پیشنهاد وقف اضطراری بگرد.")
    else:
        lines.append("تکهٔ خیلی بلندِ بی‌علامت ندارد؛ علائم چاپی معمولاً کافی‌اند.")
    lines.append("")

    lines.append("### رأس آیه")
    lines.append(
        f"وقف روی آخر آیه «{' '.join(verse.text.split()[-3:])}» — سنت است، "
        "حتی اگر از نظر اعراب حسن باشد. ابتدا از اول آیهٔ بعد."
    )
    lines.append("")
    lines.append("### اگر با کتاب یکی نبود")
    lines.append(
        "چاپ‌های محشی بعد از بازنگری کمیسیون مرکز طبع ممکن است یک علامت را جابه‌جا کرده باشند. "
        "عکس همان صفحه را بفرست تا عین حاشیه خوانده شود."
    )
    return "\n".join(lines)


def match_verse(surah: int, ayah: int) -> str:
    v = quran.make_verse(surah, ayah)
    if v is None:
        return f"آیه پیدا نشد: {surah}:{ayah}"
    return alignment_card(v)
