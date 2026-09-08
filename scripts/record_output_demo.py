"""Record a fresh PAP request and explain its published output through Playwright."""

import argparse
import asyncio
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".cache/playwright"))


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    folder = ROOT / "output/recordings" / datetime.now(UTC).strftime("output_%Y%m%d_%H%M%S")
    folder.mkdir(parents=True)
    chapters = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 1440, "height": 1080},
            record_video_dir=folder / "capture",
            record_video_size={"width": 1440, "height": 1080},
        )
        started = monotonic()
        page = await context.new_page()
        page.set_default_timeout(30000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        latest = await (await context.request.get(f"{args.url}/api/v1/pap/latest")).json()
        # Open a fixed result so an older simulator does not replace the recording controls.
        query = f"?episode={latest['episode_id']}" if latest else ""
        await page.goto(args.url + query)
        await expect(page.locator("#source")).to_be_enabled()
        await page.locator("#source").select_option("sunny")
        await page.locator("#source").select_option("mysolark")
        await page.locator("#wing").select_option("1.24")
        await page.locator("#time-window").select_option("live")
        await page.evaluate("""() => {
          const caption = document.createElement('div'); caption.id = 'demo-caption';
          caption.style.cssText = `position:fixed;bottom:0;left:0;right:0;z-index:999;
            background:#25251b;color:#e0d7b3;padding:16px 28px;font:20px/1.4 system-ui;
            border-top:2px solid #aab596;pointer-events:none`;
          document.body.append(caption); document.body.style.paddingBottom='100px';
        }""")
        offset = monotonic() - started
        began = monotonic()

        async def caption(text):
            chapters.append({"seconds": round(monotonic() - began, 2), "caption": text})
            await page.locator("#demo-caption").evaluate(
                "(node, text) => { node.textContent = text; }", text
            )
            print(text, flush=True)

        await caption(
            "1. Choose MySolArk. Run PAP will read real solar power, load and battery voltage."
        )
        await page.wait_for_timeout(5000)
        await caption("2. Run PAP. This is a new request. The waiting time is shown in real time.")
        async with page.expect_response("**/api/v1/pap/run", timeout=420000) as response:
            await page.get_by_role("button", name="Run PAP", exact=True).click()
        response = await response.value
        assert response.status == 200
        episode = await response.json()
        await expect(page.get_by_role("button", name="Run PAP", exact=True)).to_be_enabled()
        await expect(page.locator("#profile-summary")).to_be_in_viewport()
        publication = await (
            await context.request.get(f"{args.url}/api/v1/pap/{episode['publication_id']}")
        ).json()
        assert publication["status"] == "valid", "This output lesson requires a published example"
        assert publication["evidence"]["telemetry"]["data_mode"] == "live"
        assert publication["selection"] == {"wing": "1.24", "replay_at": None}
        records = await (
            await context.request.get(
                f"{args.url}/api/v1/episodes/{episode['episode_id']}/inspection"
            )
        ).json()
        intervals = publication["profile"]["intervals"]
        first = intervals[0]["available_kw"]
        energy = round(sum(row["energy_kwh"] for row in intervals), 3)
        confidence = publication["profile"]["confidence"]
        await page.locator("#published-profile").evaluate(
            "node => node.scrollIntoView({block:'start'})"
        )
        await caption(
            f"3. The output: {first:g} kW additional in the first interval, "
            f"{energy:.3f} kWh across 12 hours, {confidence} confidence."
        )
        await page.locator("#published-profile").screenshot(path=folder / "output-panel.png")
        await page.screenshot(path=folder / "output-screen.png")
        await page.wait_for_timeout(18000)
        await caption(
            "4. Each bar covers one hour. kW is modeled power headroom. "
            "The kWh total adds the energy available across all twelve hours."
        )
        await page.wait_for_timeout(18000)
        await caption(
            "5. Zero means the model allocates no extra solar power in that interval. "
            "The total is spread across the forecast, not available all at once."
        )
        await page.wait_for_timeout(16000)
        await page.locator(".guidance-panel details summary").click()
        await page.locator("#agent-guidance").scroll_into_view_if_needed()
        await caption(
            "6. Read the agent guidance and calculation assumptions. "
            "Weather is synthetic and battery discharge is zero. The operator decides what to do."
        )
        await page.wait_for_timeout(18000)
        await caption(
            "7. Valid means publication checks passed. Confidence is a qualitative label. "
            "PAP never switches equipment on or off."
        )
        await page.wait_for_timeout(12000)
        await page.get_by_role("link", name="Inspect this run", exact=True).click()
        await expect(page.get_by_role("button", name="Run PAP", exact=True)).to_be_enabled()
        await page.evaluate("""() => {
          const caption = document.createElement('div'); caption.id = 'demo-caption';
          caption.style.cssText = `position:fixed;bottom:0;left:0;right:0;z-index:999;
            background:#25251b;color:#e0d7b3;padding:16px 28px;
            font:20px/1.4 system-ui;pointer-events:none`;
          document.body.append(caption);
        }""")
        await page.get_by_role("tab", name="Trace", exact=True).click()
        await page.locator(".inspector").scroll_into_view_if_needed()
        await caption(
            "8. Inspector follows this run. Trace shows workflow order. "
            "Health checks the current service."
        )
        await page.wait_for_timeout(15000)
        await page.get_by_role("tab", name="Subagent", exact=True).click()
        providers = sorted(
            {record.get("provider", "unknown") for record in records if record.get("calls")}
        )
        model_label = (
            f"actual {', '.join(providers)} model attempts"
            if providers
            else "that this run made no model calls"
        )
        await caption(
            f"9. Subagent shows {model_label}. "
            "Use Forecast in the navigation to return to the same output."
        )
        await page.wait_for_timeout(12000)
        duration = monotonic() - began
        assert not errors, errors
        example = {
            "captured_at": datetime.now(UTC).isoformat(),
            "implementation_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "working_tree_dirty": bool(
                subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=ROOT, text=True
                ).strip()
            ),
            "episode": episode,
            "publication": publication,
            "models": [
                {key: record.get(key) for key in ("kind", "provider", "model", "status", "calls")}
                for record in records
                if record.get("calls")
            ],
        }
        (folder / "output-example.json").write_text(json.dumps(example, indent=2) + "\n")
        await context.close()
        raw = await page.video.path()
        await browser.close()
    video = folder / "DragonWings_Output_Demo.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(offset),
            "-i",
            str(raw),
            "-t",
            str(duration),
            "-an",
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(video),
        ],
        check=True,
    )
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type,width,height",
                "-of",
                "json",
                str(video),
            ]
        )
    )
    assert abs(float(probe["format"]["duration"]) - duration) < 1
    assert all(stream["codec_type"] == "video" for stream in probe["streams"])
    (folder / "recording.json").write_text(
        json.dumps(
            {
                "episode_id": episode["episode_id"],
                "chapters": chapters,
                "probe": probe,
                "audio": "Silent. Captions explain the output; add your narration if desired.",
                "presentation": (
                    "Actual browser use: fresh MySolArk run, published forecast, "
                    "and the matching Inspector episode."
                ),
            },
            indent=2,
        )
        + "\n"
    )
    (ROOT / ".cache/output-demo-latest.txt").write_text(str(folder) + "\n")
    print(f"Output demo: {folder}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
