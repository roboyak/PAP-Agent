# Completed official 7.1 planning template

[Open the September 8 version](2026-09-08_DragonWings_7.1_Capstone_Planning.pdf).
It fills all ten answers in the supplied six-page template, with 1,082 words and editable
fields. Implementation claims describe commit `1a7a7ee`, including stored weather,
five-wing replay, provider selection, the Inspector and calibration maintenance.
The original [blank template](7.1_Capstone_Planning_Template.pdf) is preserved.

Edit [planning_template_content.json](planning_template_content.json), then choose a new
output filename. On the existing Codex installation, from the repository root:

```bash
PAP_PDF_PYTHON="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python"
"$PAP_PDF_PYTHON" submission/fill_planning_template.py \
  --output submission/2026-09-08_DragonWings_7.1_Capstone_Planning_v3.pdf
open submission/2026-09-08_DragonWings_7.1_Capstone_Planning_v3.pdf
```

The builder needs Python, `pypdf==6.10.0` and `reportlab==4.4.9` (versions used here).
On another installation, `uv run --no-project --with pypdf==6.10.0 --with reportlab==4.4.9
python submission/fill_planning_template.py --output /path/to/new.pdf` supplies those
dependencies without changing the app environment. This may download packages.

The builder checks all canonical field values, widget values and appearance streams.
It wraps at 11 points with padding and rejects text that does not fit. An existing output
path is refused; shorten an overlong answer or choose a new filename and rerun. It does
not query the source database or update any application records.

After regeneration, inspect all six pages in a PDF viewer, including the last line of each
answer. For PNG review with Poppler: `pdftoppm -scale-to 1500 -png /path/to/new.pdf /tmp/pap-planning`.
Field checks and text-size checks do not replace visual review.

This is the current completed planning template. The earlier report, decks and recording
scripts retain their earlier content until separately refreshed; `build.sh` does not rebuild
this new template. Repository visibility is still private, as requested. Before submission,
make it public and verify access, then update that status in the answers. The required
narrated presentation and accessible video link remain separate deliverables.
