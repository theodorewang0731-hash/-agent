#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "=========================================="
echo "RegentOS 安装向导"
echo "治理型多智能体系统原型"
echo "=========================================="
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "未找到 python3，请先安装 Python 3.11+"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "未找到 npm，请先安装 Node.js 18+"
  exit 1
fi

if [ ! -d "$ROOT_DIR/.venv" ]; then
  python3 -m venv "$ROOT_DIR/.venv"
fi

source "$ROOT_DIR/.venv/bin/activate"
pip install -r "$ROOT_DIR/requirements.txt"
python "$ROOT_DIR/scripts/init_runtime.py"
python "$ROOT_DIR/scripts/export_agent_manifest.py"
python "$ROOT_DIR/scripts/seed_demo_data.py"

cd "$ROOT_DIR/apps/dashboard"
npm install
npm run build
cd "$ROOT_DIR"

chmod +x "$ROOT_DIR/scripts/run_api.sh" "$ROOT_DIR/scripts/run_dashboard.sh" "$ROOT_DIR/scripts/run_dev.sh"

echo ""
echo "安装完成。"
echo "下一步："
echo "  1. 启动 API:       bash scripts/run_api.sh"
echo "  2. 启动 Dashboard: bash scripts/run_dashboard.sh"
echo "  3. 打开文档:       docs/getting-started.md"
