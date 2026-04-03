#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "这个脚本不会删除你的项目代码。"
echo "它只会提示你哪些运行时目录可以手动清理："
echo "  $ROOT_DIR/.venv"
echo "  $ROOT_DIR/runtime"
echo "  $ROOT_DIR/data"
echo "  $ROOT_DIR/agents.json"
echo ""
echo "如果你确定要删除，请手动执行对应命令。"
