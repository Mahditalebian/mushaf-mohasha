from __future__ import annotations

import sys

from .ask import ask, format_pack


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("استفاده: python3 -m engine «بقره ۹۱»", file=sys.stderr)
        return 2
    question = " ".join(args)
    print(format_pack(ask(question)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
