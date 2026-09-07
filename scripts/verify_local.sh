#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
make verify
PAP_PROFILE=test EMBEDDING_BACKEND=test AGENT_BACKEND=test uv run --locked python -m pap_agent.demo
