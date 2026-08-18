from __future__ import annotations

import re
from functools import lru_cache

from . import surahs
from .models import MARKS, MarkHit, Verse
from .paths import DATA_FILE

_MARK_RE = re.compile("(" + "|".join(map(re.escape, MARKS)) + ")")
_STRIP_RE = re.compile(
    "[" + "".join(map(re.escape, list(MARKS) + ["۞", "۩"])) + "]"
)


@lru_cache(maxsize=1)
def load_verses() -> dict[tuple[int, int], str]:
    out: dict[tuple[int, int], str] = {}
    for line in DATA_FILE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "|" not in line:
            continue
        s, a, text = line.split("|", 2)
        out[(int(s), int(a))] = text
    return out


def ayah_count(surah: int) -> int:
    verses = load_verses()
    n = 0
    while (surah, n + 1) in verses:
        n += 1
    return n


def get_text(surah: int, ayah: int) -> str | None:
    return load_verses().get((surah, ayah))


def split_marks(text: str) -> list[MarkHit]:
    hits: list[MarkHit] = []
    parts = _MARK_RE.split(text)
    # parts: chunk, mark, chunk, mark, chunk...
    i = 1
    while i < len(parts):
        symbol = parts[i]
        meta = MARKS[symbol]
        before = _clean(parts[i - 1]).split()
        after = _clean(parts[i + 1] if i + 1 < len(parts) else "").split()
        hits.append(
            MarkHit(
                symbol=symbol,
                letter=meta["letter"],
                name=meta["name"],
                rule=meta["rule"],
                before=" ".join(before[-4:]),
                after=" ".join(after[:4]),
            )
        )
        i += 2
    return hits


def _clean(text: str) -> str:
    return _STRIP_RE.sub("", text).replace("۟", "").strip()


def make_verse(surah: int, ayah: int) -> Verse | None:
    text = get_text(surah, ayah)
    if text is None:
        return None
    return Verse(
        surah=surah,
        ayah=ayah,
        surah_name=surahs.display(surah),
        text=text,
        marks=split_marks(text),
    )


def neighbors(surah: int, ayah: int) -> list[Verse]:
    out: list[Verse] = []
    for s, a in ((surah, ayah - 1), (surah, ayah + 1)):
        if a < 1:
            continue
        v = make_verse(s, a)
        if v:
            out.append(v)
    return out


def find_by_mark(symbol: str) -> list[Verse]:
    found: list[Verse] = []
    for (s, a), text in load_verses().items():
        if symbol in text:
            v = make_verse(s, a)
            if v:
                found.append(v)
    return found
