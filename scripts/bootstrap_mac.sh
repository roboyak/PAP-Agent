#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
make setup db-up migrate seed memory-index
echo "Ready to start: make run"
