"""Use the real local UI to verify seven-day playback and recovery for every wing."""

import argparse
import json
import os
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".cache/playwright"))
PACIFIC = ZoneInfo("America/Los_Angeles")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--wings", nargs="+", default=["1.21", "1.22", "1.23", "1.24", "1.25"])
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/data/week-playback-verification.json"
    )
    args = parser.parse_args()
    report = {"checked_at": datetime.now(UTC).isoformat(), "status": "running", "runs": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    screenshots = ROOT / "test-results/real-week-playback"
    screenshots.mkdir(parents=True, exist_ok=True)

    def save():
        args.output.write_text(json.dumps(report, indent=2) + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        page.set_default_timeout(60000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        current_id = None
        try:
            page.goto(args.url)
            expect(page.locator("#source")).to_be_enabled()
            for wing in args.wings:
                started = time.monotonic()
                page.locator("#source").select_option("mysolark")
                page.locator("#wing").select_option(wing)
                page.locator("#time-window").select_option("week")
                page.locator("#replay-day").select_option("2026-08-30")
                page.locator("#replay-end-day").select_option("2026-09-05")
                page.locator("#replay-time").fill("00:00")
                page.get_by_role("button", name="1 hour", exact=True).click()
                page.locator("#playback-speed").select_option("0")
                with page.expect_response("**/api/v1/simulations") as response:
                    page.get_by_role("button", name="Start simulation", exact=True).click()
                assert response.value.status == 200
                run = response.value.json()
                current_id = run["id"]
                assert run["wing"] == wing
                assert run["total_steps"] == 168 and run["delay_seconds"] == 0
                print(f"DW {wing} started: {args.url}/?simulation={current_id}", flush=True)
                page.wait_for_function(
                    "n => parseInt(document.getElementById('simulation-count').textContent) >= n",
                    arg=13,
                    timeout=300000,
                )
                page.get_by_role("button", name="Pause", exact=True).click()
                expect(page.locator("#simulation-status")).to_have_text("Paused")
                expect(page.locator("#run-progress")).to_be_hidden()
                paused = page.request.get(f"{args.url}/api/v1/simulations/{current_id}").json()
                before = paused["completed_steps"]
                page.reload()
                expect(page.locator("#simulation-status")).to_have_text("Paused")
                expect(page.locator("#run-progress")).to_be_hidden()
                expect(page.locator("#playback-speed")).to_have_value("0")
                page.get_by_role("button", name="Resume", exact=True).click()
                page.wait_for_function(
                    "n => parseInt(document.getElementById('simulation-count').textContent) > n",
                    arg=before,
                    timeout=300000,
                )
                for count in range(24, 169, 24):
                    page.wait_for_function(
                        """n => parseInt(document.querySelector('#simulation-count')
                            .textContent) >= n""",
                        arg=count,
                        timeout=300000,
                    )
                    print(f"DW {wing}: {count}/168 steps", flush=True)
                expect(page.locator("#simulation-status")).to_have_text("Finished")
                finished = page.request.get(f"{args.url}/api/v1/simulations/{current_id}").json()
                assert finished["wing"] == wing
                assert finished["status"] == "completed" and len(finished["results"]) == 168
                days = Counter(
                    datetime.fromisoformat(row["replay_at"]).astimezone(PACIFIC).date().isoformat()
                    for row in finished["results"]
                )
                assert len(days) == 7 and set(days.values()) == {24}
                assert any(row["status"] == "valid" for row in finished["results"])
                assert len({row["episode_id"] for row in finished["results"]}) == 168
                expect(page.locator("#run-meta")).to_contain_text(
                    finished["results"][-1]["episode_id"]
                )
                expect(page.locator("#chart-day option")).to_have_count(8)
                assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
                page.screenshot(path=screenshots / f"dw-{wing}-last-day.png", full_page=True)
                page.locator("#chart-day").select_option("2026-08-30")
                expect(page.locator("#run-meta")).to_contain_text(
                    finished["results"][23]["episode_id"]
                )
                page.screenshot(path=screenshots / f"dw-{wing}-first-day.png", full_page=True)
                page.locator("#chart-day").select_option("follow")
                expect(page.locator("#run-meta")).to_contain_text(
                    finished["results"][-1]["episode_id"]
                )
                assert not errors
                report["runs"].append(
                    {
                        **{
                            key: finished[key]
                            for key in (
                                "wing",
                                "id",
                                "status",
                                "starts_at",
                                "ends_at",
                                "step_minutes",
                                "delay_seconds",
                                "completed_steps",
                                "total_steps",
                            )
                        },
                        "url": f"{args.url}/?simulation={current_id}",
                        "day_steps": dict(days),
                        "outcomes": dict(Counter(row["status"] for row in finished["results"])),
                        "pause_reload_resume_verified": True,
                        "earlier_day_review_verified": True,
                        "elapsed_seconds": round(time.monotonic() - started, 1),
                        "browser_errors": [],
                    }
                )
                save()
                print(f"DW {wing} PASSED", flush=True)
                current_id = None
            report["status"] = "complete"
            save()
        finally:
            if current_id:
                page.request.post(f"{args.url}/api/v1/simulations/{current_id}/pause")
            browser.close()
    print(args.output, flush=True)


if __name__ == "__main__":
    main()
