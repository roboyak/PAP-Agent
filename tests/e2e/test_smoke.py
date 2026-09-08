from pathlib import Path

import pytest
from playwright.sync_api import expect
from sqlalchemy import text

from pap_agent import __version__
from pap_agent.seed import sunny_fixture
from pap_agent.store import save_scenario


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_live_cloud_provider_configuration(
    browser, live_service, database_url, monkeypatch, provider
):
    monkeypatch.setenv("AGENT_BACKEND", provider)
    monkeypatch.setenv("AGENT_MODEL", "selected-cloud-model")
    monkeypatch.setenv(f"{provider.upper()}_API_KEY", "local-test-key")
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url + "/inspector")
            page.get_by_role("button", name="Check service", exact=True).click()
            expect(page.get_by_role("status")).to_have_text("Service healthy")
            page.get_by_role("tab", name="Health", exact=True).click()
            expect(page.locator("#readiness-result")).to_contain_text(
                f'"model_backend": "{provider}"'
            )
            expect(page.locator("#readiness-result")).to_contain_text("selected-cloud-model")
            expect(page.locator("#readiness-result")).to_contain_text("Configuration only")
            assert "local-test-key" not in page.content()
        finally:
            page.close()


def test_live_memory_search(browser, live_service, database_url):
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url + "/inspector")
            page.get_by_role("tab", name="Memory", exact=True).click()
            page.get_by_role("button", name="Index memory").click()
            expect(page.locator("#memory-results")).to_contain_text('"indexed": 3')
            page.locator("#memory-query").fill("battery voltage reserve")
            page.get_by_role("button", name="Search memory").click()
            expect(page.locator("#memory-results")).to_contain_text('"source_id": "reserve"')
            expect(page.locator("#memory-results")).to_contain_text("cosine similarity")
        finally:
            page.close()


def test_live_outcome_feedback(browser, live_service, database, database_url):
    save_scenario(database, sunny_fixture())
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url + "/inspector")
            page.get_by_role("button", name="Load sunny fixture").click()
            expect(page.locator("#evidence-note")).to_contain_text("Sunny demo")
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#profile-summary")).to_contain_text("reduced confidence")
            page.get_by_role("button", name="Evaluate cloudy demo").click()
            expect(page.locator("#outcome-feedback")).to_contain_text('"solar_bias_kw": 2')
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#profile-summary")).to_contain_text("low confidence")
            expect(page.locator("#profile-summary")).to_contain_text("10.600 kWh")
        finally:
            page.close()


def test_live_durable_workflow(browser, live_service, database_url, source_database):
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url + "/inspector")
            page.get_by_role("button", name="Read MySolArk now").click()
            expect(page.get_by_role("button", name="Read MySolArk now")).to_be_enabled()
            with page.expect_response("**/api/v1/pap/run") as response:
                page.get_by_role("button", name="Run PAP").click()
            episode = response.value.json()
            expect(page.locator("#graph-trace")).to_contain_text("finalize_episode")
            assert episode["status"] == "valid"
            expect(page.locator("#profile-intervals tr")).to_have_count(12)
            expect(page.locator("#profile-provenance")).to_contain_text("floor 305.2 V")
            publication = page.request.get(f"{url}/api/v1/pap/{episode['publication_id']}").json()
            assert publication["evidence_id"] == episode["evidence_id"]
            page.reload()
            expect(page.locator("#profile-intervals tr")).to_have_count(12)
            assert (
                page.request.get(f"{url}/api/v1/episodes/{episode['episode_id']}").json() == episode
            )
            resumed = page.request.post(f"{url}/api/v1/episodes/{episode['episode_id']}/resume")
            assert resumed.json() == episode
        finally:
            page.close()


