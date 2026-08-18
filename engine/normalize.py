from __future__ import annotations

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

ARABIC_DIACRITICS = dict.fromkeys(map(ord, "ًٌٍَُِّْٰٕٖٜٓٔٗ٘ٙٚٛٝٞ"), None)


def to_ascii_digits(text: str) -> str:
    return text.translate(FA_DIGITS)


def collapse(text: str) -> str:
    return " ".join(text.replace("‌", " ").split())


def fold_arabic(text: str) -> str:
    t = text.translate(ARABIC_DIACRITICS)
    return (
        t.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ٱ", "ا")
        .replace("ة", "ه")
        .replace("ى", "ی")
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("ؤ", "و")
        .replace("ئ", "ی")
    )


def fold(text: str) -> str:
    return fold_arabic(collapse(to_ascii_digits(text))).casefold()
