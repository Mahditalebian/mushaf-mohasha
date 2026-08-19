"""سرور محلی HTML برای موتور.

    python3 -m engine serve
    بعد در مرورگر: http://127.0.0.1:8765
"""

from __future__ import annotations

import argparse
import json
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .ask import ask
from .paths import WEB_DIR
from .check import verify

WEB = WEB_DIR
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8765


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print("[web]", self.address_string(), fmt % args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_file(WEB / "index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/api/ask":
            self._api_ask(parsed)
            return
        if parsed.path == "/api/health":
            self._health()
            return
        super().do_GET()

    def _api_ask(self, parsed) -> None:
        qs = parse_qs(parsed.query)
        raw = (qs.get("q") or [""])[0]
        question = unquote(raw).strip()
        if not question:
            self._json(400, {"error": "پرسش خالی است. مثلاً: آل عمران 156"})
            return
        try:
            pack = ask(question)
            self._json(200, pack.to_dict())
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"error": str(exc)})

    def _health(self) -> None:
        report = verify()
        self._json(
            200 if report.ok else 503,
            {"ok": report.ok, "lines": report.lines},
        )

    def _send_file(self, path: Path, ctype: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="سرور محلی مصحف محشی")
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--open", action="store_true", help="مرورگر را باز کن")
    p.add_argument("--skip-check", action="store_true")
    args = p.parse_args(argv)
    if not (WEB / "index.html").exists():
        raise SystemExit(f"فایل HTML نیست: {WEB / 'index.html'}")
    if not args.skip_check:
        report = verify()
        if not report.ok:
            print("داده ناقص است. اول این را بزن: python3 -m engine check")
            for line in report.lines:
                print(line)
            return 1
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"موتور محلی آماده است:  {url}", flush=True)
    print("توقف: Ctrl+C", flush=True)
    print("سؤال در ریپو ذخیره نمی‌شود.", flush=True)
    if args.open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nایستاد.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
