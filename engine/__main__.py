from __future__ import annotations

import sys

from .ask import ask, format_pack


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in {"serve", "web", "html"}:
        from .server import main as serve

        return serve(args[1:])
    if not args:
        print("استفاده:", file=sys.stderr)
        print("  python3 -m engine «بقره ۹۱»", file=sys.stderr)
        print("  python3 -m engine serve", file=sys.stderr)
        return 2
    question = " ".join(args)
    print(format_pack(ask(question)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
