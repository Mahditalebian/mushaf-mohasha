from __future__ import annotations

from dataclasses import dataclass, field


MARKS = {
    "ۘ": {
        "letter": "م",
        "name": "لازم",
        "rule": "وصل دو طرف معنا را عوض یا فاسد می‌کند. باید ایستاد.",
    },
    "ۙ": {
        "letter": "لا",
        "name": "ممنوع",
        "rule": "وقف معنا را ناقص یا فاسد می‌کند. وصل کن. اگر اضطراری ایستادی اعاده کن.",
    },
    "ۗ": {
        "letter": "قلی",
        "name": "وقف اولی",
        "rule": "معنا اینجا بهتر تمام می‌شود. وقف بهتر است؛ وصل هم جایز است.",
    },
    "ۖ": {
        "letter": "صلی",
        "name": "وصل اولی",
        "rule": "پیوستگی معنا قوی‌تر است. وصل بهتر است؛ وقف هم جایز است.",
    },
    "ۚ": {
        "letter": "ج",
        "name": "جایز",
        "rule": "وقف و وصل نزدیک به هم است.",
    },
    "ۛ": {
        "letter": "معانقه",
        "name": "معانقه",
        "rule": "دو جا نزدیک هم؛ فقط روی یکی بایست.",
    },
    "ۜ": {
        "letter": "س",
        "name": "سکت",
        "rule": "قطع کوتاه صدا بدون نفس تازه.",
    },
}


@dataclass
class MarkHit:
    symbol: str
    letter: str
    name: str
    rule: str
    before: str
    after: str


@dataclass
class Verse:
    surah: int
    ayah: int
    surah_name: str
    text: str
    marks: list[MarkHit] = field(default_factory=list)


@dataclass
class DocHit:
    path: str
    title: str
    snippet: str
    score: float


@dataclass
class ContextPack:
    query: str
    kind: str
    verses: list[Verse] = field(default_factory=list)
    neighbors: list[Verse] = field(default_factory=list)
    notes: list[tuple[str, str]] = field(default_factory=list)
    docs: list[DocHit] = field(default_factory=list)
    protocol: str = ""
    warnings: list[str] = field(default_factory=list)
