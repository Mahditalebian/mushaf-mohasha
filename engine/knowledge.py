from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .models import DocHit
from .normalize import fold
from .paths import AYAT_DIR, DOCS_DIR
from . import surahs


@lru_cache(maxsize=1)
def load_docs() -> list[tuple[Path, str, str]]:
    docs = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = path.stem
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        docs.append((path, title, text))
    return docs


def protocol_text() -> str:
    p = DOCS_DIR / "03-protocol.md"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def existing_note(surah: int, ayah: int) -> tuple[str, str] | None:
    folder = AYAT_DIR / surahs.SLUGS[surah]
    path = folder / f"{ayah:03d}.md"
    if path.exists():
        return str(path.relative_to(AYAT_DIR.parent)), path.read_text(encoding="utf-8")
    return None


_TOKEN = re.compile(r"[0-9A-Za-zآ-یءئؤإأآة]+")


def _tokens(text: str) -> set[str]:
    return {fold(t) for t in _TOKEN.findall(text) if len(fold(t)) > 1}


def search_docs(query: str, extra_terms: list[str] | None = None, limit: int = 4) -> list[DocHit]:
    terms = _tokens(query)
    if extra_terms:
        terms |= {fold(t) for t in extra_terms if t}
    if not terms:
        return []
    hits: list[DocHit] = []
    for path, title, text in load_docs():
        blocks = _blocks(text)
        best: DocHit | None = None
        for block in blocks:
            score = _score(terms, title + "\n" + block)
            if score <= 0:
                continue
            cand = DocHit(
                path=str(path.relative_to(path.parents[1])),
                title=title,
                snippet=_clip(block),
                score=score,
            )
            if best is None or cand.score > best.score:
                best = cand
        if best:
            hits.append(best)
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]


def _blocks(text: str) -> list[str]:
    parts = re.split(r"\n(?=## )", text)
    return [p.strip() for p in parts if p.strip()]


def _score(terms: set[str], block: str) -> float:
    bag = _tokens(block)
    if not bag:
        return 0.0
    inter = terms & bag
    if not inter:
        return 0.0
    return len(inter) + (0.3 * len(inter) / max(len(terms), 1))


def _clip(text: str, n: int = 700) -> str:
    t = text.strip()
    if len(t) <= n:
        return t
    return t[: n - 1].rsplit(" ", 1)[0] + "…"
