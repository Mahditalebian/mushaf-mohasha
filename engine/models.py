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

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "letter": self.letter,
            "name": self.name,
            "rule": self.rule,
            "waqf_on": self.before,
            "ibtida_from": self.after,
        }


@dataclass
class Verse:
    surah: int
    ayah: int
    surah_name: str
    text: str
    marks: list[MarkHit] = field(default_factory=list)

    def to_dict(self) -> dict:
        from .pages import page_of

        page, juz = page_of(self.surah, self.ayah)
        return {
            "surah": self.surah,
            "ayah": self.ayah,
            "surah_name": self.surah_name,
            "text": self.text,
            "page": page,
            "juz": juz,
            "marks": [m.to_dict() for m in self.marks],
        }


@dataclass
class DocHit:
    path: str
    title: str
    snippet: str
    score: float

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "title": self.title,
            "snippet": self.snippet,
            "score": self.score,
        }


@dataclass
class ContextPack:
    query: str
    kind: str
    verses: list[Verse] = field(default_factory=list)
    neighbors: list[Verse] = field(default_factory=list)
    notes: list[tuple[str, str]] = field(default_factory=list)
    docs: list[DocHit] = field(default_factory=list)
    jadval: list[dict] = field(default_factory=list)
    best: list[dict] = field(default_factory=list)
    protocol: str = ""
    warnings: list[str] = field(default_factory=list)
    explanation: dict | None = None

    def to_dict(self) -> dict:
        cards = []
        if self.kind in {"verse", "range"} and len(self.verses) <= 5:
            from .match import alignment_card

            cards = [alignment_card(v) for v in self.verses]
        return {
            "query": self.query,
            "kind": self.kind,
            "warnings": self.warnings,
            "verses": [v.to_dict() for v in self.verses],
            "neighbors": [v.to_dict() for v in self.neighbors],
            "notes": [{"path": p, "text": t} for p, t in self.notes],
            "docs": [d.to_dict() for d in self.docs],
            "jadval": self.jadval,
            "best": self.best,
            "cards": cards,
            "explanation": self.explanation,
        }
