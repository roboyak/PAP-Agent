from urllib.parse import parse_qs, urlparse

from playwright.sync_api import expect
from sqlalchemy import text


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
            page.locator("#replay-time").fill("12:00")
            page.get_by_role("button", name="15 min", exact=True).click()
            with page.expect_response("**/api/v1/simulations") as response:
                page.get_by_role("button", name="Start simulation", exact=True).click()
            run = response.value.json()
            expect(page.locator("#publication-status")).to_have_text("Historical replay")
            expect(page.locator("#wing")).to_be_disabled()
            expect(page.locator("#playback-speed")).to_be_enabled()
            page.locator("#playback-speed").select_option("0")
            expect(page.locator("#run-progress")).to_be_hidden()
            expect(page.locator("#simulation-count")).not_to_have_text(
                f"0 / {run['total_steps']} steps"
            )
            page.get_by_role("button", name="Pause", exact=True).click()
            expect(page.locator("#simulation-status")).to_have_text("Paused")
            paused = page.request.get(f"{url}/api/v1/simulations/{run['id']}").json()
            assert 0 < paused["completed_steps"] < paused["total_steps"]
            assert paused["delay_seconds"] == 0
            expect(page.locator("#view-recorded")).to_have_attribute("aria-pressed", "true")
            assert run["ends_at"] == "2026-09-06T07:00:00Z"
            for selector in ("#simulator", "#recorded-chart", "#agent-guidance", "#view-inspector"):
                expect(page.locator(selector)).to_be_in_viewport(ratio=1)
            assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
            page.get_by_role("button", name="Future estimate", exact=True).click()
            expect(page.locator("#forecast-limit")).to_contain_text("does not predict sunrise")
            expect(page.locator("#forecast-chart")).to_be_in_viewport(ratio=1)
            page.get_by_role("button", name="Recorded day", exact=True).click()
            page.reload()
            expect(page.locator("#simulation-status")).to_have_text("Paused")
            expect(page.locator("#playback-speed")).to_have_value("0")
            page.locator("#playback-speed").select_option("3")
            expect(page.locator("#run-progress")).to_be_hidden()
            assert (
                page.request.get(f"{url}/api/v1/simulations/{run['id']}").json()["delay_seconds"]
                == 3
            )
            page.locator("#playback-speed").select_option("0")
            expect(page.locator("#run-progress")).to_be_hidden()
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


def test_recorded_morning_keeps_night_load_and_missing_gap(
    browser, live_service, database, database_url, wing_history
):
    with database.session() as session:
        session.execute(
            text("""INSERT INTO source_fixture.telemetry_snapshots VALUES
            ('test-1.21', 'solark_cloud', '2026-08-30 11:58:00', 380, 0, 1500),
            ('test-1.21', 'solark_cloud', '2026-08-30 13:58:00', 380, 800, 1500),
            ('test-1.21', 'solark_cloud', '2026-08-30 14:58:00', 380, 3200, 1500)""")
        )
    with live_service(database_url) as url:
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        try:
            response = page.request.post(
                url + "/api/v1/simulations",
                data={
                    "wing": "1.21",
                    "starts_at": "2026-08-30T05:00:00-07:00",
                    "ends_at": "2026-08-30T09:00:00-07:00",
                    "step_minutes": 60,
                },
            )
            run = response.json()
            page.goto(url + f"/?simulation={run['id']}")
            expect(page.locator("#simulation-status")).to_have_text("Finished", timeout=30000)
            expect(page.locator("#solar-current")).to_have_text("3.2 kW")
            expect(page.locator("#load-current")).to_have_text("1.5 kW")
            expect(page.locator("#surplus-current")).to_have_text("1.7 kW")
            expect(page.locator("#agent-guidance")).to_contain_text("leaving 1.7 kW")
            expect(page.locator("#source-time")).to_contain_text("7:58 AM Pacific")
            solar = page.locator('#recorded-chart circle[data-series="solar_kw"]')
            load = page.locator('#recorded-chart circle[data-series="load_kw"]')
            expect(solar).to_have_count(3)  # Missing 6 AM stays a gap, not a zero reading.
            assert float(solar.first.get_attribute("cy")) == 173  # Night solar is zero.
            assert float(load.first.get_attribute("cy")) < 173  # Site load still exists.
            assert float(solar.last.get_attribute("cx")) < 477  # Observed before Pacific noon.
            path = page.locator('#recorded-chart path[data-series="solar_kw"]').get_attribute("d")
            assert path.count("M") == 2  # Do not connect across the missing hour.
            expect(page.locator("#recorded-period")).to_contain_text("3 recorded step readings")
            assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
            result = page.request.get(url + f"/api/v1/simulations/{run['id']}").json()
            for index, message in [(0, "No solar was recorded"), (2, "site is using all of it")]:
                page.goto(url + f"/?episode={result['results'][index]['episode_id']}")
                page.get_by_role("button", name="Recorded day", exact=True).click()
                expect(page.locator("#agent-guidance")).to_contain_text(message)
        finally:
            page.close()


