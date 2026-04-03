#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "RegentOS dev quick start"
echo "1. API:       bash scripts/run_api.sh"
echo "2. Dashboard: bash scripts/run_dashboard.sh"
echo "3. Seed data: source .venv/bin/activate && python scripts/seed_demo_data.py"
echo "4. Frontend dev: cd apps/dashboard && npm install && VITE_API_BASE=http://127.0.0.1:8000 npm run dev -- --host 0.0.0.0 --port 7891"
