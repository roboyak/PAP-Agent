from urllib.parse import parse_qs, urlparse

from playwright.sync_api import expect


def test_simulator_start_pause_inspect_resume(browser, live_service, database_url, wing_history):
    with live_service(database_url) as url:
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            page.goto(url)
            page.locator("#source").select_option("mysolark")
            page.locator("#wing").select_option("1.21")
            page.locator("#time-window").select_option("week")
            page.locator("#replay-time").fill("2026-08-30T12:00")
            page.get_by_role("button", name="15 min", exact=True).click()
            with page.expect_response("**/api/v1/simulations") as response:
                page.get_by_role("button", name="Start simulation", exact=True).click()
            run = response.value.json()
            expect(page.locator("#publication-status")).to_have_text("Historical replay")
            expect(page.locator("#wing")).to_be_disabled()
            expect(page.locator("#simulation-count")).not_to_have_text(
                f"0 / {run['total_steps']} steps"
            )
            page.get_by_role("button", name="Pause", exact=True).click()
            expect(page.locator("#simulation-status")).to_have_text("Paused")
            paused = page.request.get(f"{url}/api/v1/simulations/{run['id']}").json()
            assert 0 < paused["completed_steps"] < paused["total_steps"]
            for selector in ("#simulator", "#forecast-chart", "#agent-guidance", "#view-inspector"):
                expect(page.locator(selector)).to_be_in_viewport(ratio=1)
            assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
            page.reload()
            expect(page.locator("#simulation-status")).to_have_text("Paused")
            expect(page.locator("#simulation-count")).to_have_text(
                f"{paused['completed_steps']} / {paused['total_steps']} steps"
            )
            page.get_by_role("button", name="Results", exact=True).click()
            expect(page.locator("#simulation-results tr")).to_have_count(paused["completed_steps"])
            page.locator("#simulation-results a").first.click()
            expect(page.get_by_role("tab")).to_have_count(6)
            episode_id = paused["results"][0]["episode_id"]
            expect(page.locator("#graph-trace")).to_contain_text(episode_id)
            expect(page.locator("#evaluate-outcome")).to_be_disabled()
            page.get_by_role("link", name="Back to simulation", exact=True).click()
            expect(page.locator("#simulation-status")).to_have_text("Paused")
            page.get_by_role("button", name="Resume", exact=True).click()
            expect(page.locator("#simulation-count")).not_to_have_text(
                f"{paused['completed_steps']} / {paused['total_steps']} steps"
            )
            page.get_by_role("link", name="Inspect this run", exact=True).click()
            expect(page.locator("#graph-trace")).to_contain_text("finalize_episode")
            selected = parse_qs(urlparse(page.url).query)["episode"][0]
            # The browser is inspecting a fixed episode while the server advances.
            before = page.request.get(f"{url}/api/v1/simulations/{run['id']}").json()[
                "completed_steps"
            ]
            page.wait_for_function(
                """async ({id, before}) => {
                    const response = await fetch(`/api/v1/simulations/${id}`);
                    return (await response.json()).completed_steps > before;
                }""",
                arg={"id": run["id"], "before": before},
            )
            expect(page.locator("#graph-trace")).to_contain_text(selected)
            page.get_by_role("link", name="Back to simulation", exact=True).click()
            expect(page.locator("#simulation-status")).to_have_text("Running")
            page.get_by_role("button", name="Pause", exact=True).click()
            expect(page.locator("#simulation-status")).to_have_text("Paused")
            page.screenshot(path="test-results/pap-simulator.png", full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert errors == []
        finally:
            page.close()
