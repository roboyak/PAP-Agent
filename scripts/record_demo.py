"""Record both narration-ready app walkthroughs through a real local Playwright browser."""

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
CHAPTERS = json.loads((ROOT / "submission/recording_chapters.json").read_text())
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".cache/playwright"))


async def focus_record(page, selector, key):
    await page.locator(selector).evaluate(
        """(element, key) => {
          const node = element.firstChild, range = document.createRange();
          const start = node.textContent.indexOf(`"${key}":`);
          if (start < 0) throw new Error(`Missing recorded field: ${key}`);
          range.setStart(node, start); range.setEnd(node, start + key.length + 3);
          const panel = element.closest('[role="tabpanel"]');
          panel.scrollTop += range.getBoundingClientRect().top
            - panel.getBoundingClientRect().top - 16;
        }""",
        key,
    )


async def show(page, chapter):
    action = chapter["action"]
    tabs = {
        "overview": "Context",
        "context": "Context",
        "context_raw": "Context",
        "memory": "Memory",
        "memory_search": "Memory",
        "tools": "Tools",
        "agents": "Subagent",
        "agents_raw": "Subagent",
        "trace": "Trace",
        "search": "Trace",
        "health": "Health",
        "calculate": "Context",
    }
    await page.get_by_role("tab", name=tabs[action], exact=True).click()
    await page.get_by_role("tabpanel").evaluate("element => { element.scrollTop = 0; }")
    await page.evaluate("window.scrollTo(0, 0)")
    details = {"context_raw": "model-context", "agents_raw": "agent-activity"}
    if action in details:
        target = page.locator(f"#details-{details[action]}")
        if not await target.get_attribute("open"):
            await target.locator("summary").click()
        await target.scroll_into_view_if_needed()
        if action == "agents_raw":
            await focus_record(page, "#agent-activity", "tools")
    elif action == "memory_search":
        await page.locator("#memory-query").fill("battery voltage reserve")
        await page.get_by_role("button", name="Search memory", exact=True).click()
        await expect(page.get_by_role("button", name="Search memory", exact=True)).to_be_enabled()
    elif action == "search":
        await page.get_by_text("Search branches and selection", exact=True).click()
        await focus_record(page, "#search-trace", "branches")
    elif action == "health":
        await page.get_by_role("button", name="Check service", exact=True).click()
        await expect(page.get_by_role("button", name="Check service", exact=True)).to_be_enabled()
    elif action == "calculate":
        await page.get_by_role("button", name="Load sunny fixture").click()
        await expect(page.get_by_role("button", name="Calculate PAP", exact=True)).to_be_enabled()
        await page.get_by_role("button", name="Calculate PAP", exact=True).click()
        await expect(page.locator("#calculation-summary")).to_contain_text("10.600 kWh")
        await page.locator("#calculation-summary").scroll_into_view_if_needed()


