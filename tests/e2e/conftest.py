import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager

import httpx
import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture
def live_service(tmp_path):
    """Start a real Uvicorn process on a reserved loopback socket (macOS/Linux)."""

    @contextmanager
    def start(database_url):
        with socket.socket() as listener, (tmp_path / "service.log").open("w+") as log:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            url = f"http://127.0.0.1:{listener.getsockname()[1]}"
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "pap_agent.main:app",
                    "--fd",
                    str(listener.fileno()),
                ],
                pass_fds=(listener.fileno(),),
                env={**os.environ, "DATABASE_URL": database_url},
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 15
                with httpx.Client(base_url=url, timeout=1, trust_env=False) as client:
                    while time.monotonic() < deadline:
                        if process.poll() is not None:
                            break
                        try:
                            if client.get("/api/v1/version").status_code == 200:
                                break
                        except httpx.TransportError:
                            pass
                        time.sleep(0.1)
                    else:
                        pytest.fail("Local service did not become available within 15 seconds")
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(f"Local service exited: {log.read()}")
                yield url
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    return start
