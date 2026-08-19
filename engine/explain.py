"""استدلال چهاربخشی از دادهٔ همین ریپو.

عین جملهٔ حاشیهٔ کتاب کاغذی را نداریم. منبع حکم:
جدول حسینی (بر پایهٔ مصحف محشی) + علائم چاپی + اصول معنی‌محوری +
یادداشت ثابت آیه اگر از قبل نوشته شده باشد.
"""

from __future__ import annotations

import re

from . import jadval
from .models import ContextPack, MarkHit, Verse
from .pages import page_of

_PART_HEAD = re.compile(
    r"^##\s*([۱۲۳۴1-4])\)\s*.+$",
    re.M,
)

_DIGIT = {"1": "1", "2": "2", "3": "3", "4": "4", "۱": "1", "۲": "2", "۳": "3", "۴": "4"}


def explain(pack: ContextPack) -> dict:
    if pack.kind in {"verse", "range"} and pack.verses:
        return _explain_verses(pack)
    if pack.kind == "marks":
        return _explain_marks(pack)
    return _explain_topic(pack)


def format_explanation(ex: dict) -> str:
    if not ex:
        return ""
    lines: list[str] = []
    if ex.get("title"):
        lines.append(f"# {ex['title']}")
    meta = []
    if ex.get("page"):
        meta.append(f"صفحه {ex['page']} مصحف ۶۰۴صفحه‌ای")
    if ex.get("juz"):
        meta.append(f"جزء {ex['juz']}")
    if meta:
        lines.append(" · ".join(meta))
    if ex.get("intro"):
        lines.append("")
        lines.append(ex["intro"])
    table = ex.get("table") or []
    if table:
        lines.append("")
        lines.append("## جدول وقف روی / ابتدا از")
        lines.append("")
        lines.append("| نوع | وقف روی | ابتدا از | چرا |")
        lines.append("| --- | --- | --- | --- |")
        for row in table:
            lines.append(
                f"| {row.get('tag') or '—'} | {row.get('on') or '—'} | "
                f"{row.get('from') or '—'} | {row.get('why') or ''} |"
            )
    best = ex.get("best") or []
    if best:
        lines.append("")
        lines.append("## بهترین مواضع (ترکیب محشی + علائم چاپی)")
        lines.append("")
        lines.append("| رتبه | امتیاز | وقف روی | ابتدا از | منبع |")
        lines.append("| --- | --- | --- | --- | --- |")
        for row in best:
            lines.append(
                f"| {row.get('rank')} | {row.get('score')} | {row.get('waqf_on') or '—'} | "
                f"{row.get('ibtida_from') or '—'} | {row.get('source') or '—'} |"
            )
        if any(b.get("source", "").startswith("تأیید دو منبع") for b in best):
            lines.append("")
            lines.append("«تأیید دو منبع» یعنی جدول محشی و علامت چاپی اینجا همرأی‌اند — مطمئن‌ترین جای وقف.")
    if ex.get("waqf"):
        lines.append("")
        lines.append("## ۱) دلیل وقف")
        lines.append(ex["waqf"])
    if ex.get("wasl"):
        lines.append("")
        lines.append("## ۲) دلیل وصل")
        lines.append(ex["wasl"])
    if ex.get("ibtida"):
        lines.append("")
        lines.append("## ۳) دلیل ابتدا")
        lines.append(ex["ibtida"])
    if ex.get("wrong"):
        lines.append("")
        lines.append("## ۴) حالات اشتباه")
        lines.append(ex["wrong"])
    if ex.get("disclaimer"):
        lines.append("")
        lines.append(ex["disclaimer"])
    return "\n".join(lines).strip() + "\n"


