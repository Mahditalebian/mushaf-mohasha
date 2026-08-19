"""بهترین مواضع وقف و ابتدا — ترکیب جدول محشی + علائم چاپی.

دو منبع با هم سنجیده می‌شوند:

1. جدول وقف و ابتدا (سید علی حسینی، بر پایهٔ مصحف محشی) — استدلال معنایی،
   از بقره تا ماعون (۸۷۴ موضع). هر جا باشد اولویت دارد.
2. علائم چاپی مصحف (طبع و نشر / متن عثمانی Tanzil همراه pause marks) —
   کل قرآن، ۶۲۳۶ آیه.
3. رأس آیه — همیشه هست؛ وقف بر آن سنت است.

هر موضع امتیاز می‌گیرد؛ جایی که هر دو منبع همرأی باشند بالاترین امتیاز را
دارد («تأیید دو منبع»). خروجی برای هر آیه فهرست رتبه‌بندی‌شدهٔ «بهترین جا»هاست.
"""

from __future__ import annotations

from . import jadval, quran
from .explain import _is_instruction, _pairs, _tag_meaning
from .models import MARKS

# --- امتیاز علامت‌های چاپی به‌عنوان موضع وقف ---
_MARK_SCORE = {
    "ۘ": 100,   # لازم — باید ایستاد
    "ۗ": 75,    # قلی — وقف اولی
    "ۛ": 60,    # معانقه — فقط روی یکی از دو نقطه
    "ۚ": 55,    # جایز
    "ۜ": 45,    # سکت — قطع کوتاه بدون نفس
    "ۖ": 25,    # صلی — وصل بهتر است
    "ۙ": 0,     # ممنوع — نباید ایستاد
}

_MARK_KIND = {
    "ۘ": "waqf",
    "ۗ": "waqf",
    "ۛ": "waqf",
    "ۚ": "waqf",
    "ۜ": "sakt",
    "ۖ": "wasl_preferred",
    "ۙ": "avoid",
}

_AGREE_BONUS = 20
_RAS_SCORE = 65  # رأس آیه — سنت


def _tag_score(tag: str) -> int:
    """امتیاز پیش‌فرض یک موضع جدول محشی بر اساس تگ آن."""
    t = (tag or "").replace("ي", "ی").replace("ك", "ک")
    if "اضطرار" in t:
        return 30
    if "اولویت یکسان" in t:
        return 85
    if "اولویت اول" in t or "اولویت یک" in t:
        return 100
    if "اولویت دوم" in t:
        return 80
    if "اولویت سوم" in t:
        return 70
    if "مورد اول" in t:
        return 95
    if "مورد دوم" in t:
        return 85
    if "مورد سوم" in t:
        return 75
    if "مورد چهارم" in t:
        return 65
    if "یادداشت" in t:
        return 70
    return 85


def _entry(
    *,
    surah: int,
    ayah: int,
    on: str,
    fr: str,
    score: int,
    source: str,
    note: str,
    kind: str,
    tag: str = "",
) -> dict:
    return {
        "surah": surah,
        "ayah": ayah,
        "waqf_on": on.strip(),
        "ibtida_from": fr.strip(),
        "score": score,
        "source": source,
        "tag": tag.strip(),
        "note": note.strip(),
        "kind": kind,
    }


