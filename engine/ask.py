from __future__ import annotations

from . import jadval, knowledge, quran
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
        if parsed.kind == "verse" and pack.verses:
            v0 = pack.verses[0]
            pack.neighbors = quran.neighbors(v0.surah, v0.ayah)
            extra.extend(_mark_terms(v0))
        extra.extend([pack.verses[0].surah_name] if pack.verses else [])

    elif parsed.kind == "marks" and parsed.mark:
        found = quran.find_by_mark(parsed.mark)
        pack.verses = found
        extra.append(parsed.mark)

    else:
        pack.docs = knowledge.search_docs(question, extra_terms=extra, limit=5)
        if parsed.mark:
            found = quran.find_by_mark(parsed.mark)
            pack.verses = found[:12]
            if len(found) > 12:
                pack.warnings.append(f"{len(found)} آیه این علامت را دارد؛ ۱۲ تای اول آمده.")
        return pack

    pack.docs = knowledge.search_docs(question, extra_terms=extra, limit=4)
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
    lines.append(f"# زمینه از ریپو")
    lines.append(f"پرسش: {pack.query}")
    lines.append(f"نوع: {pack.kind}")
    lines.append("")

    if pack.warnings:
        lines.append("هشدار:")
        for w in pack.warnings:
            lines.append(f"- {w}")
        lines.append("")

    if pack.verses:
        lines.append("## آیات")
        for v in pack.verses:
            lines.append(f"### {v.surah_name} {v.ayah}  ({v.surah}:{v.ayah})")
            lines.append(v.text)
            if v.marks:
                lines.append("علائم:")
                for m in v.marks:
                    bit = f"- وقف روی «{m.before}» — {m.symbol} {m.letter} / {m.name}"
                    if m.after:
                        bit += f"\n  ابتدا از: «{m.after}»"
                    bit += f"\n  {m.rule}"
                    lines.append(bit)
            else:
                lines.append("علامت میانی ندارد. رأس آیه را جدا در نظر بگیر. اگر نفس نرسید بهترین نقطهٔ معنایی را بگو.")
            lines.append("")
        if pack.kind in {"verse", "range"} and len(pack.verses) <= 3:
            lines.append("## تطبیق با مصحف محشی")
            for v in pack.verses:
                lines.append(alignment_card(v))
                lines.append("")

    if pack.neighbors:
        lines.append("## آیه قبل و بعد")
        for v in pack.neighbors:
            lines.append(f"- {v.surah}:{v.ayah} {v.text}")
        lines.append("")

    if pack.jadval:
        lines.append("## جدول مصحف محشی (حسینی)")
        for row in pack.jadval:
            lines.append(jadval.format_row(row))
            chk = jadval.verify_row(row)
            if not chk["ok"]:
                bad = [h["phrase"] for h in chk["hits"] if h["ok"] is False]
                lines.append("  (عبارت در آیه پیدا نشد: " + "، ".join(bad) + ")")
            lines.append("")

    if pack.notes:
        lines.append("## یادداشت موجود در ریپو")
        for path, text in pack.notes:
            lines.append(f"### {path}")
            lines.append(text.strip())
            lines.append("")

    if pack.docs:
        lines.append("## از docs/")
        for doc in pack.docs:
            lines.append(f"### {doc.title}  ({doc.path})")
            lines.append(doc.snippet)
            lines.append("")

    lines.append("## قالب جواب")
    lines.append("۱) دلیل وقف  ۲) دلیل وصل  ۳) دلیل ابتدا  ۴) حالات اشتباه")
    lines.append("سؤال را در ریپو ذخیره نکن. فقط از همین زمینه جواب بده.")
    return "\n".join(lines).strip() + "\n"