def test_choose_inclusive_dates_and_review_an_earlier_day(
    browser, live_service, database, database_url, wing_history
):
    with database.session() as session:
        session.execute(
            text("""INSERT INTO source_fixture.telemetry_snapshots VALUES
            ('test-1.21', 'solark_cloud', '2026-08-31 05:58:00', 380, 0, 1100),
            ('test-1.21', 'solark_cloud', '2026-08-31 06:58:00', 380, 0, 1200),
            ('test-1.21', 'solark_cloud', '2026-08-31 07:58:00', 380, 0, 1300)""")
        )
    with live_service(database_url) as url:
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        try:
            run = page.request.post(
                url + "/api/v1/simulations",
                data={
                    "wing": "1.21",
                    "starts_at": "2026-08-30T23:00:00-07:00",
                    "ends_at": "2026-08-31T02:00:00-07:00",
                    "step_minutes": 60,
                },
            ).json()
            page.goto(url + f"/?simulation={run['id']}")
            expect(page.locator("#simulation-status")).to_have_text("Finished", timeout=30000)
            expect(page.locator("#chart-day option")).to_have_count(3)
            expect(page.locator("#recorded-day-heading")).to_contain_text("Aug 31")
            page.locator("#chart-day").select_option("2026-08-30")
            expect(page.locator("#recorded-day-heading")).to_contain_text("Aug 30")
            expect(page.locator("#load-current")).to_have_text("1.1 kW")
            expect(page.locator("#simulation-time")).to_contain_text("Aug 31")
            result = page.request.get(url + f"/api/v1/simulations/{run['id']}").json()
            expect(page.locator("#view-inspector")).to_have_attribute(
                "href",
                f"/inspector?episode={result['results'][0]['episode_id']}&simulation={run['id']}",
            )
            page.locator("#chart-day").select_option("follow")
            expect(page.locator("#load-current")).to_have_text("1.3 kW")
            page.get_by_role("button", name="Run once", exact=True).click()
            expect(page.locator("#publication-status")).to_have_text("Historical replay")
            page.get_by_role("button", name="Recorded day", exact=True).click()
            expect(page.locator("#chart-day")).to_be_disabled()
            expect(page.locator("#chart-day option")).to_have_count(1)
            page.locator("#replay-day").select_option("2026-09-02")
            page.locator("#replay-end-day").select_option("2026-09-03")
            page.locator("#replay-time").fill("00:00")
            with page.expect_response("**/api/v1/simulations") as response:
                page.get_by_role("button", name="Start simulation", exact=True).click()
            selected = response.value.json()
            assert selected["starts_at"] == "2026-09-02T07:00:00Z"
            assert selected["ends_at"] == "2026-09-04T07:00:00Z"
            assert selected["total_steps"] == 48
            page.get_by_role("button", name="Pause", exact=True).click()
            expect(page.locator("#simulation-status")).to_have_text("Paused")
        finally:
            page.close()