def _explain_verses(pack: ContextPack) -> dict:
    verses = pack.verses
    first = verses[0]
    page, juz = page_of(first.surah, first.ayah)
    title = (
        f"{first.surah_name} {first.ayah}"
        if len(verses) == 1
        else f"{first.surah_name} {verses[0].ayah}–{verses[-1].ayah}"
    )

    table: list[dict] = []
    for v in verses:
        table.extend(_table_for_verse(v, [r for r in pack.jadval if r.get("surah") == v.surah and r.get("ayah") == v.ayah]))

    parsed_note = _split_note(pack.notes[0][1]) if pack.notes else {}
    generated = _generate_parts(verses, pack.jadval)

    source = "note" if parsed_note else "generated"
    parts = {
        "waqf": parsed_note.get("1") or generated["waqf"],
        "wasl": parsed_note.get("2") or generated["wasl"],
        "ibtida": parsed_note.get("3") or generated["ibtida"],
        "wrong": parsed_note.get("4") or generated["wrong"],
    }
    # اگر یادداشت چهاربخش نبود، متن کامل را در مقدمه می‌آوریم
    intro_bits = []
    if len(verses) == 1:
        intro_bits.append(first.text)
    if pack.notes and not parsed_note:
        intro_bits.append(pack.notes[0][1].strip())
    elif source == "note":
        intro_bits.append("این جواب از یادداشت ثابت همین ریپو است.")

    notes_from_table = [r.get("note") for r in pack.jadval if r.get("note")]
    if notes_from_table:
        intro_bits.append("یادداشت جدول محشی: " + " ".join(notes_from_table))

    best_rows = [
        {
            "rank": e.get("rank"),
            "score": e.get("score"),
            "waqf_on": e.get("waqf_on"),
            "ibtida_from": e.get("ibtida_from"),
            "source": e.get("source"),
        }
        for e in pack.best[:5]
    ]

    return {
        "title": title,
        "page": page,
        "juz": juz,
        "source": source,
        "intro": "\n\n".join(intro_bits),
        "table": table,
        "best": best_rows,
        "waqf": parts["waqf"].strip(),
        "wasl": parts["wasl"].strip(),
        "ibtida": parts["ibtida"].strip(),
        "wrong": parts["wrong"].strip(),
        "disclaimer": (
            "منبع حکم: جدول وقف و ابتدا (سید علی حسینی، بر پایهٔ مصحف محشی) "
            "+ علائم چاپی مصحف + اصول معنی‌محوری. "
            "عین جملهٔ حاشیهٔ کتاب کاغذی در داده نیست."
        ),
    }


