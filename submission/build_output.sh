#!/usr/bin/env bash
set -euo pipefail
PAP_REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PAP_ARTIFACT_RUNTIME="${PAP_ARTIFACT_RUNTIME:-$HOME/.cache/codex-runtimes/codex-primary-runtime}"
RUNTIME_NODE="$PAP_ARTIFACT_RUNTIME/dependencies/node/bin/node"
RUNTIME_PYTHON="$PAP_ARTIFACT_RUNTIME/dependencies/python/bin/python"
RUNTIME_NODE_MODULES="$PAP_ARTIFACT_RUNTIME/dependencies/node/node_modules"
RUNTIME_BIN_DIR="$PAP_ARTIFACT_RUNTIME/dependencies/bin/override"
export RUNTIME_NODE_MODULES RUNTIME_BIN_DIR
export PATH="$RUNTIME_BIN_DIR:$PATH"
PAP_PRESENTATIONS_SKILL="$PAP_ARTIFACT_RUNTIME/plugins/openai-primary-runtime/plugins/presentations/skills/presentations"
PAP_PDF_SKILL="$PAP_ARTIFACT_RUNTIME/plugins/openai-primary-runtime/plugins/pdf/skills/pdf"
PAP_OUTPUT_EXAMPLE="${1:-$PAP_REPO_ROOT/submission/examples/output}"
PAP_STAMP="$(date -u +%Y%m%d_%H%M%S)"
PAP_SUBMISSION_BUILD="$PAP_REPO_ROOT/.cache/output-slides/$PAP_STAMP"
PAP_SUBMISSION_OUT="$PAP_REPO_ROOT/output/capstone/output_$PAP_STAMP"
mkdir -p "$PAP_SUBMISSION_BUILD" "$PAP_SUBMISSION_OUT"
export PAP_REPO_ROOT RUNTIME_PYTHON PAP_PRESENTATIONS_SKILL PAP_OUTPUT_EXAMPLE PAP_SUBMISSION_BUILD PAP_SUBMISSION_OUT
if [[ "${PAP_ARTIFACT_MARKERS_DONE:-0}" != 1 ]]; then
  "$RUNTIME_NODE" "$PAP_PRESENTATIONS_SKILL/container_tools/mark_artifact_operation_started.mjs" --operation-kind create --expected-output-count 1 --output-format pptx
  "$RUNTIME_NODE" "$PAP_PDF_SKILL/container_tools/mark_artifact_operation_started.mjs" --operation-kind create --expected-output-count 1 --output-format pdf
fi
cp "$PAP_REPO_ROOT/submission/build_output_slides.mjs" "$PAP_SUBMISSION_BUILD/build_output_slides.mjs"
ln -s "$PAP_ARTIFACT_RUNTIME/dependencies/node/node_modules" "$PAP_SUBMISSION_BUILD/node_modules"
cd "$PAP_SUBMISSION_BUILD"
"$RUNTIME_NODE" "$PAP_SUBMISSION_BUILD/build_output_slides.mjs"
"$PAP_ARTIFACT_RUNTIME/dependencies/bin/override/soffice" --headless --convert-to pdf --outdir "$PAP_SUBMISSION_OUT" "$PAP_SUBMISSION_OUT/DragonWings_Output_Walkthrough.pptx"
"$PAP_ARTIFACT_RUNTIME/dependencies/bin/override/pdftoppm" -scale-to 1600 -png "$PAP_SUBMISSION_OUT/DragonWings_Output_Walkthrough.pdf" "$PAP_SUBMISSION_BUILD/pdf-slide"
printf '%s\n' "$PAP_SUBMISSION_OUT" > "$PAP_REPO_ROOT/.cache/output-slides-latest.txt"
printf 'Artifacts: %s\nReview images: %s\n' "$PAP_SUBMISSION_OUT" "$PAP_SUBMISSION_BUILD"