def test_live_calculation_repeatable(
    browser, live_service, database, database_url, source_database
):
    save_scenario(database, sunny_fixture())
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url + "/inspector")
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
            page.goto(url + "/inspector")
            page.get_by_role("button", name="Read MySolArk now").click()
            expect(page.locator("#evidence-note")).to_have_text(
                "DW 1.24 MySolArk live scrape + synthetic weather", timeout=15000
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
            page.goto(url + "/inspector")
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
            response = page.goto(url + "/inspector")
            assert response.status == 200
            expect(page).to_have_title("DragonWings PAP Inspector")
            expect(page.get_by_role("heading", name="Run inspector")).to_be_visible()
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
            expect(page.locator("#trace-events li")).to_have_count(4)
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
            page.goto(url + "/inspector")
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


def test_live_agent_comparison(browser, live_service, database, database_url):
    from pap_agent.memory import index_memory

    save_scenario(database, sunny_fixture())
    index_memory(database)
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url + "/inspector")
            page.get_by_role("button", name="Load sunny fixture").click()
            page.get_by_role("button", name="Compare agent off / on").click()
            expect(page.locator("#agent-comparison")).to_contain_text(
                '"same_available_power": true', timeout=30000
            )
            expect(page.locator("#model-calls")).to_have_text("1")
            expect(page.locator("#model-context")).to_contain_text("evidence_id")
            page.get_by_role("tab", name="Subagent", exact=True).click()
            expect(page.locator("#agent-activity")).to_contain_text('"tools": []')
            expect(page.locator("#agent-activity")).to_contain_text('"status": "ok"')
            page.get_by_role("tab", name="Memory", exact=True).click()
            expect(page.locator("#run-memory-results")).to_contain_text("selection_reason")
            saved_url = page.url
            page.reload()
            expect(page.locator("#run-meta a")).to_have_attribute(
                "href", "?episode=" + saved_url.split("?episode=")[1]
            )
            page.get_by_role("tab", name="Subagent", exact=True).click()
            expect(page.locator("#agent-summary")).to_contain_text("interpretation: ok")
            expect(page.locator("#agent-summary")).to_contain_text("test-double")
            page.get_by_role("tab", name="Memory", exact=True).click()
            recorded_memory = page.locator("#run-memory-results").text_content()
            page.get_by_role("button", name="Search memory", exact=True).click()
            expect(page.locator("#memory-search-summary")).to_contain_text("manual search results")
            assert page.locator("#run-memory-results").text_content() == recorded_memory
            page.route("**/inspection", lambda route: route.abort())
            page.reload()
            expect(page.locator("#run-status")).to_have_text("Run details unavailable.")
            expect(page.locator("#published-profile")).to_be_hidden()
            expect(page.locator("#model-summary")).to_have_text("Run records could not be loaded.")
            expect(page.locator("#trace-events")).to_contain_text("network error")
            assert page.url == saved_url
            page.unroute("**/inspection")
            page.reload()
            expect(page.locator("#agent-summary")).to_contain_text("interpretation: ok")
            page.get_by_role("button", name="Load sunny fixture").click()
            expect(page.locator("#run-status")).to_contain_text("source preview")
            expect(page.locator("#published-profile")).to_be_hidden()
            expect(page.locator("#run-meta")).to_be_empty()
            expect(page.locator("#agent-summary")).to_be_empty()
        finally:
            page.close()


def test_live_pending_run_locks_source_actions(browser, live_service, database, database_url):
    save_scenario(database, sunny_fixture())
    with live_service(database_url) as url:
        page = browser.new_page()
        pending = []
        try:
            page.goto(url + "/inspector")
            page.route("**/api/v1/pap/run", lambda route: pending.append(route))
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#run-progress")).to_contain_text("seconds elapsed")
            expect(page.get_by_role("button", name="Load sunny fixture")).to_be_disabled()
            expect(page.get_by_role("button", name="Compare agent off / on")).to_be_disabled()
            expect(page.locator("#trace-events")).to_contain_text("pending")
            route = pending[0]
            response = page.request.post(route.request.url, data=route.request.post_data_json)
            route.fulfill(response=response)
            expect(page.locator("#run-status")).to_contain_text(
                "Published evaluation", timeout=15000
            )
            expect(page.locator("#run-progress")).to_be_hidden()
            expect(page.get_by_role("button", name="Load sunny fixture")).to_be_enabled()
            page.unroute("**/api/v1/pap/run")
            page.route("**/api/v1/pap/run", lambda route: route.abort())
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#run-status")).to_have_text("Run unavailable.")
            expect(page.locator("#action-notice")).to_be_in_viewport(ratio=1)
            expect(page.locator("#action-notice")).to_contain_text("Request failed")
            expect(page.locator(".session-history")).not_to_have_attribute("open", "")
        finally:
            page.close()