def best_places(surah: int, ayah: int) -> list[dict]:
    """فهرست رتبه‌بندی‌شدهٔ مواضع برای یک آیه (ترکیب دو منبع)."""
    v = quran.make_verse(surah, ayah)
    if v is None:
        return []
    rows = jadval.by_verse(surah, ayah)
    entries: list[dict] = []
    matched_marks: set[int] = set()

    # ۱) مواضع جدول محشی — منبع استدلالی
    for row in rows:
        if row.get("note") and _is_instruction(row["note"]):
            entries.append(
                _entry(
                    surah=surah,
                    ayah=ayah,
                    on=row["note"],
                    fr="",
                    score=70,
                    source="یادداشت جدول محشی",
                    note=row["note"],
                    kind="note",
                )
            )
            continue
        for w, b in _pairs(row):
            on = (w.get("on") or "").strip()
            fr = (b.get("from") or "").strip()
            tag = (w.get("tag") or b.get("tag") or "").strip()
            if not on and not fr:
                continue
            if _is_instruction(on) or _is_instruction(fr):
                entries.append(
                    _entry(
                        surah=surah,
                        ayah=ayah,
                        on=on,
                        fr=fr,
                        score=70,
                        source="دستور جدول محشی",
                        note=f"{on} {fr}".strip(),
                        kind="note",
                    )
                )
                continue
            score = _tag_score(tag)
            note = _tag_meaning(tag) or "پیشنهاد جدول محشی."
            if on and fr and jadval._norm_ar(on) == jadval._norm_ar(fr):
                note += " وقف حسن: می‌ایستی و همان عبارت را تکرار می‌کنی."
            entries.append(
                _entry(
                    surah=surah,
                    ayah=ayah,
                    on=on,
                    fr=fr,
                    score=score,
                    source="جدول محشی",
                    tag=tag,
                    note=note,
                    kind="waqf",
                )
            )

    # ۲) علائم چاپی — و جستجوی همرأیی با جدول
    for i, m in enumerate(v.marks):
        base = _MARK_SCORE.get(m.symbol, 50)
        kind = _MARK_KIND.get(m.symbol, "waqf")
        meta = MARKS[m.symbol]
        note = meta["rule"]
        if m.symbol == "ۖ":
            note += " برای ایستادن، جای قوی‌ترِ همین آیه را ببین."
        if m.symbol == "ۙ":
            note = "اینجا نایست؛ اگر نفس برید اعاده کن و وصل بخوان."
        if m.symbol == "ۛ":
            note += " فقط روی یکی از دو نقطه بایست."
        hit = _entry(
            surah=surah,
            ayah=ayah,
            on=m.before,
            fr=m.after or "اول آیهٔ بعد",
            score=base,
            source=f"علامت چاپی ({m.letter} / {m.name})",
            note=note,
            kind=kind,
        )
        # همرأیی یا اختلاف با جدول محشی؟
        agreed = False
        for e in entries:
            if e["kind"] != "waqf" or not e["waqf_on"]:
                continue
            if jadval._norm_ar(m.before) and (
                jadval._norm_ar(m.before) in jadval._norm_ar(e["waqf_on"])
                or jadval._norm_ar(e["waqf_on"]) in jadval._norm_ar(m.before)
            ):
                matched_marks.add(i)
                agreed = True
                if m.symbol == "ۙ":
                    # علامت چاپی ممنوع + موضع محشی
                    if "اضطرار" in (e["tag"] or ""):
                        e["source"] = "محشی: فقط اضطراری · چاپی: ممنوع"
                        e["score"] = 35
                        e["note"] = (
                            e["note"] + " علامت چاپی اینجا ممنوع است؛ جدول محشی "
                            "فقط برای اضطرار نفس اجازه می‌دهد، نه وقف برنامه‌ریزی‌شده."
                        ).strip()
                    else:
                        e["source"] = "اختلاف دو منبع (محشی: وقف · چاپی: ممنوع)"
                        e["score"] = min(e["score"], 40)
                        e["note"] = (
                            e["note"] + " علامت چاپی وقف را ممنوع می‌داند ولی جدول "
                            "محشی اینجا موضع گذاشته. در ترتیل جانب احتیاط را بگیر."
                        ).strip()
                    break
                if m.symbol == "ۖ":
                    e["score"] = max(e["score"], base) + 10
                    e["source"] = "تأیید دو منبع (محشی + علامت صلی)"
                    e["note"] = (
                        e["note"] + " صلی وصل را اولی می‌داند؛ وقف هم رواست."
                    ).strip()
                else:
                    e["score"] = max(e["score"], base) + _AGREE_BONUS
                    e["source"] = f"تأیید دو منبع (محشی + علامت {m.letter})"
                    e["note"] = (e["note"] + " " + note).strip()
                    if m.symbol == "ۘ":
                        e["kind"] = "waqf_lazim"
                break
        if not agreed:
            entries.append(hit)

    # ۳) رأس آیه — سنت
    last = " ".join(v.text.split()[-3:])
    entries.append(
        _entry(
            surah=surah,
            ayah=ayah,
            on=last,
            fr="اول آیهٔ بعد",
            score=_RAS_SCORE,
            source="رأس آیه (سنت)",
            note="وقف بر رأس آیه سنت است؛ ابتدا از اول آیهٔ بعد.",
            kind="waqf",
        )
    )

    entries.sort(key=lambda e: e["score"], reverse=True)
    for rank, e in enumerate(entries, 1):
        e["rank"] = rank
    return entries


def best_one(surah: int, ayah: int) -> dict | None:
    """بالاترین موضع پیشنهادی برای وقف در یک آیه."""
    for e in best_places(surah, ayah):
        if e["kind"] == "waqf":
            return e
    return None


def summary() -> dict:
    """آمار کل قرآن برای ترکیب دو منبع."""
    verses = quran.load_verses()
    rows = jadval.load_rows()
    jadval_verses: set[tuple[int, int]] = {
        (r.get("surah", 0), r.get("ayah", 0)) for r in rows
    }
    marked = 0
    mark_total = 0
    agree = 0
    for s, a in verses:
        v = quran.make_verse(s, a)
        if v is None:
            continue
        if v.marks:
            marked += 1
            mark_total += len(v.marks)
        if (s, a) in jadval_verses and v.marks:
            agree += sum(
                1 for e in best_places(s, a) if e["source"].startswith("تأیید دو منبع")
            )
    return {
        "total": len(verses),
        "jadval_rows": len(rows),
        "jadval_verses": len(jadval_verses),
        "marked_verses": marked,
        "mark_total": mark_total,
        "agreements": agree,
        "coverage": len(verses),  # رأس آیه همیشه هست
    }


def format_best(entries: list[dict], top: int = 0) -> str:
    if not entries:
        return "موضعی پیدا نشد."
    head = entries[0]
    lines = [f"## بهترین مواضع — {head['surah']}:{head['ayah']}"]
    shown = entries[:top] if top else entries
    for e in shown:
        src = e["source"]
        tag = f" · {e['tag']}" if e.get("tag") else ""
        lines.append(
            f"{e['rank']}. [{e['score']}] وقف روی «{e['waqf_on'] or '—'}»"
            f" → ابتدا از «{e['ibtida_from'] or '—'}» — {src}{tag}"
        )
        if e.get("note"):
            lines.append(f"   {e['note']}")
    return "\n".join(lines)


def best_cli(argv: list[str]) -> int:
    from .parse import parse_query

    if not argv:
        print("استفاده: python3 -m engine best «بقره ۹۱»", file=__import__("sys").stderr)
        return 2
    parsed = parse_query(" ".join(argv))
    if parsed.kind not in {"verse", "range"} or not parsed.surah:
        print("برای «بهترین جا» آیه را با شماره بپرس؛ مثلاً: بقره ۹۱", file=__import__("sys").stderr)
        return 2
    for ayah in range(parsed.start or 1, (parsed.end or parsed.start or 1) + 1):
        entries = best_places(parsed.surah, ayah)
        print(format_best(entries, top=5))
        print()
    return 0
