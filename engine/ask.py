from __future__ import annotations

from . import jadval, knowledge, quran
from .best import best_places
from .explain import explain, format_explanation
from .match import alignment_card
from .models import ContextPack, Verse
from .parse import parse_query


def ask(question: str) -> ContextPack:
    parsed = parse_query(question)
    pack = ContextPack(query=question, kind=parsed.kind, protocol=knowledge.protocol_text())

    extra = list(parsed.extra_terms or [])

    if parsed.kind in {"verse", "range"} and parsed.surah and parsed.start and parsed.end:
        for ayah in range(parsed.start, parsed.end + 1):
            v = quran.make_verse(parsed.surah, ayah)
            if v is None:
                pack.warnings.append(f"آیه پیدا نشد: {parsed.surah}:{ayah}")
                continue
            pack.verses.append(v)
            note = knowledge.existing_note(parsed.surah, ayah)
            if note:
                pack.notes.append(note)
            pack.jadval.extend(jadval.by_verse(parsed.surah, ayah))
            pack.best.extend(best_places(parsed.surah, ayah))
        if parsed.kind == "verse" and pack.verses:
            v0 = pack.verses[0]
            pack.neighbors = quran.neighbors(v0.surah, v0.ayah)
            extra.extend(_mark_terms(v0))
        extra.extend([pack.verses[0].surah_name] if pack.verses else [])

    elif parsed.kind == "marks" and parsed.mark:
        found = quran.find_by_mark(parsed.mark)
        pack.verses = found[:40]
        extra.append(parsed.mark)
        if len(found) > 40:
            pack.warnings.append(f"{len(found)} آیه این علامت را دارد؛ ۴۰ تای اول آمده.")

    else:
        if parsed.mark:
            found = quran.find_by_mark(parsed.mark)
            pack.verses = found[:12]
            if len(found) > 12:
                pack.warnings.append(f"{len(found)} آیه این علامت را دارد؛ ۱۲ تای اول آمده.")

    pack.docs = knowledge.search_docs(question, extra_terms=extra, limit=5 if pack.kind == "topic" else 4)
    pack.explanation = explain(pack)
    return pack


def _mark_terms(verse: Verse) -> list[str]:
    terms = [m.name for m in verse.marks]
    if any(m.symbol == "ۘ" for m in verse.marks):
        terms += ["لازم", "فساد معنا"]
    if any(m.symbol == "ۙ" for m in verse.marks):
        terms += ["ممنوع", "قبیح"]
    if any(m.symbol == "ۛ" for m in verse.marks):
        terms += ["معانقه"]
    if not verse.marks:
        terms += ["بی‌علامت", "اضطراری"]
    return terms


def format_pack(pack: ContextPack) -> str:
    lines: list[str] = []
    if pack.warnings:
        lines.append("هشدار:")
        for w in pack.warnings:
            lines.append(f"- {w}")
        lines.append("")

    if pack.explanation:
        lines.append(format_explanation(pack.explanation))
    else:
        lines.append(f"پرسش: {pack.query}")
        lines.append("")

    if pack.kind in {"verse", "range"} and pack.verses and len(pack.verses) <= 3:
        lines.append("## تطبیق با مصحف کاغذی")
        for v in pack.verses:
            lines.append(alignment_card(v))
            lines.append("")

    if pack.neighbors:
        lines.append("## آیه قبل و بعد")
        for v in pack.neighbors:
            lines.append(f"- {v.surah}:{v.ayah} {v.text}")
        lines.append("")

    if pack.docs and pack.kind != "topic":
        lines.append("## از دانش‌نامه")
        for doc in pack.docs[:2]:
            lines.append(f"### {doc.title}")
            lines.append(doc.snippet)
            lines.append("")

    lines.append("سؤال در ریپو ذخیره نشد.")
    return "\n".join(lines).strip() + "\n"