def test_live_selective_search_trace(browser, live_service, database, database_url):
    save_scenario(database, sunny_fixture())
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url + "/inspector")
            page.get_by_role("button", name="Load sunny fixture").click()
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#reasoning-mode")).to_have_text("linear", timeout=15000)
            page.get_by_role("button", name="Evaluate cloudy demo").click()
            expect(page.locator("#outcome-feedback")).to_contain_text("mean_solar_bias_kw")
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#reasoning-mode")).to_have_text("selective_tot", timeout=15000)
            page.get_by_role("tab", name="Trace", exact=True).click()
            expect(page.locator("#node-summary")).not_to_contain_text("undefined")
            page.get_by_text("Search branches and selection", exact=True).click()
            expect(page.locator("#search-trace")).to_contain_text('"beam_width": 2')
            expect(page.locator("#search-trace")).to_contain_text("prune_reason")
            expect(page.locator("#search-trace")).to_contain_text("selected_id")
            expect(page.locator("#profile-summary")).to_contain_text("10.600 kWh")
            page.get_by_role("button", name="Compare agent off / on").click()
            expect(page.locator("#model-calls")).to_have_text("3", timeout=30000)
            page.get_by_role("tab", name="Subagent", exact=True).click()
            for role in ("generator", "critic", "interpretation"):
                expect(page.locator("#agent-activity")).to_contain_text(f'"kind": "{role}"')
            expect(page.locator("#agent-comparison")).to_contain_text(
                '"same_available_power": true'
            )
        finally:
            page.close()


