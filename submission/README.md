# Capstone submission builders

The reviewed report, decks, and supporting documents are versioned in
[`artifacts/`](artifacts/). Git history preserves earlier reviewed versions alongside
the content and scripts that produced them.

| Review item | Versioned files |
| --- | --- |
| Final report | [PDF](artifacts/DragonWings_Final_Report.pdf), [DOCX](artifacts/DragonWings_Final_Report.docx) |
| Main presentation | [PowerPoint](artifacts/DragonWings_Final_Presentation.pptx), [PDF](artifacts/DragonWings_Final_Presentation.pdf) |
| 90-second pitch | [PowerPoint](artifacts/DragonWings_90_Second_Pitch.pptx), [PDF](artifacts/DragonWings_90_Second_Pitch.pdf) |
| Speaking preparation | [Main script](artifacts/DragonWings_Presentation_Plan_and_Script.docx), [faculty Q&A](artifacts/DragonWings_Faculty_Showcase_Preparation.docx) |
| App walkthroughs | [2:30 MP4](artifacts/DragonWings_App_Walkthrough_short.mp4), [9:00 MP4](artifacts/DragonWings_App_Walkthrough_full.mp4), [narration guide](artifacts/Narration_Guide.md) |
| Video submission | [Link document](artifacts/DragonWings_Video_Link_Submission.docx), awaiting hosted URLs |

The app walkthroughs are silent browser recordings. Add your narration before using them
as a presentation submission. The 2:30 app walkthrough is separate from the 90-second pitch.

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

Implementation claims are anchored to commit `aa61ba7` and the cited PR records. Update
the evidence deliberately after new measurements. A single real outcome comparison or
agent pair is not an accuracy rate. Weather remains synthetic and the live equipment cap
is unconfigured. The repository visibility and recording state are not inferred by builders.

`assets/pap-console.png` is the September 7 Playwright view of the saved sunny-fixture
run with four actual Ollama calls.
`assets/blueprint.png` is a conceptual illustration made with the built-in image tool.
Its prompt requested a dark navy, text-free technical blueprint, cyan traces, muted amber
details, generic solar panels and an unbranded portable battery on the right, and open
space on the left. It contains no equipment ratings and is not a picture of real hardware.
The user's supplied PDF, PowerPoint, and video guide the visual style, not implementation
claims. Sources and design credits are recorded in slide notes.

## App recordings

`scripts/record_demo.py` records actual browser use in two versions: 2:30 and 9:00.
They are silent, ready for your narration. Chapter captions are recording annotations;
the application results and interactions are real. `recording_chapters.json` contains the
editable captions plus short and full narration guides.

Requires the repository's Playwright installation and command-line `ffmpeg`/`ffprobe`.
Start the app with `PAP_PROFILE=macmini-replay make run`, use the sunny fixture, and complete
a published selective Ollama run with successful generator and critic records
(Evaluate cloudy demo can trigger selective reasoning).
Use the selected-run UUID shown by the UI:

```bash
uv run --locked python scripts/record_demo.py --episode YOUR_COMPLETED_RUN_UUID --version both
```

The recorder verifies sunny-fixture data, a published selective run, and successful Ollama roles.
Two independent browser contexts inspect that saved run and perform manual memory searches
and numerical previews; they do not generate new agent responses or evaluate/index new outcomes.
Manual search uses the local embedding model. Health checks the current service independently.
Recordings, narration guides and duration receipts go to a fresh `output/recordings/` directory.
Use `--url` for another local service port or `--version short` / `--version full` for one cut.
After inspecting playback and chapter screenshots, copy the selected MP4s and narration guide
into `submission/artifacts/` and commit them. Add narration, host the video, and update the
submission document's real URL before Canvas submission.
