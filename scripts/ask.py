#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.ask import ask, format_pack  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("استفاده: python3 scripts/ask.py «بقره ۹۱»", file=sys.stderr)
        return 2
    print(format_pack(ask(" ".join(sys.argv[1:]))), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