async def record(browser, args, output, version, seconds):
    cache = output / f"{version}-capture"
    context = await browser.new_context(
        viewport={"width": 1440, "height": 1000},
        record_video_dir=cache,
        record_video_size={"width": 1440, "height": 1000},
    )
    started = monotonic()
    page = await context.new_page()
    page.set_default_timeout(30000)
    episode = await (await context.request.get(f"{args.url}/api/v1/episodes/{args.episode}")).json()
    records = await (
        await context.request.get(f"{args.url}/api/v1/episodes/{args.episode}/inspection")
    ).json()
    models = [record for record in records if record.get("calls")]
    assert episode["scenario"] == "sunny", "Use the labeled sunny fixture for these captions"
    assert episode["status"] == "valid" and episode["reasoning_mode"] == "selective_tot", (
        "Use a completed, published selective-reasoning run"
    )
    assert models and all(record.get("provider") == "ollama" for record in models), (
        "These narration cues describe a real Ollama run"
    )
    assert {"generator", "critic"} <= {
        record["kind"] for record in models if record["status"] == "ok"
    }, "These narration cues require successful generator and critic records"
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    await page.goto(f"{args.url}/inspector?episode={args.episode}")
    await expect(page.get_by_role("button", name="Run PAP", exact=True)).to_be_enabled()
    await expect(page.locator("#run-meta")).to_contain_text(args.episode)
    await page.evaluate("""() => {
      const note = document.createElement('div'); note.id = 'recording-caption';
      note.style.cssText = `position:fixed;bottom:0;left:0;right:0;z-index:999;
        background:#142632;color:white;padding:14px 32px;font:18px/1.4 system-ui;
        box-shadow:0 -1px 0 #7bcddd;pointer-events:none`;
      document.body.append(note); document.body.style.paddingBottom = '100px';
    }""")
    offset = monotonic() - started
    walk_started = monotonic()
    timings = []
    for i, chapter in enumerate(CHAPTERS):
        begin = monotonic() - walk_started
        await page.locator("#recording-caption").evaluate(
            "(node, text) => { node.textContent = text; }",
            f"{i + 1}/{len(CHAPTERS)}  {chapter['title']} — {chapter['cue']}",
        )
        await show(page, chapter)
        if errors:
            raise RuntimeError(f"Browser error during {chapter['title']}: {errors}")
        await page.screenshot(path=cache / f"chapter-{i + 1:02}.png")
        timings.append({"start_seconds": round(begin, 2), "title": chapter["title"]})
        print(f"{version}: {i + 1}/{len(CHAPTERS)} {chapter['title']}", flush=True)
        remaining = seconds * (i + 1) / len(CHAPTERS) - (monotonic() - walk_started)
        if remaining > 0:
            await page.wait_for_timeout(remaining * 1000)
    await page.wait_for_timeout(1500)
    await context.close()
    raw = await page.video.path()
    destination = output / f"DragonWings_App_Walkthrough_{version}.mp4"
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(offset),
        "-i",
        str(raw),
        "-t",
        str(seconds),
        "-an",
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(destination),
    )
    if await process.wait():
        raise RuntimeError("MP4 conversion failed")
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
                str(destination),
            ]
        )
    )
    assert abs(float(probe["format"]["duration"]) - seconds) < 1
    assert not any(stream["codec_type"] == "audio" for stream in probe["streams"])
    (output / f"{version}-chapters.json").write_text(
        json.dumps(
            {
                "episode_id": args.episode,
                "duration_seconds": seconds,
                "audio": "None; ready for the owner's narration",
                "chapters": timings,
                "probe": probe,
            },
            indent=2,
        )
    )
    print(f"Saved {destination}", flush=True)


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--episode", required=True, help="Completed sunny-fixture run with real model calls"
    )
    parser.add_argument("--version", choices=["short", "full", "both"], default="both")
    args = parser.parse_args()
    output = ROOT / "output/recordings" / datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output.mkdir(parents=True)
    versions = {"short": 150, "full": 540}
    notes = [
        "# App walkthrough narration",
        "",
        "Silent browser footage; captions are recording annotations. "
        "Add your own narration before submission.",
        "",
    ]
    for version, duration in versions.items():
        notes.extend([f"## {version.title()} version ({duration // 60}:{duration % 60:02})", ""])
        for i, chapter in enumerate(CHAPTERS):
            start = int(i * duration / len(CHAPTERS))
            notes.extend(
                [f"### {start // 60}:{start % 60:02}  {chapter['title']}", "", chapter[version], ""]
            )
    (output / "Narration_Guide.md").write_text("\n".join(notes))
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            await asyncio.gather(
                *(
                    record(browser, args, output, version, duration)
                    for version, duration in versions.items()
                    if args.version in {version, "both"}
                )
            )
        finally:
            await browser.close()
    (ROOT / ".cache/recordings-latest.txt").write_text(str(output) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