def test_live_forecast_and_inspector_share_run(
    browser, live_service, database_url, source_database
):
    with live_service(database_url) as url:
        page = browser.new_page(viewport={"width": 1440, "height": 1080})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            page.goto(url)
            page.locator("#source").select_option("mysolark")
            with page.expect_response("**/api/v1/pap/run") as response:
                page.get_by_role("button", name="Run PAP", exact=True).click()
            episode = response.value.json()
            expect(page.locator("#publication-status")).to_have_text("Published evaluation")
            expect(page.locator("#profile-summary")).to_be_in_viewport()
            expect(page.locator("#floor-value")).to_have_text("305.2 V")
            publication = page.request.get(f"{url}/api/v1/pap/{episode['publication_id']}").json()
            assert (
                float(page.locator("#power-value").inner_text())
                == publication["profile"]["intervals"][0]["available_kw"]
            )
            for width, height in [(1366, 768), (1440, 900), (1920, 1080)]:
                page.set_viewport_size({"width": width, "height": height})
                for selector in (
                    "#run-workflow",
                    "#forecast-chart",
                    "#agent-guidance",
                    "#view-inspector",
                    ".assumptions",
                ):
                    expect(page.locator(selector)).to_be_in_viewport(ratio=1)
                assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
            page.get_by_text("View the hourly numbers", exact=True).click()
            expect(page.locator("#profile-intervals tr")).to_have_count(12)
            page.get_by_role("link", name="Inspect this run", exact=True).click()
            assert page.url == f"{url}/inspector?episode={episode['episode_id']}"
            expect(page.locator("#graph-trace")).to_contain_text(episode["episode_id"])
            expect(page.get_by_role("tab")).to_have_count(6)
            page.set_viewport_size({"width": 1366, "height": 768})
            page.locator("#details-model-context summary").click()
            page.get_by_role("tabpanel").evaluate(
                "panel => { panel.scrollTop = panel.scrollHeight; }"
            )
            expect(page.get_by_role("tablist")).to_be_in_viewport(ratio=1)
            expect(page.locator("#details-evidence-context summary")).to_be_in_viewport()
            expect(page.locator("#run-workflow")).to_be_in_viewport(ratio=1)
            assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
            page.get_by_role("link", name="Forecast", exact=True).click()
            expect(page.locator("#publication-status")).to_have_text("Published evaluation")
            assert page.url == f"{url}/?episode={episode['episode_id']}"
            page.screenshot(path="test-results/pap-forecast.png", full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.screenshot(path="test-results/pap-forecast-mobile.png", full_page=True)
            page.reload()
            expect(page.locator("#floor-value")).to_have_text("305.2 V")
            assert errors == []
        finally:
            page.close()


def test_wing_replay_steps_and_inspector(browser, live_service, database_url, wing_history):
    with live_service(database_url) as url:
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        try:
            page.goto(url)
            page.locator("#source").select_option("mysolark")
            expect(page.locator("#wing option")).to_have_count(5)
            page.locator("#wing").select_option("1.21")
            page.locator("#time-window").select_option("week")
            page.locator("#replay-time").fill("2026-08-30T12:00")
            page.get_by_role("button", name="15 min", exact=True).click()
            page.get_by_role("button", name="Next replay time").click()
            expect(page.locator("#replay-time")).to_have_value("2026-08-30T12:15")
            with page.expect_response("**/api/v1/pap/run") as response:
                page.get_by_role("button", name="Run PAP", exact=True).click()
            episode = response.value.json()
            assert episode["selection"] == {"wing": "1.21", "replay_at": "2026-08-30T19:15:00Z"}
            expect(page.locator("#publication-status")).to_have_text("Historical replay")
            expect(page.locator("#power-value")).to_have_text("1.2")
            expect(page.locator("#floor-value")).to_have_text("313.2 V")
            expect(page.locator("#source-age")).to_contain_text("120 sec old at replay time")
            expect(page.locator("#view-inspector")).to_be_in_viewport(ratio=1)
            assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
            page.get_by_role("link", name="Inspect this run", exact=True).click()
            expect(page.locator("#selected-source")).to_contain_text("DW 1.21")
            expect(page.locator("#evaluate-outcome")).to_be_disabled()
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#run-status")).to_contain_text("Historical replay", timeout=15000)
            expect(page.locator("#graph-trace")).to_contain_text("2026-08-30T19:15:00Z")
            page.get_by_role("link", name="Forecast", exact=True).click()
            expect(page.locator("#wing")).to_have_value("1.21")
            expect(page.locator("#replay-time")).to_have_value("2026-08-30T12:15")
            page.get_by_role("button", name="1 hour", exact=True).click()
            expect(page.locator("#replay-time")).to_have_value("2026-08-30T12:00")
            page.get_by_role("button", name="Next replay time").click()
            expect(page.locator("#replay-time")).to_have_value("2026-08-30T13:00")
            page.locator("#replay-time").fill("2026-09-05T23:00")
            expect(page.locator("#next-time")).to_be_disabled()
            page.locator("#time-window").select_option("live")
            with page.expect_response("**/api/v1/pap/run") as response:
                page.get_by_role("button", name="Run PAP", exact=True).click()
            assert response.value.json()["selection"] == {"wing": "1.21", "replay_at": None}
            expect(page.locator("#publication-status")).to_have_text("Published evaluation")
            page.set_viewport_size({"width": 390, "height": 844})
            page.locator("#time-window").select_option("week")
            expect(page.locator("#step-quarter")).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        finally:
            page.close()


def test_live_forecast_withheld_clears_previous_output(
    browser, live_service, database, database_url, source_database
):
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url)
            page.locator("#source").select_option("mysolark")
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#publication-status")).to_have_text("Published evaluation")
            with database.session() as session:
                session.execute(
                    text("""UPDATE source_fixture.telemetry_snapshots
                    SET timestamp = timestamp - interval '10 minutes'""")
                )
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#publication-status")).to_have_text("Withheld")
            expect(page.locator("#valid-output")).to_be_hidden()
            expect(page.locator("#guidance-heading")).to_have_text("Why the result was withheld")
            expect(page.locator("#agent-guidance")).not_to_be_empty()
            page.reload()
            expect(page.locator("#publication-status")).to_have_text("Withheld")
            expect(page.locator("#source")).to_have_value("mysolark")
            page.get_by_role("link", name="Inspect this run", exact=True).click()
            expect(page.locator("#run-status")).to_contain_text("Withheld")
        finally:
            page.close()


def test_live_forecast_identifies_unavailable_model_advice(
    browser, live_service, database_url, monkeypatch
):
    monkeypatch.setenv("AGENT_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("ENABLE_INTERPRETATION_AGENT", "true")
    with live_service(database_url) as url:
        page = browser.new_page()
        try:
            page.goto(url)
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#publication-status")).to_have_text("Published evaluation")
            expect(page.locator("#agent-guidance")).to_contain_text(
                "Optional model advice was unavailable or rejected"
            )
            expect(page.locator("#confidence-value")).to_have_text("low")
            page.set_viewport_size({"width": 390, "height": 844})
            expect(page.locator(".assumptions")).to_be_visible()
        finally:
            page.close()
