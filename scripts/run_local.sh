#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
make db-up migrate seed
exec uv run --locked uvicorn pap_agent.main:app --host 127.0.0.1 --port "${PAP_PORT:-8000}"
