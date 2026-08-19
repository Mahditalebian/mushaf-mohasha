"""تحلیل «کجا نباید وقف کرد» — کلمه‌به‌کلمه در خود آیه.

قواعد لفظی آشکار متن عثمانی بررسی می‌شوند:

- حرف جر بدون مجرور («فِی»، «مِن»، «عَلَى»، «إِلَى»...)
- مضاف بدون مضاف‌الیه (کلمه‌ای با کسرهٔ بی‌تنوین که اسم معرفهٔ بعدش مال اوست)
- موصول بدون صله («ٱلَّذِی»، «ٱلَّتِی»، «ٱلَّذِینَ»...)
- فعل قول بدون مقول («قَالَ»، «قُلْ»، «يَقُولُونَ»...)
- ادات شرط بدون جزا («إِن»، «لَو»، «لَوْلَا»، «إِذَا»...)
- نفی بدون منفی («لَا»، «مَا»، «لَمْ»، «لَنْ») و اسم «لا» نافیهٔ جنس قبل از «إلا»
- ادات استثنا بدون مستثنی و جدا کردن مستثنی‌منه از «إلا»
- حرف عطف تنها («ثُمَّ»، «بَلْ»، «أَوْ»...)
- ظرف «إِذْ» بدون جمله‌اش

علاوه بر آن علامت‌های چاپی: ممنوع (ۙ) صریح «نایست»، صلی (ۖ) و معانقه (ۛ)
احتیاطی‌اند. اگر مصحف علامت لازم/قلی/جایز گذاشته باشد، آن حکم را محترم
می‌شماریم و چیزی نمی‌گوییم.
"""

from __future__ import annotations

import re

from . import quran
from .jadval import _norm_ar
from .models import MARKS

_IGNORE = set(MARKS) | {"۞", "۩"}

_PREPS = {"من", "فی", "علی", "الی", "عن", "حتی", "منذ", "مذ", "ب", "ل", "ک"}
_INNA = {"ان", "فان", "وان", "انما", "لعل", "لیت", "لکن", "کان"}
_SHART = {
    "لو", "لولا", "لوما", "اذا", "کلما", "متی",
    "اینما", "این", "حیثما", "کیفما", "مهما", "لین",
}
_IDH = {"اذ", "واذ", "فاذ", "اذما", "واذما"}
_REL = {
    "الذی", "التی", "الذین", "اللذین", "اللذان", "اللتان",
    "اللات", "اللائی", "اللاتی", "الذان", "التان", "اولو", "اولی", "اولات",
}
_QAWL = {
    "قال", "قالا", "قالوا", "قالت", "قالتا", "قلن", "قل", "قولوا", "قولا",
    "یقول", "یقولان", "یقولون", "تقول", "تقولین", "تقولان",
    "اقول", "نقول", "یقل", "تقل", "نقل",
}
_NEG = {"لا", "ما", "لم", "لن", "لیس"}
_ATF = {"و", "ف", "ثم", "بل", "او", "ام"}
_STOP_ALLOWED_MARKS = {"ۘ", "ۗ", "ۚ"}

_KASRA_END = re.compile(r"\u0650$")
_DEF_START = re.compile(r"^[ٱا]ل")


def _mk(verse, raw: str, kind: str, reason: str, mandatory: bool) -> dict:
    return {
        "surah": verse.surah,
        "ayah": verse.ayah,
        "on": raw,
        "kind": kind,
        "reason": reason,
        "severity": "ممنوع" if mandatory else "احتیاط",
    }


