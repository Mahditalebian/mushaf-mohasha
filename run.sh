#!/usr/bin/env bash
# بعد از کلون: ./run.sh
set -euo pipefail
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  PY=(python3)
elif command -v python >/dev/null 2>&1; then
  PY=(python)
else
  echo "پایتون ۳ پیدا نشد. نسخهٔ ۳.۱۰ یا بالاتر را نصب کن."
  exit 1
fi

"${PY[@]}" -m engine check
exec "${PY[@]}" -m engine serve --open "$@"
