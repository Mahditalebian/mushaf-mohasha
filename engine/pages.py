from __future__ import annotations

from functools import lru_cache

from .paths import PAGES_FILE


@lru_cache(maxsize=1)
def load_pages() -> dict[tuple[int, int], tuple[int, int]]:
    out: dict[tuple[int, int], tuple[int, int]] = {}
    if not PAGES_FILE.exists():
        return out
    for line in PAGES_FILE.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        s, a, page, juz = line.split("\t")
        out[(int(s), int(a))] = (int(page), int(juz))
    return out


def page_of(surah: int, ayah: int) -> tuple[int | None, int | None]:
    return load_pages().get((surah, ayah), (None, None))
