from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] in {"-h", "--help", "help"}:
        print("موتور محلی مصحف محشی", file=sys.stderr)
        print("از ریشهٔ ریپو:", file=sys.stderr)
        print("  python3 -m engine check", file=sys.stderr)
        print("  python3 -m engine serve", file=sys.stderr)
        print("  python3 -m engine «بقره ۹۱»", file=sys.stderr)
        print("  python3 -m engine serve --port 9000 --open", file=sys.stderr)
        return 0 if args else 2
    cmd = args[0]
    if cmd in {"serve", "web", "html"}:
        from .server import main as serve

        return serve(args[1:])
    if cmd in {"check", "doctor", "verify"}:
        from .check import main as check

        return check(args[1:])
    if cmd in {"best", "بهترین"}:
        from .best import best_cli

        return best_cli(args[1:])
    question = " ".join(args)
    from .ask import ask, format_pack

    print(format_pack(ask(question)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
