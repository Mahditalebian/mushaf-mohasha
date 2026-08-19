"""جدول وقف و ابتدا (سید علی حسینی، بر پایهٔ مصحف محشی)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .normalize import fold
from .paths import JADVAL_DIR
from .quran import get_text

RAW = JADVAL_DIR


_DROP = dict.fromkeys(
    map(
        ord,
        "ًٌٍَُِّْٰٕٖۣٓٔٗ٘۟۠ۡۢۤۥۦ۪ۭۧۨ۫۬ـۖۗۘۙۚۛۜ۩۞"
        + "".join(chr(c) for c in range(0x0610, 0x061B)),
    ),
    None,
)


def _norm_ar(s: str) -> str:
    t = s.replace("ٰ", "ا").replace("ٱ", "ا")
    t = fold(t).translate(_DROP)
    for a, b in (
        ("أ", "ا"),
        ("إ", "ا"),
        ("آ", "ا"),
        ("ٱ", "ا"),
        ("ة", "ه"),
        ("ۀ", "ه"),
        ("ى", "ی"),
        ("ي", "ی"),
        ("ؤ", "و"),
        ("ئ", ""),
        ("ء", ""),
        (" ", ""),
        ("‌", ""),
        ("ـ", ""),
    ):
        t = t.replace(a, b)
    return t


@lru_cache(maxsize=1)
def load_rows() -> list[dict]:
    rows: list[dict] = []
    if not RAW.exists():
        return rows
    for path in sorted(RAW.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def by_verse(surah: int, ayah: int) -> list[dict]:
    return [r for r in load_rows() if r.get("surah") == surah and r.get("ayah") == ayah]


def verify_row(row: dict) -> dict:
    text = get_text(row["surah"], row["ayah"]) or ""
    folded = _norm_ar(text)
    hits = []
    for item in row.get("waqf", []) + row.get("ibtida", []):
        phrase = item.get("on") or item.get("from") or ""
        if not phrase:
            hits.append({"phrase": phrase, "ok": None})
            continue
        ok = _norm_ar(phrase) in folded
        hits.append({"phrase": phrase, "ok": ok})
    return {
        "surah": row["surah"],
        "ayah": row["ayah"],
        "ok": all(h["ok"] is not False for h in hits),
        "hits": hits,
    }


def coverage() -> dict:
    rows = load_rows()
    checked = [verify_row(r) for r in rows]
    ok = sum(1 for c in checked if c["ok"])
    surahs = sorted({r["surah"] for r in rows})
    return {
        "rows": len(rows),
        "matched": ok,
        "failed": len(rows) - ok,
        "surahs": surahs,
        "failures": [c for c in checked if not c["ok"]][:20],
    }


def format_row(row: dict) -> str:
    lines = [f"جدول محشی · سوره {row['surah']} آیه {row['ayah']} · جزء {row.get('juz','')}"]
    for w, i in zip(row.get("waqf", []), row.get("ibtida", []) or [{}] * 20):
        tag = w.get("tag") or i.get("tag") or ""
        on = w.get("on") or "—"
        fr = i.get("from") or "—"
        prefix = f"{tag} · " if tag else ""
        lines.append(f"- {prefix}وقف روی «{on}»  →  ابتدا از «{fr}»")
    extra_w = row.get("waqf", [])[len(row.get("ibtida", [])) :]
    extra_i = row.get("ibtida", [])[len(row.get("waqf", [])) :]
    for w in extra_w:
        lines.append(f"- وقف روی «{w.get('on')}»")
    for i in extra_i:
        lines.append(f"- ابتدا از «{i.get('from')}»")
    return "\n".join(lines)
