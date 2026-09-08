from playwright.sync_api import expect


def test_calibration_maintenance_keeps_saved_run_fixed(browser, live_service, database_url):
    with live_service(database_url) as url:
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        try:
            page.goto(url + "/inspector")
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#run-status")).to_contain_text("Published evaluation")
            saved_url = page.url
            page.get_by_role("tab", name="Memory", exact=True).click()
            expect(page.locator("#run-calibration-summary")).to_contain_text("No measured outcome")
            page.get_by_text("Current calibration maintenance", exact=True).click()
            page.get_by_role("button", name="Check current calibration", exact=True).click()
            expect(page.locator("#calibration-summary")).to_contain_text("Threshold review needed")
            expect(page.locator("#calibration-summary")).to_contain_text("ECE unavailable")
            expect(page.locator("#calibration-summary")).to_contain_text("0/20 recent outcomes")
            page.get_by_role("button", name="Evaluate cloudy demo", exact=True).click()
            expect(page.locator("#calibration-summary")).to_contain_text("2.000 kW")
            expect(page.locator("#calibration-summary")).to_contain_text("1/20 recent outcomes")
            expect(page.locator("#run-calibration-summary")).to_contain_text("No measured outcome")
            assert page.url == saved_url
            page.get_by_role("button", name="Run PAP", exact=True).click()
            expect(page.locator("#run-calibration-summary")).to_contain_text(
                "point-error-v2-", timeout=15000
            )
            recorded = page.locator("#run-calibration-summary").inner_text()
            page.get_by_role("tab", name="Memory", exact=True).click()
            page.get_by_role("button", name="Check current calibration", exact=True).click()
            expect(page.locator("#run-calibration-summary")).to_have_text(recorded)
            page.reload()
            page.get_by_role("tab", name="Memory", exact=True).click()
            expect(page.locator("#run-calibration-summary")).to_have_text(recorded)
            expect(page.get_by_role("tablist")).to_be_in_viewport(ratio=1)
            assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
            page.screenshot(path="test-results/pap-calibration.png", full_page=True)
        finally:
            page.close()