def forbidden_stops(verse) -> list[dict]:
    """فهرست کلمه‌هایی از همین آیه که نباید روی آن‌ها وقف کرد."""
    toks = verse.text.split()
    words: list[tuple[str, str | None]] = []
    for t in toks:
        if t in MARKS:
            if words:
                words[-1] = (words[-1][0], t)
            continue
        words.append((t, None))

    out: list[dict] = []
    last = len(words) - 1
    for i, (raw, mark) in enumerate(words):
        if i >= last:
            break  # رأس آیه محل وقف است؛ تحلیل نمی‌کنیم
        if mark in _STOP_ALLOWED_MARKS:
            continue  # چاپ مصحف اجازه/لزوم وقف داده

        if mark == "ۙ":
            out.append(
                _mk(
                    verse,
                    raw,
                    "علامت ممنوع",
                    "علامت چاپی ممنوع (لا): وقف اینجا معنا را ناقص یا فاسد می‌کند.",
                    True,
                )
            )
            continue

        nxt = words[i + 1][0]
        prev = words[i - 1][0] if i > 0 else ""
        n = _norm_ar(raw)
        nn = _norm_ar(nxt)
        np_ = _norm_ar(prev)
        if not n:
            continue

        reasons: list[tuple[str, str, bool]] = []

        if mark == "ۖ":
            reasons.append(
                ("علامت وصل اولی", "علامت صلی: وصل اولی است؛ وقف اینجا جایز ولی مرجوح.", False)
            )
        if mark == "ۛ":
            reasons.append(
                ("معانقه", "معانقه: فقط روی یکی از دو نقطه بایست؛ روی هر دو نه.", False)
            )

        naji = np_ == "لا" and nn == "الا"
        if naji:
            reasons.append(
                (
                    "نفی جنس",
                    "اسم «لا» نافیهٔ جنس بدون خبر؛ تا «إلا…» نرسیده نایست "
                    "(مثل «لا إله إلا الله»).",
                    True,
                )
            )

        if n in _PREPS:
            if n == "من":
                reasons.append(
                    ("حرف جر / موصول", "«من» بدون مجرور یا صله؛ جمله ناتمام می‌ماند.", True)
                )
            else:
                reasons.append(
                    ("حرف جر", f"حرف جر «{raw}» بدون مجرور؛ شنونده منتظر اسم مجرور می‌ماند.", True)
                )

        if n in _INNA:
            if n in {"ان", "فان", "وان", "انما"}:
                reasons.append(
                    (
                        "ادات ناصبه/مشبهه",
                        "پس از «أن/إن» نایست: فعل ناصبه یا جزای شرط، یا اسم و خبر، "
                        "ناتمام می‌ماند.",
                        True,
                    )
                )
            else:
                reasons.append(("حرف مشبهه", f"حرف مشبهه «{raw}» بدون اسم و خبر.", True))
        elif n in _SHART:
            reasons.append(
                ("ادات شرط", f"ادات شرط «{raw}» بدون جزا (و جواب قسم).", True)
            )
        elif n in _IDH:
            reasons.append(
                ("ظرف إذ", "ظرف «إذ» بدون جمله‌ای که به آن اضافه شود.", True)
            )

        if n in _REL:
            reasons.append(
                ("موصول و صله", f"موصول «{raw}» بدون صله؛ صله برای تمام شدن معنا لازم است.", True)
            )
        if n in _QAWL:
            reasons.append(
                ("قول و مقول", f"فعل قول «{raw}» بدون مقول؛ گوینده را از سخنش جدا می‌کند.", True)
            )
        if n in _NEG and not naji:
            if n == "لا":
                reasons.append(("نفی/نهی", "ادات نفی/نهی «لا» بدون منفی یا فعل.", True))
            elif n in {"لم", "لن"}:
                reasons.append(("جزم/نصب", f"حرف جزم/نصب «{raw}» بدون فعل.", True))
            elif n == "ما":
                reasons.append(("نفی/موصول", "«ما» نافیه یا موصوله بدون منفی/صله.", True))
            elif n == "لیس":
                reasons.append(("فعل ناقص", "فعل ناقص «لیس» بدون اسم و خبر.", True))

        if n == "الا":
            reasons.append(("استثنا", "ادات استثنا «إلا» بدون مستثنی.", True))
        elif nn == "الا" and not naji:
            reasons.append(
                (
                    "استثنا",
                    "مستثنی‌منه را از «إلا» جدا نکن؛ استثنا به همین برمی‌گردد.",
                    False,
                )
            )

        if n in _ATF:
            reasons.append(("عطف", f"حرف عطف «{raw}» بدون معطوف.", True))

        if (
            _KASRA_END.search(raw)
            and not n.startswith("ال")
            and n not in _PREPS | _INNA
            and _DEF_START.search(nxt)
        ):
            reasons.append(
                (
                    "مضاف و مضاف‌الیه",
                    f"مضاف «{raw}» بدون مضاف‌الیه؛ رابطهٔ اضافه ناقص می‌ماند.",
                    True,
                )
            )

        if not reasons:
            continue

        seen: set[str] = set()
        merged: list[tuple[str, str, bool]] = []
        for kind, reason, mandatory in reasons:
            if kind in seen:
                continue
            seen.add(kind)
            merged.append((kind, reason, mandatory))

        out.append(
            _mk(
                verse,
                raw,
                "، ".join(k for k, _, _ in merged),
                " ".join(r for _, r, _ in merged),
                any(m for _, _, m in merged),
            )
        )
    return out


def nahy_for(surah: int, ayah: int) -> list[dict]:
    v = quran.make_verse(surah, ayah)
    if v is None:
        return []
    return forbidden_stops(v)


def format_nahy(items: list[dict]) -> str:
    if not items:
        return "موضع ممنوعی در تحلیل پیدا نشد (رأس آیه که سنت است)."
    head = items[0]
    lines = [f"## کجا در این آیه نباید وقف کرد — {head['surah']}:{head['ayah']}"]
    for h in items:
        lines.append(
            f"- [{h['severity']}] روی «{h['on']}» نایست — {h['kind']} — {h['reason']}"
        )
    return "\n".join(lines)


def nahy_cli(argv: list[str]) -> int:
    import sys

    from .parse import parse_query

    if not argv:
        print("استفاده: python3 -m engine nahy «بقره ۲۵۸»", file=sys.stderr)
        return 2
    parsed = parse_query(" ".join(argv))
    if parsed.kind not in {"verse", "range"} or not parsed.surah:
        print("برای تحلیل «نایست» آیه را با شماره بپرس؛ مثلاً: بقره ۲۵۸", file=sys.stderr)
        return 2
    for ayah in range(parsed.start or 1, (parsed.end or parsed.start or 1) + 1):
        items = nahy_for(parsed.surah, ayah)
        print(format_nahy(items))
        print()
    return 0
