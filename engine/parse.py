from __future__ import annotations

import re
from dataclasses import dataclass

from . import surahs
from .normalize import fold, to_ascii_digits
from .quran import ayah_count


@dataclass
class ParsedQuery:
    kind: str  # verse | range | topic | marks
    surah: int | None = None
    start: int | None = None
    end: int | None = None
    topic: str | None = None
    mark: str | None = None
    extra_terms: list[str] | None = None


_MARK_WORDS = {
    "لازم": "ۘ",
    "م": "ۘ",
    "ممنوع": "ۙ",
    "لا": "ۙ",
    "قلی": "ۗ",
    "قلي": "ۗ",
    "وقف اولی": "ۗ",
    "صلی": "ۖ",
    "صلي": "ۖ",
    "وصل اولی": "ۖ",
    "جایز": "ۚ",
    "جايز": "ۚ",
    "معانقه": "ۛ",
    "مراقبه": "ۛ",
    "سکت": "ۜ",
}

_TOPIC_HINTS = (
    "وقف",
    "وصل",
    "ابتدا",
    "کلا",
    "كلّا",
    "كلا",
    "بلی",
    "نعم",
    "قبیح",
    "تام",
    "کافی",
    "حسن",
    "سکت",
    "معانقه",
    "لازم",
    "ممنوع",
)


def parse_query(raw: str) -> ParsedQuery:
    q = to_ascii_digits(raw).strip()
    folded = fold(q)

    mark = _detect_mark(folded)
    if mark and not re.search(r"\d", q):
        # «همه وقف لازم» / «مواضع معانقه»
        if any(k in folded for k in ("همه", "مواضع", "فهرست", "لیست", "کجا")):
            return ParsedQuery(kind="marks", mark=mark, topic=q, extra_terms=[mark])

    verse = _detect_verse(q)
    if verse:
        surah, start, end = verse
        kind = "range" if end != start else "verse"
        extra = []
        if mark:
            extra.append(MARK_NAME.get(mark, ""))
        return ParsedQuery(
            kind=kind,
            surah=surah,
            start=start,
            end=end,
            topic=q,
            mark=mark,
            extra_terms=extra or None,
        )

    if mark:
        return ParsedQuery(kind="topic", topic=q, mark=mark, extra_terms=[MARK_NAME.get(mark, "")])

    return ParsedQuery(kind="topic", topic=q, extra_terms=_topic_terms(folded))


MARK_NAME = {v: k for k, v in [("لازم", "ۘ"), ("ممنوع", "ۙ"), ("قلی", "ۗ"), ("صلی", "ۖ"), ("جایز", "ۚ"), ("معانقه", "ۛ"), ("سکت", "ۜ")]}


def _detect_mark(folded: str) -> str | None:
    for word, symbol in sorted(_MARK_WORDS.items(), key=lambda x: -len(x[0])):
        if fold(word) in folded:
            return symbol
    return None


def _detect_verse(q: str) -> tuple[int, int, int] | None:
    q = re.sub(r"[،,]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()

    # 2:91 or 2/91
    m = re.search(r"\b(\d{1,3})\s*[:/]\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?\b", q)
    if m:
        s, a, b = int(m.group(1)), int(m.group(2)), m.group(3)
        if 1 <= s <= 114:
            end = int(b) if b else a
            return _clamp(s, a, end)

    # آیه 91 بقره / بقره آیه 91 / بقره 91 / بقره 90 تا 92
    names = sorted(surahs.ALIASES.keys(), key=len, reverse=True)
    found_s = None
    folded_q = fold(q)
    for name in names:
        if not name:
            continue
        if len(name) <= 2:
            if re.search(rf"(^|[^0-9a-zآ-ی]){re.escape(name)}([^0-9a-zآ-ی]|$)", folded_q):
                found_s = surahs.ALIASES[name]
                break
        elif name in folded_q:
            found_s = surahs.ALIASES[name]
            break
    if found_s is None:
        return None

    # numbers after removing surah words
    nums = [int(x) for x in re.findall(r"\d+", q)]
    # drop surah number if user wrote «سوره 2 آیه 91»
    if re.search(r"سوره\s*\d+", q) and len(nums) >= 2:
        nums = nums[1:]
    if not nums:
        # whole surah is too big; default first ayah as hint
        return _clamp(found_s, 1, 1)
    start = nums[0]
    end = nums[1] if len(nums) > 1 and re.search(r"(تا|-|–)", q) else start
    return _clamp(found_s, start, end)


def _clamp(surah: int, start: int, end: int) -> tuple[int, int, int]:
    n = ayah_count(surah)
    start = max(1, min(start, n or start))
    end = max(start, min(end, n or end))
    return surah, start, end


def _topic_terms(folded: str) -> list[str]:
    return [h for h in _TOPIC_HINTS if fold(h) in folded]
