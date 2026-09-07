from pathlib import Path

from playwright.sync_api import expect
from sqlalchemy import text

from pap_agent import __version__
from pap_agent.seed import sunny_fixture
from pap_agent.store import save_scenario


def test_live_calculation_repeatable(
    browser, live_service, database, database_url, source_database
):
    save_scenario(database, sunny_fixture())
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url)
            page.get_by_role("button", name="Load sunny fixture").click()
            expect(page.locator("#evidence-note")).to_contain_text("Sunny demo")
            outputs = []
            for _ in range(2):
                with page.expect_response("**/api/v1/pap/calculate") as response:
                    page.get_by_role("button", name="Calculate PAP").click()
                outputs.append(response.value.json()["pap"]["intervals"])
                expect(page.get_by_role("button", name="Calculate PAP")).to_be_enabled()
            assert outputs[0] == outputs[1]
            expect(page.locator("#messages")).to_contain_text("10.6 kWh across 12 hours")
            with database.session() as session:
                session.execute(
                    text("""UPDATE source_fixture.telemetry_snapshots
                    SET timestamp = timestamp - interval '10 minutes'""")
                )
            page.get_by_role("button", name="Read MySolArk now").click()
            expect(page.get_by_role("button", name="Read MySolArk now")).to_be_enabled()
            with page.expect_response("**/api/v1/pap/calculate") as response:
                page.get_by_role("button", name="Calculate PAP").click()
            assert response.value.json()["status"] == "withheld"
            expect(page.locator("#messages")).to_contain_text("PAP withheld")
        finally:
            page.close()


def test_live_mysolark_mcp(browser, live_service, database_url, source_database):
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url)
            page.get_by_role("button", name="Read MySolArk now").click()
            expect(page.locator("#evidence-note")).to_have_text(
                "MySolArk live scrape + synthetic weather", timeout=15000
            )
            expect(page.locator("#tool-calls")).to_contain_text("get_current_telemetry")
            expect(page.locator("#tool-calls")).to_contain_text("get_solar_forecast")
            page.get_by_role("tab", name="Context", exact=True).click()
            expect(page.locator("#evidence-context")).to_contain_text('"data_mode": "live"')
            expect(page.locator("#messages")).to_contain_text("seconds ago")
        finally:
            page.close()


def test_live_persisted_fixture(browser, live_service, database, database_url):
    save_scenario(database, sunny_fixture())
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url)
            page.get_by_role("button", name="Load sunny fixture").click()
            expect(page.locator("#evidence-note")).to_have_text(
                "Sunny demo (synthetic) loaded from PostgreSQL."
            )
            expect(page.locator("#evidence-context")).to_contain_text('"battery_voltage_v": 53.2')
            expect(page.locator("#messages")).to_contain_text("4 kW solar")
            result = page.request.get(f"{url}/api/v1/scenarios/sunny")
            assert result.status == 200
            assert result.json()["telemetry"]["source"] == "synthetic fixture"
        finally:
            page.close()


def test_live_home_health_and_version(browser, live_service, database_url):
    with live_service(database_url) as url:
        page = browser.new_page(viewport={"width": 1360, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            response = page.goto(url)
            assert response.status == 200
            expect(page).to_have_title("DragonWings PAP Forecaster")
            expect(page.get_by_role("heading", name="DragonWings PAP Forecaster")).to_be_visible()
            expect(page.get_by_text("READ ONLY", exact=True)).to_be_visible()
            expect(
                page.get_by_text("Local telemetry · synthetic weather", exact=True)
            ).to_be_visible()
            page.get_by_role("button", name="Check service", exact=True).click()
            expect(page.get_by_role("status")).to_have_text("Service healthy")
            panels = {
                "Context": "Model context",
                "Memory": "Long-term memory",
                "Tools": "Tools and calls",
                "Subagent": "Subagent activity",
                "Trace": "Execution trace",
                "Health": "Service health",
            }
            for tab, heading in panels.items():
                page.get_by_role("tab", name=tab, exact=True).click()
                expect(page.get_by_role("tabpanel")).to_have_count(1)
                expect(
                    page.get_by_role("tabpanel").get_by_role("heading", name=heading)
                ).to_be_visible()
            expect(page.locator("#database-status")).to_have_text("ok")
            expect(page.locator("#pgvector-status")).to_have_text("ok")
            expect(page.locator("#app-version")).to_have_text(__version__)
            page.get_by_role("tab", name="Trace", exact=True).click()
            expect(page.locator("#trace-events li")).to_have_count(2)
            page.locator("#trace-events summary").first.click()
            Path("test-results").mkdir(exist_ok=True)
            page.screenshot(path="test-results/pap-home.png", full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.screenshot(path="test-results/pap-mobile.png", full_page=True)
            page.get_by_role("tab", name="Context", exact=True).click()
            page.get_by_role("tab", name="Context", exact=True).press("End")
            expect(page.get_by_role("tab", name="Health", exact=True)).to_be_focused()
            page.get_by_role("button", name="Reset view", exact=True).click()
            expect(page.get_by_role("status")).to_have_text("Service not checked")
            expect(page.locator("#trace-events li")).to_have_count(0)
            assert errors == []
            with page.expect_response(f"{url}/health") as health:
                page.get_by_role("link", name="Health", exact=True).click()
            assert health.value.status == 200
            assert health.value.json() == {"status": "ok", "database": "ok", "pgvector": "ok"}
            version = page.request.get(f"{url}/api/v1/version")
            assert version.status == 200
            assert version.json() == {
                "version": __version__,
                "read_only": True,
                "mode": "local",
            }
        finally:
            page.close()


def test_live_database_failure_is_visible(browser, live_service):
    with live_service("postgresql+psycopg://pap:test-secret@127.0.0.1:1/pap") as url:
        page = browser.new_page()
        try:
            page.goto(url)
            page.get_by_role("button", name="Check service", exact=True).click()
            expect(page.get_by_role("status")).to_have_text("Service unavailable")
            page.get_by_role("tab", name="Health", exact=True).click()
            expect(page.locator("#database-status")).to_have_text("unavailable")
            expect(page.locator("#app-version")).to_have_text(__version__)
            page.get_by_role("tab", name="Trace", exact=True).click()
            expect(page.locator("#trace-events")).to_contain_text("GET /health · 503")
            with page.expect_response(f"{url}/health") as health:
                page.get_by_role("link", name="Health", exact=True).click()
            assert health.value.status == 503
            assert health.value.json() == {
                "status": "unavailable",
                "database": "unavailable",
                "pgvector": "unavailable",
            }
            assert "test-secret" not in page.content()
            assert page.request.get(f"{url}/api/v1/version").status == 200
        finally:
            page.close()
