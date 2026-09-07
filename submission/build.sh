#!/usr/bin/env bash
set -euo pipefail

PAP_REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PAP_ARTIFACT_RUNTIME="${PAP_ARTIFACT_RUNTIME:-$HOME/.cache/codex-runtimes/codex-primary-runtime}"
RUNTIME_NODE="$PAP_ARTIFACT_RUNTIME/dependencies/node/bin/node"
RUNTIME_PYTHON="$PAP_ARTIFACT_RUNTIME/dependencies/python/bin/python"
RUNTIME_NODE_MODULES="$PAP_ARTIFACT_RUNTIME/dependencies/node/node_modules"
RUNTIME_BIN_DIR="$PAP_ARTIFACT_RUNTIME/dependencies/bin/override"
PAP_SKILLS="$PAP_ARTIFACT_RUNTIME/plugins/openai-primary-runtime/plugins"
PAP_PRESENTATIONS_SKILL="$PAP_SKILLS/presentations/skills/presentations"
PAP_DOCUMENTS_SKILL="$PAP_SKILLS/documents/skills/documents"
PAP_PDF_SKILL="$PAP_SKILLS/pdf/skills/pdf"
for binary in "$RUNTIME_NODE" "$RUNTIME_PYTHON" "$RUNTIME_BIN_DIR/soffice"; do
  test -x "$binary" || { echo "Missing bundled runtime: $binary" >&2; exit 1; }
done

PAP_SUBMISSION_SRC="$PAP_REPO_ROOT/submission"
PAP_STAMP="$(date -u +%Y%m%d_%H%M%S)"
PAP_SUBMISSION_BUILD="$PAP_REPO_ROOT/.cache/capstone-build/$PAP_STAMP"
PAP_SUBMISSION_OUT="$PAP_REPO_ROOT/output/capstone/$PAP_STAMP"
mkdir -p "$PAP_REPO_ROOT/.cache/capstone-build" "$PAP_REPO_ROOT/output/capstone"
mkdir "$PAP_SUBMISSION_BUILD" "$PAP_SUBMISSION_OUT"
export PAP_REPO_ROOT PAP_SUBMISSION_SRC PAP_SUBMISSION_OUT PAP_SUBMISSION_BUILD
export RUNTIME_NODE RUNTIME_PYTHON RUNTIME_NODE_MODULES RUNTIME_BIN_DIR PAP_PRESENTATIONS_SKILL
export PATH="$RUNTIME_BIN_DIR:$PATH"

# A caller that has already announced this artifact operation can skip these markers.
if [[ "${PAP_ARTIFACT_MARKERS_DONE:-0}" != 1 ]]; then
  "$RUNTIME_NODE" "$PAP_DOCUMENTS_SKILL/container_tools/mark_artifact_operation_started.mjs" --operation-kind create --expected-output-count 4 --output-format docx
  "$RUNTIME_NODE" "$PAP_PRESENTATIONS_SKILL/container_tools/mark_artifact_operation_started.mjs" --operation-kind create --expected-output-count 2 --output-format pptx
  "$RUNTIME_NODE" "$PAP_PDF_SKILL/container_tools/mark_artifact_operation_started.mjs" --operation-kind create --expected-output-count 3 --output-format pdf
fi

"$RUNTIME_PYTHON" "$PAP_SUBMISSION_SRC/build_documents.py"
cp "$PAP_SUBMISSION_SRC/build_slides.mjs" "$PAP_SUBMISSION_BUILD/build_slides.mjs"
ln -s "$RUNTIME_NODE_MODULES" "$PAP_SUBMISSION_BUILD/node_modules"
"$RUNTIME_NODE" "$PAP_SUBMISSION_BUILD/build_slides.mjs"

for name in DragonWings_Final_Report DragonWings_Presentation_Plan_and_Script DragonWings_Video_Link_Submission DragonWings_Faculty_Showcase_Preparation; do
  "$RUNTIME_PYTHON" "$PAP_DOCUMENTS_SKILL/render_docx.py" "$PAP_SUBMISSION_OUT/$name.docx" --output_dir "$PAP_SUBMISSION_BUILD/$name" --dpi 110 --emit_pdf
done
cp "$PAP_SUBMISSION_BUILD/DragonWings_Final_Report/DragonWings_Final_Report.pdf" "$PAP_SUBMISSION_OUT/DragonWings_Final_Report.pdf"

for name in DragonWings_Final_Presentation DragonWings_90_Second_Pitch; do
  "$RUNTIME_BIN_DIR/soffice" --headless --convert-to pdf --outdir "$PAP_SUBMISSION_OUT" "$PAP_SUBMISSION_OUT/$name.pptx"
  "$RUNTIME_BIN_DIR/pdftoppm" -scale-to 1600 -png "$PAP_SUBMISSION_OUT/$name.pdf" "$PAP_SUBMISSION_BUILD/$name/pdf-slide"
done

"$RUNTIME_PYTHON" "$PAP_SUBMISSION_SRC/check_artifacts.py"
printf '%s\n' "$PAP_SUBMISSION_OUT" > "$PAP_REPO_ROOT/.cache/capstone-latest.txt"
printf 'Artifacts: %s\nReview images: %s\n' "$PAP_SUBMISSION_OUT" "$PAP_SUBMISSION_BUILD"
