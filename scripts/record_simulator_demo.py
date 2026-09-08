"""Record a short, silent MySolArk replay through the real browser controls."""

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".cache/playwright"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--wing", choices=["1.21", "1.22", "1.23", "1.24", "1.25"], default="1.21")
    parser.add_argument("--start", default="2026-08-30T12:00", help="Pacific time")
    parser.add_argument("--step", type=int, choices=[15, 60], default=60)
    args = parser.parse_args()
    folder = ROOT / "output/recordings" / datetime.now(UTC).strftime("simulator_%Y%m%d_%H%M%S")
    folder.mkdir(parents=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            record_video_dir=folder / "capture",
            record_video_size={"width": 1366, "height": 768},
        )
        page = context.new_page()
        page.set_default_timeout(60000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        run_id = None
        try:
            latest = context.request.get(f"{args.url}/api/v1/pap/latest").json()
            page.goto(args.url + (f"?episode={latest['episode_id']}" if latest else ""))
            expect(page.locator("#source")).to_be_enabled()
            page.locator("#source").select_option("mysolark")
            page.locator("#wing").select_option(args.wing)
            page.locator("#time-window").select_option("week")
            page.locator("#replay-time").fill(args.start)
            page.get_by_role(
                "button", name="15 min" if args.step == 15 else "1 hour", exact=True
            ).click()
            with page.expect_response("**/api/v1/simulations") as response:
                page.get_by_role("button", name="Start simulation", exact=True).click()
            assert response.value.status == 200, "Pause any existing simulation before recording."
            run_id = response.value.json()["id"]
            expect(page.locator("#published-profile")).to_be_visible()
            expect(page.locator("#publication-status")).to_have_text("Historical replay")
            page.screenshot(path=folder / "first-forecast.png")
            page.wait_for_timeout(10000)
            page.get_by_role("button", name="Pause", exact=True).click()
            expect(page.locator("#simulation-status")).to_have_text("Paused", timeout=600000)
            page.screenshot(path=folder / "paused.png")
            page.get_by_role("button", name="Results", exact=True).click()
            page.wait_for_timeout(3500)
            page.locator("#simulation-results a").first.click()
            expect(page.locator("#graph-trace")).to_contain_text("finalize_episode")
            for tab in ("Context", "Tools", "Subagent", "Trace", "Memory", "Health"):
                page.get_by_role("tab", name=tab, exact=True).click()
                page.wait_for_timeout(1000)
            page.get_by_role("link", name="Back to simulation", exact=True).click()
            page.get_by_role("button", name="Resume", exact=True).click()
            page.wait_for_timeout(5000)
            page.get_by_role("button", name="Pause", exact=True).click()
            expect(page.locator("#simulation-status")).to_have_text("Paused", timeout=600000)
            result = context.request.get(f"{args.url}/api/v1/simulations/{run_id}").json()
            assert result["completed_steps"] > 1 and not errors
            (folder / "run.json").write_text(json.dumps(result, indent=2) + "\n")
            page.screenshot(path=folder / "desktop.png", full_page=True)
            page.wait_for_timeout(3000)
            video = page.video
        finally:
            try:
                if run_id:
                    context.request.post(f"{args.url}/api/v1/simulations/{run_id}/pause")
            finally:
                context.close()
        video.save_as(folder / "simulator.webm")
        browser.close()
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(folder / "simulator.webm"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(folder / "simulator.mp4"),
        ],
        check=True,
    )
    print(folder)
    print(f"{args.url}/?simulation={run_id}")


if __name__ == "__main__":
    main()
