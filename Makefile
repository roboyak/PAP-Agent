export UV_CACHE_DIR := $(CURDIR)/.cache/uv
export PLAYWRIGHT_BROWSERS_PATH := $(CURDIR)/.cache/playwright

.NOTPARALLEL: verify
.PHONY: setup db-up db-down migrate seed dev format format-check lint test e2e verify
.PHONY: bootstrap run demo verify-mac memory-index

bootstrap:
	bash scripts/bootstrap_mac.sh

run:
	bash scripts/run_local.sh

verify-mac:
	bash scripts/verify_local.sh

demo: db-up migrate seed
	PAP_PROFILE=macmini-replay uv run --locked python -m pap_agent.demo

setup:
	uv sync --locked
	uv run --locked playwright install chromium

db-up:
	bash scripts/db.sh up

db-down:
	bash scripts/db.sh down

migrate:
	uv run --locked alembic upgrade head

seed:
	uv run --locked python -m pap_agent.seed

memory-index:
	uv run --locked python -m pap_agent.memory

dev:
	uv run --locked uvicorn pap_agent.main:app --host 127.0.0.1 --port 8000

format:
	uv run --locked ruff format src tests migrations scripts

format-check:
	uv run --locked ruff format --check src tests migrations scripts

lint:
	uv run --locked ruff check src tests migrations scripts

test:
	uv run --locked pytest tests --ignore=tests/e2e

e2e:
	uv run --locked pytest tests/e2e

verify:
	$(MAKE) format-check lint
	$(MAKE) db-up
	$(MAKE) migrate
	$(MAKE) seed
	$(MAKE) test
	$(MAKE) e2e
