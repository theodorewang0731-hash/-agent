#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v npm >/dev/null 2>&1; then
  echo "未找到 npm，请先安装 Node.js 18+"
  exit 1
fi

if [ ! -d "$ROOT_DIR/.venv" ]; then
  python3 -m venv "$ROOT_DIR/.venv"
fi

cd "$ROOT_DIR/apps/dashboard"
npm install
npm run build
cd "$ROOT_DIR"

source "$ROOT_DIR/.venv/bin/activate"
python "$ROOT_DIR/apps/dashboard/server.py" --host 0.0.0.0 --port 7891 --api-base "http://127.0.0.1:8000"
