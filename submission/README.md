# Capstone submission builders

The reviewed report, decks, and supporting documents are versioned in
[`artifacts/`](artifacts/). Git history preserves earlier reviewed versions alongside
the content and scripts that produced them.

Edit `content.json`, then regenerate all deliverables:

```bash
bash submission/build.sh
```

The builder uses the installed **Codex bundled artifact runtime**. It does not install
packages, contact a model, use Docker, or alter the PAP/source databases. On a different
Codex installation, set `PAP_ARTIFACT_RUNTIME` to its `codex-primary-runtime` directory.
Application setup in the repository README is independent of these document tools.

Each run writes a new UTC-stamped directory under `output/capstone/` and puts private
validation receipts and PNG previews under `.cache/capstone-build/`. The latest successful
directory is recorded in `.cache/capstone-latest.txt`. Existing outputs are preserved.

`content.json` holds report sections, shared numeric facts, slide copy, timings, notes,
and evidence links. `build_documents.py` creates DOCX files. `build_slides.mjs` creates
native editable PowerPoint text, diagrams, and tables using `@oai/artifact-tool`.
The bundled renderer exports PDF/PNG files and high-resolution slides. The PowerPoint
files retain editable text, diagrams, and tables. `check_artifacts.py` checks the report
word count, required sections, slide counts, matching narration, durations, and unresolved variables.
The fixed slide layouts intentionally support this capstone's 10-slide presentation and
3-slide pitch. Change the corresponding layout function when adding a new slide kind.

After every change, inspect **every** rendered document page and slide. Text changes can
alter line wrapping even when automated checks pass. The scripts do not claim visual QA.

After reviewing a successful build, update the versioned files:

```bash
cp "$(cat .cache/capstone-latest.txt)"/* submission/artifacts/
git diff --stat
```

Commit the reviewed artifacts together with their changed content and scripts. Temporary
builds and QA previews remain ignored so the repository contains the selected version.

## Before Canvas submission

- Record the main 8–10 minute presentation and test its audio and playback.
- Set `video_url` to the accessible hosted recording link and regenerate.
- If recording the optional pitch, set `optional_pitch_url` and regenerate.
- Make the repository public, as the owner has planned, and verify signed-out access.
- Compare the files with the official Checkpoint 7.1 templates when those are available.
  The current organization follows the supplied rubric and earlier report sections.
- Upload the report and completed video-link document. The empty-link version is a
  preparation document, not a complete video submission.

## Evidence and assets

Implementation claims are anchored to commit `74cc759` and the cited PR records. Update
the evidence deliberately after new measurements. A single real outcome comparison or
agent pair is not an accuracy rate. Weather remains synthetic and the live equipment cap
is unconfigured. The repository visibility and recording state are not inferred by builders.

`assets/pap-console.png` is the actual September 7 local Playwright screenshot.
`assets/blueprint.png` is a conceptual illustration made with the built-in image tool.
Its prompt requested a dark navy, text-free technical blueprint, cyan traces, muted amber
details, generic solar panels and an unbranded portable battery on the right, and open
space on the left. It contains no equipment ratings and is not a picture of real hardware.
The user's supplied PDF, PowerPoint, and video guide the visual style, not implementation
claims. Sources and design credits are recorded in slide notes.
