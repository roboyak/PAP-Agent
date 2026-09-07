#!/usr/bin/env bash
set -euo pipefail

echo "== Branch =="
git branch --show-current

echo "== Working tree =="
git status --short

echo "== Automated verification =="
make verify

cat <<'EOF'

Automated verification completed.

NEXT — HUMAN IN THE LOOP:
1. Use the PR-specific HIL commands in the PR description.
2. Review the branch diff.
3. Complete HUMAN-ONLY signoff yourself.
4. Only then open/review/merge the PR.

This script does NOT authorize merge.
EOF
