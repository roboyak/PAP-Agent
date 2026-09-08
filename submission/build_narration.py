"""Regenerate the timed, per-clip reading script from narration.json."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def clock(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02}"


def main():
    plan = json.loads((ROOT / "narration.json").read_text())
    clips = plan["clips"]
    total = sum(clip["seconds"] for clip in clips)
    words = sum(
        len(re.findall(r"\S+", beat["narration"])) for clip in clips for beat in clip["beats"]
    )
    assert 480 <= total <= 600
    assert len({clip["stem"] for clip in clips}) == len(clips)
    lines = [
        f"# {plan['title']}",
        "",
        f"Target: **{clock(total)} total**, including slides, both demos and brief screen actions.",
        f"**{words} spoken words**; approximately {words / plan['target_wpm']:.1f} minutes "
        f"at {plan['target_wpm']} words/minute before clicks and pauses. Rehearse once.",
        "",
        "## Before recording",
        "",
        *[f"- {item}" for item in plan["setup"]],
        "",
        "## Recording order",
        "",
        "| Clip filename | Target | Finished-video position |",
        "| --- | ---: | --- |",
    ]
    elapsed = 0
    for clip in clips:
        end = elapsed + clip["seconds"]
        lines.append(
            f"| {clip['stem']}.mov | {clock(clip['seconds'])} | {clock(elapsed)}–{clock(end)} |"
        )
        elapsed = end
    elapsed = 0
    for clip in clips:
        end = elapsed + clip["seconds"]
        lines.extend(
            [
                "",
                f"## {clip['title']}",
                "",
                f"**{clip['stem']}.mov · {clock(clip['seconds'])} · "
                f"{clock(elapsed)}–{clock(end)}**",
            ]
        )
        for beat in clip["beats"]:
            lines.extend(["", f"*Action: {beat['action']}*", "", beat["narration"]])
        elapsed = end
    lines.extend(
        [
            "",
            "## Join the recordings",
            "",
            "Put the twelve numbered MOV or MP4 files in one folder. Give the folder path to "
            "Codex for trimming and assembly, or use:",
            "",
            "```bash",
            "uv run python scripts/assemble_presentation.py --clips /path/to/your/clips",
            "```",
            "",
            "The command creates a new MP4 and timing receipt under output/recordings/. "
            "Original clips stay unchanged. Review the full result for audible narration, "
            "readable screens, clean cuts and an 8–10-minute duration before hosting it.",
            "",
            "Edit submission/narration.json and run `uv run python submission/build_narration.py` "
            "to regenerate this reading copy. Per-clip trim_start/trim_end are seconds removed "
            "from the beginning/end, only when deliberately configured after review.",
            "",
        ]
    )
    output = ROOT / "artifacts/DragonWings_9_Minute_Recording_Script.md"
    output.write_text("\n".join(lines))
    print(f"{output}: {len(clips)} clips, {words} words, target {clock(total)}")


if __name__ == "__main__":
    main()