def _table_for_verse(verse: Verse, rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        note = (row.get("note") or "").strip()
        if note and _is_instruction(note):
            out.append(
                {
                    "tag": tag_or_note(row),
                    "on": "—",
                    "from": "—",
                    "why": note,
                }
            )
            continue
        for w, b in _pairs(row):
            on = (w.get("on") or "").strip()
            fr = (b.get("from") or "").strip()
            tag = (w.get("tag") or b.get("tag") or "").strip()
            if not on and not fr:
                continue
            if _is_instruction(on) or _is_instruction(fr):
                out.append(
                    {
                        "tag": tag or "یادداشت",
                        "on": "—",
                        "from": "—",
                        "why": note or f"{on} {fr}".strip(),
                    }
                )
                continue
            why = _why(tag, on, fr, verse.marks)
            if note and "یادداشت" in tag.replace("ي", "ی"):
                why = (why + " " + note).strip()
            out.append({"tag": tag or "جدول محشی", "on": on or "—", "from": fr or "—", "why": why})
    for m in verse.marks:
        if _already(out, m.before, m.after):
            continue
        out.append(
            {
                "tag": f"علامت {m.letter}",
                "on": m.before,
                "from": m.after or "آیهٔ بعد",
                "why": m.rule,
            }
        )
    last = " ".join(verse.text.split()[-3:])
    out.append(
        {
            "tag": "رأس آیه",
            "on": last,
            "from": "اول آیهٔ بعد",
            "why": "وقف رأس آیه سنت است؛ ابتدا از آیهٔ بعد.",
        }
    )
    return out


def _already(rows: list[dict], on: str, fr: str) -> bool:
    n_on = jadval._norm_ar(on or "")
    n_fr = jadval._norm_ar(fr or "")
    if not n_on:
        return False
    for r in rows:
        if n_on and n_on in jadval._norm_ar(r.get("on") or ""):
            return True
        if n_on and jadval._norm_ar(r.get("on") or "") in n_on:
            return True
        if n_fr and n_fr and n_fr in jadval._norm_ar(r.get("from") or ""):
            return True
    return False


def _pairs(row: dict) -> list[tuple[dict, dict]]:
    waqf = row.get("waqf") or []
    ibtida = row.get("ibtida") or []
    n = max(len(waqf), len(ibtida), 1)
    out: list[tuple[dict, dict]] = []
    for i in range(n):
        w = waqf[i] if i < len(waqf) else {}
        b = ibtida[i] if i < len(ibtida) else {}
        out.append((w, b))
    return out


def _why(tag: str, on: str, fr: str, marks: list[MarkHit]) -> str:
    bits: list[str] = []
    meaning = _tag_meaning(tag)
    if meaning:
        bits.append(meaning)
    if on and fr and jadval._norm_ar(on) == jadval._norm_ar(fr):
        bits.append("وقف حسن: می‌ایستی و دوباره از همین عبارت شروع می‌کنی.")
    elif fr:
        bits.append(f"بعد از این وقف ابتدا از «{fr}».")
    for m in marks:
        if on and jadval._norm_ar(on) and jadval._norm_ar(on) in jadval._norm_ar(m.before):
            bits.append(f"نزدیک علامت {m.letter} / {m.name}.")
            break
    return " ".join(bits).strip()


def _tag_meaning(tag: str) -> str:
    if not tag:
        return "پیشنهاد جدول محشی."
    t = tag.replace("ي", "ی").replace("ك", "ک")
    parts: list[str] = []
    if "یادداشت" in t:
        parts.append("یادداشت جدول محشی.")
    if "اضطرار" in t:
        parts.append("اگر نفس نرسید.")
    if "اولویت یکسان" in t:
        parts.append("هر دو وجه برابرند.")
    elif "اولویت اول" in t or "اولویت یک" in t:
        parts.append("پیشنهاد اصلی جدول.")
    elif "اولویت دوم" in t:
        parts.append("اولویت بعدی.")
    elif "اولویت سوم" in t:
        parts.append("اولویت سوم.")
    if "مورد اول" in t:
        parts.append("وجه اول.")
    elif "مورد دوم" in t:
        parts.append("وجه دوم.")
    elif "مورد سوم" in t:
        parts.append("وجه سوم.")
    elif "مورد چهارم" in t:
        parts.append("وجه چهارم.")
    if "مکث" in t:
        parts.append("مکث کوتاه.")
    return " ".join(parts)


def _generate_parts(verses: list[Verse], rows: list[dict]) -> dict:
    waqf_l: list[str] = []
    wasl_l: list[str] = []
    ibtida_l: list[str] = []
    wrong_l: list[str] = []

    for v in verses:
        local = [r for r in rows if r.get("surah") == v.surah and r.get("ayah") == v.ayah]
        label = f"{v.surah_name} {v.ayah}"
        if len(verses) > 1:
            waqf_l.append(f"**{label}**")
            wasl_l.append(f"**{label}**")
            ibtida_l.append(f"**{label}**")
            wrong_l.append(f"**{label}**")

        if local:
            waqf_l.append(_waqf_from_jadval(v, local))
            ibtida_l.append(_ibtida_from_jadval(v, local))
        else:
            waqf_l.append(
                "در جدول محشی حسینی برای این آیه سطر جدا نیست. "
                "پس حکم را از علائم چاپی و معنی جمله می‌گیریم."
            )
            ibtida_l.append(_ibtida_from_marks(v))

        waqf_l.append(_waqf_from_marks(v))
        wasl_l.append(_wasl_from(v, local))
        wrong_l.append(_wrong_from(v, local))

        last = " ".join(v.text.split()[-3:])
        waqf_l.append(f"رأس آیه روی «{last}» سنت است؛ ابتدا از اول آیهٔ بعد.")

    return {
        "waqf": "\n\n".join(x for x in waqf_l if x),
        "wasl": "\n\n".join(x for x in wasl_l if x),
        "ibtida": "\n\n".join(x for x in ibtida_l if x),
        "wrong": "\n\n".join(x for x in wrong_l if x),
    }


def _waqf_from_jadval(verse: Verse, rows: list[dict]) -> str:
    lines = [
        "طبق جدول محشی (حسینی) این وقف‌ها برای قرائت ترتیل پیشنهاد شده:"
    ]
    for row in rows:
        if row.get("note"):
            lines.append(row["note"].strip())
        for w, b in _pairs(row):
            on = (w.get("on") or "").strip()
            fr = (b.get("from") or "").strip()
            tag = (w.get("tag") or b.get("tag") or "").strip()
            if not on and not fr:
                continue
            if _is_instruction(on) or _is_instruction(fr):
                continue
            head = f"وقف روی «{on or '—'}» → ابتدا از «{fr or '—'}»"
            extra = _tag_meaning(tag)
            if on and fr and jadval._norm_ar(on) == jadval._norm_ar(fr):
                extra = (extra + " این وقف حسن است: تکهٔ اول مفید است، ولی برای ادامه باید همان عبارت را تکرار کنی.").strip()
            lines.append(f"- {head}. {extra}".strip())
    lines.append(
        "معیار محشی معنی‌محوری است: جایی بایست که جمله مفید باشد و مراد خدا خراب نشود، "
        "نه جایی که فقط نفس تمام شده."
    )
    return "\n".join(lines)


def _is_instruction(text: str) -> bool:
    t = (text or "").replace("ي", "ی").replace("ك", "ک")
    return any(k in t for k in ("باید", "وصل خوانده", "نایست", "نباید", "به وصل"))


def tag_or_note(row: dict) -> str:
    for item in (row.get("waqf") or []) + (row.get("ibtida") or []):
        if item.get("tag"):
            return item["tag"]
    return "یادداشت"


def _ibtida_from_marks(verse: Verse) -> str:
    lines = [
        "ابتدا فقط اختیاری است. اگر جای بدی ایستادی، برگرد و از جای درست شروع کن."
    ]
    if not verse.marks:
        lines.append("این آیه علامت میانی ندارد؛ ابتدا از اول آیهٔ بعد، یا از همان جملهٔ کاملی که جدول گفته.")
        return "\n".join(lines)
    for m in verse.marks:
        if not m.after:
            continue
        lines.append(f"- بعد از وقف روی «{m.before}» از «{m.after}» شروع کن.")
        if m.symbol == "ۘ":
            lines.append("  جملهٔ بعد سخن جداست؛ به قول قبل نچسبان.")
        if m.symbol == "ۙ":
            lines.append("  از بعدِ ممنوع شروع نکن؛ اعاده کن و وصل بخوان.")
    return "\n".join(lines)


def _ibtida_from_jadval(verse: Verse, rows: list[dict]) -> str:
    lines = [
        "ابتدا فقط اختیاری است. اگر جای بدی ایستادی، برگرد و از جای درست شروع کن."
    ]
    for row in rows:
        if row.get("note") and _is_instruction(row["note"]):
            lines.append("- " + row["note"].strip() + " پس از وسط این دو آیه شروع نکن.")
            continue
        for w, b in _pairs(row):
            on = (w.get("on") or "").strip()
            fr = (b.get("from") or "").strip()
            if _is_instruction(on) or _is_instruction(fr):
                lines.append(f"- {(row.get('note') or (on + ' ' + fr)).strip()}")
                continue
            if not fr:
                continue
            if on and jadval._norm_ar(on) == jadval._norm_ar(fr):
                lines.append(
                    f"- بعد از وقف روی «{on}» از خود «{fr}» دوباره شروع کن. "
                    "شروع از کلمهٔ بعدی معمولاً جمله را بی‌سر می‌کند."
                )
            elif on:
                lines.append(
                    f"- بعد از وقف روی «{on}» از «{fr}» شروع کن. "
                    "از وسط همان تکه یا از یک کلمه جلوتر شروع نکن."
                )
            else:
                lines.append(f"- ابتدا از «{fr}».")
    for m in verse.marks:
        if m.after:
            lines.append(
                f"- بعد از علامت {m.letter} روی «{m.before}»، ابتدا از «{m.after}»."
            )
    return "\n".join(lines)


def _waqf_from_marks(verse: Verse) -> str:
    if not verse.marks:
        return (
            "این آیه علامت میانی ندارد. فقط رأس آیه محل وقف سنت است. "
            "اگر آیه بلند است و نفس نمی‌رسد، همان نقطهٔ جدول محشی "
            "(یا نزدیک‌ترین جملهٔ کامل) وقف اضطراری است."
        )
    lines = ["علائم چاپی مصحف:"]
    for m in verse.marks:
        lines.append(f"- روی «{m.before}» علامت **{m.letter} / {m.name}**. {m.rule}")
        if m.symbol == "ۘ":
            lines.append(
                "  اگر وصل کنی، دو طرف قاطی می‌شود و شنونده معنا را عوض می‌فهمد. باید ایستاد."
            )
        elif m.symbol == "ۙ":
            lines.append(
                "  اینجا نباید ایستاد. اگر نفس برید، اعاده کن و وصل بخوان."
            )
        elif m.symbol == "ۛ":
            lines.append("  معانقه: فقط روی یکی از دو نقطه بایست؛ روی هر دو نه.")
    return "\n".join(lines)


def _wasl_from(verse: Verse, rows: list[dict]) -> str:
    lines = [
        "این‌ها را نباید برید، وگرنه جمله سر ندارد یا معنا عوض می‌شود:",
        "- فعل را از فاعل، مضاف را از مضاف‌الیه، موصول را از صله جدا نکن.",
        "- قول را از گفته جدا نکن («قالوا» بدون مقول قول ناقص است).",
        "- شرط را از جزا و قسم را از جوابش نبر.",
    ]
    for m in verse.marks:
        if m.symbol == "ۙ":
            lines.append(
                f"- علامت ممنوع روی «{m.before}»: این تکه را به بعدش وصل کن. "
                f"ادامه: «{m.after or '…'}»."
            )
        elif m.symbol == "ۖ":
            lines.append(
                f"- روی «{m.before}» وصل اولی است؛ پیوستگی معنا به «{m.after or 'بعد'}» قوی‌تر است."
            )
        elif m.symbol == "ۘ":
            lines.append(
                f"- دو طرف «{m.before}» را به هم وصل نکن. جدا کردن اینجا حفظ معناست."
            )
    for row in rows:
        note = (row.get("note") or "")
        if "وصل" in note:
            lines.append("- " + note)
        for w, b in _pairs(row):
            on = (w.get("on") or "").strip()
            fr = (b.get("from") or "").strip()
            if on and fr and "باید وصل" in (on + fr + note):
                lines.append(f"- جدول می‌گوید این موضع وصل خوانده شود: «{on}» / «{fr}».")
    return "\n".join(lines)


def _wrong_from(verse: Verse, rows: list[dict]) -> str:
    lines = ["### وقف غلط", "- وسط مضاف و مفعول و صله نایست.", "- روی حرف نفی بدون منفی‌اش نایست (مثل «لا اله» بدون «الا الله»)."]
    for m in verse.marks:
        if m.symbol == "ۙ":
            lines.append(f"- وقف روی «{m.before}» (ممنوع): معنا ناقص یا فاسد می‌شود.")
        if m.symbol == "ۘ":
            lines.append(
                f"- وصل بی‌فاصله از روی «{m.before}»: سخن دو طرف قاطی می‌شود."
            )
    lines.append("### وصل غلط")
    lines.append("- قول مردم را به قول خدا بچسبانی طوری که یک گوینده به گوش برسد.")
    lines.append("- رحمت را به عذاب، یا مدح را به ذم، بی‌هیچ فاصله وصل کنی.")
    for m in verse.marks:
        if m.symbol == "ۘ":
            lines.append(f"- وصل از روی لازمِ «{m.before}».")
        if m.symbol == "ۗ":
            lines.append(
                f"- وصل کامل «{m.before}» به بعد، بدون هیچ فاصله: موضوع بعد داخل موضوع قبل می‌رود. قلی برای همین است."
            )
    lines.append("### ابتدای غلط")
    lines.append("- از وسط جمله، از مضاف‌الیه، از صله، یا از جزا بدون شرط شروع نکن.")
    for row in rows:
        for w, b in _pairs(row):
            on = (w.get("on") or "").strip()
            fr = (b.get("from") or "").strip()
            if on and fr and jadval._norm_ar(on) == jadval._norm_ar(fr):
                lines.append(
                    f"- بعد از وقف حسن روی «{on}» از کلمهٔ بعدی شروع نکن؛ همان عبارت را تکرار کن."
                )
            elif fr and not _is_instruction(fr):
                lines.append(f"- بعد از «{on or 'این وقف'}» از جایی غیر از «{fr}» شروع نکن.")
    lines.append("### اگر نفس برید")
    lines.append("1. روی همان کلمهٔ ناقص نمان.")
    lines.append("2. برگرد به نزدیک‌ترین ابتدای درست جدول یا اول جملهٔ کامل.")
    lines.append("3. وصل کن تا موضع مجاز بعدی.")
    return "\n".join(lines)


def _split_note(text: str) -> dict[str, str]:
    matches = list(_PART_HEAD.finditer(text))
    if len(matches) < 3:
        return {}
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        key = _DIGIT.get(m.group(1), "")
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if key:
            out[key] = text[start:end].strip()
    return out if {"1", "2", "3", "4"} <= set(out) else {}


def _explain_marks(pack: ContextPack) -> dict:
    symbol = None
    if pack.verses:
        for v in pack.verses:
            for m in v.marks:
                symbol = m.symbol
                break
            if symbol:
                break
    name = {"ۘ": "لازم", "ۙ": "ممنوع", "ۗ": "قلی", "ۖ": "صلی", "ۚ": "جایز", "ۛ": "معانقه", "ۜ": "سکت"}.get(symbol or "", "علامت")
    intro = f"مواضع علامت {name} در متن عثمانی این ریپو."
    table = []
    for v in pack.verses[:40]:
        for m in v.marks:
            if symbol and m.symbol != symbol:
                continue
            table.append(
                {
                    "tag": f"{v.surah_name} {v.ayah}",
                    "on": m.before,
                    "from": m.after or "آیهٔ بعد",
                    "why": m.rule,
                }
            )
    docs = "\n\n".join(d.snippet for d in pack.docs[:3])
    return {
        "title": f"مواضع {name}",
        "page": None,
        "juz": None,
        "source": "marks",
        "intro": intro,
        "table": table,
        "waqf": docs or f"علامت {name}: جای ایستادن یا نایستادن از روی خطر معناست.",
        "wasl": "وصل را از روی همین جدول و قاعدهٔ هر علامت بسنج؛ لازم را وصل نکن، ممنوع را نبر.",
        "ibtida": "بعد از هر وقف، از ستون «ابتدا از» شروع کن.",
        "wrong": "وقف روی ممنوع، وصل از روی لازم، و ابتدا از وسط جمله از اشتباه‌های تکراری است.",
        "disclaimer": "فهرست از متن عثمانی همین ریپو است.",
    }


def _explain_topic(pack: ContextPack) -> dict:
    snippets = "\n\n".join(f"**{d.title}**\n{d.snippet}" for d in pack.docs)
    return {
        "title": pack.query,
        "page": None,
        "juz": None,
        "source": "topic",
        "intro": "از دانش‌نامهٔ همین ریپو:",
        "table": [],
        "waqf": snippets or "در docs/ چیزی نزدیک این پرسش پیدا نشد. آیه را با شماره بپرس؛ مثلاً بقره ۹۱.",
        "wasl": "وصل یعنی دو تکه را بدون قطع بخوانی، چون وابستگی لفظی یا معنوی دارند.",
        "ibtida": "ابتدا فقط از جملهٔ وافی است. ابتدا اضطراری نداریم.",
        "wrong": "وقف قبیح، وصل دو موضوع متضاد، و شروع از وسط جمله معنای فاسد می‌سازد. جزئیات: docs/04-ghalat.md",
        "disclaimer": "برای حکم دقیق یک آیه، همان آیه را بپرس تا جدول محشی و علائم همان موضع بیاید.",
    }
