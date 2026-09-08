"""Join numbered narrated clips into one 1080p MP4, following submission/narration.json."""

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def probe(path: Path) -> dict:
    return json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clips", required=True, type=Path)
    parser.add_argument("--plan", type=Path, default=ROOT / "submission/narration.json")
    parser.add_argument("--output", type=Path, help="New output folder; originals stay unchanged")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    inputs, filters, labels, receipt = [], [], [], []
    for index, clip in enumerate(plan["clips"]):
        matches = [
            path.resolve()
            for path in args.clips.glob(f"{clip['stem']}.*")
            if path.suffix.lower() in {".mov", ".mp4"}
        ]
        if len(matches) != 1:
            parser.error(f"Expected one MOV or MP4 for {clip['stem']}; found {len(matches)}")
        path = matches[0]
        info = probe(path)
        if not {"video", "audio"} <= {s["codec_type"] for s in info["streams"]}:
            parser.error(f"{path.name} needs video and recorded microphone audio")
        duration = float(info["format"]["duration"])
        origin = float(info["format"].get("start_time", 0))
        start, trim_end = float(clip.get("trim_start", 0)), float(clip.get("trim_end", 0))
        end = duration - trim_end
        if not (0 <= start < end <= duration):
            parser.error(f"Invalid trim times for {path.name}")
        inputs.extend(["-i", str(path)])
        # Normalize each synchronized pair, then concatenate audio and video together.
        # https://ffmpeg.org/ffmpeg-filters.html#concat
        filters.extend(
            [
                f"[{index}:v:0]setpts=PTS-({origin})/TB,trim=start={start}:end={end},"
                f"setpts=PTS-({start})/TB,scale=1920:1080:force_original_aspect_ratio=decrease,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30:start_time=0,format=yuv420p"
                f"[v{index}]",
                f"[{index}:a:0]asetpts=PTS-({origin})/TB,atrim=start={start}:end={end},"
                f"asetpts=PTS-({start})/TB,aresample=48000:async=1:first_pts=0,"
                f"aformat=channel_layouts=stereo,apad,atrim=duration={end - start}[a{index}]",
            ]
        )
        labels.append(f"[v{index}][a{index}]")
        receipt.append(
            {
                "file": path.name,
                "source_seconds": duration,
                "trim_start": start,
                "trim_end": trim_end,
            }
        )
    filters.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=1[v][a]")
    folder = args.output or ROOT / "output/recordings" / datetime.now(UTC).strftime(
        "presentation_%Y%m%d_%H%M%S"
    )
    folder.mkdir(parents=True)
    output = folder / "DragonWings_Narrated_Presentation.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-copyts",
            "-n",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-i", str(output), "-f", "null", "-"],
        check=True,
    )
    result = probe(output)
    seconds = float(result["format"]["duration"])
    report = {
        "inputs": receipt,
        "output": output.name,
        "duration_seconds": seconds,
        "within_8_to_10_minutes": 480 <= seconds <= 600,
        "decode_verified": True,
        "audio_clarity_and_cuts_reviewed": False,
    }
    (folder / "assembly.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"{output}\nDuration: {seconds / 60:.2f} minutes")
    if not report["within_8_to_10_minutes"]:
        print("Outside the 8–10-minute target; review pacing and trims before submission.")
    print("Review the narration, readability and cuts before hosting the final video.")


if __name__ == "__main__":
    main()
