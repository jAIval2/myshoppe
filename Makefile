# MyShoppe — bootstrap, run and verify.
#
#   make            show help
#   make setup      install everything and prepare the database
#   make run        start API + worker + web (Ctrl-C stops them)
#   make test       backend + browser suites
#
# Named your 3.13 interpreter differently?  make setup SYSTEM_PYTHON=python3

SHELL := /bin/bash
.DEFAULT_GOAL := help

ROOT   := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
VENV   := $(ROOT)/.venv
PY     := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip
ALEMBIC:= $(VENV)/bin/alembic
PYTEST := $(VENV)/bin/pytest
RUFF   := $(VENV)/bin/ruff
WEB    := $(ROOT)/web
SYSTEM_PYTHON ?= python3.13
BREW_BIN := $(shell command -v /opt/homebrew/bin/brew || command -v /usr/local/bin/brew || command -v brew)

.PHONY: help bootstrap setup doctor env venv deps db db-docker migrate seed assets \
        run test test-backend test-web test-web-install lint typecheck \
        build types-api check clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

bootstrap: ## New Mac: install Homebrew, Python, Node, Postgres, FFmpeg, then the project
	@set -e; \
	BREW=""; PREFIX=""; ARCH="$$(uname -m)"; \
	if [ -x /opt/homebrew/bin/brew ]; then BREW=/opt/homebrew/bin/brew; PREFIX=/opt/homebrew; \
	elif [ -x /usr/local/bin/brew ]; then BREW=/usr/local/bin/brew; PREFIX=/usr/local; fi; \
	if [ -z "$$BREW" ]; then \
	  echo "📦 Installing Homebrew (may ask for your password)..."; \
	  NONINTERACTIVE=1 /bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; \
	  if [ "$$ARCH" = "arm64" ]; then PREFIX=/opt/homebrew; else PREFIX=/usr/local; fi; \
	  BREW="$$PREFIX/bin/brew"; \
	  if [ "$$PREFIX" = "/opt/homebrew" ]; then LINE='eval "$$(/opt/homebrew/bin/brew shellenv)"'; \
	  else LINE='eval "$$(/usr/local/bin/brew shellenv)"'; fi; \
	  grep -qxF "$$LINE" "$$HOME/.zprofile" 2>/dev/null || printf '\n%s\n' "$$LINE" >> "$$HOME/.zprofile"; \
	  echo "✅ Appended the initialization code to ~/.zprofile so it works in future terminal windows"; \
	fi; \
	eval "$$($$BREW shellenv)"; \
	echo "✅ Activated instantly in the current running script session"; \
	command -v python3.13 >/dev/null 2>&1 || { echo "⚙️  Installing Python..."; brew install python; }; \
	command -v node       >/dev/null 2>&1 || { echo "⚙️  Installing Node.js..."; brew install node; }; \
	command -v npm        >/dev/null 2>&1 || { echo "⚙️  Installing Node.js (npm)..."; brew install node; }; \
	command -v initdb     >/dev/null 2>&1 || { \
	  echo "⚙️  Installing PostgreSQL..."; brew install postgresql@18; \
	  PG_LINE='export PATH="'$$(brew --prefix postgresql@18)'/bin:$$PATH"'; \
	  grep -qxF "$$PG_LINE" "$$HOME/.zprofile" 2>/dev/null || printf '%s\n' "$$PG_LINE" >> "$$HOME/.zprofile"; \
	  export PATH="$$(brew --prefix postgresql@18)/bin:$$PATH"; }; \
	command -v ffmpeg     >/dev/null 2>&1 || { echo "⚙️  Installing FFmpeg..."; brew install ffmpeg; }; \
	echo "🔧 Toolchain ready"; \
	$(MAKE) setup
	@echo
	@echo "🎉 Setup finished! Start the store with:  make run"

setup: doctor env deps db migrate seed ## Full bootstrap on a fresh machine
	@echo
	@echo "Ready. Start everything with:  make run"

doctor: ## Check the required toolchain
	@fail=0; \
	for tool in $(SYSTEM_PYTHON) node npm; do \
	  if command -v $$tool >/dev/null 2>&1; then echo "  ok       $$tool"; \
	  else echo "  MISSING  $$tool"; fail=1; fi; \
	done; \
	for tool in initdb pg_ctl psql createdb ffmpeg ffprobe; do \
	  if command -v $$tool >/dev/null 2>&1; then echo "  ok       $$tool"; \
	  else echo "  warn     $$tool   (needed for 'make db' / video uploads)"; fi; \
	done; \
	if [ $$fail -ne 0 ]; then \
	  echo; echo "Install the missing tools above, then run 'make setup' again."; exit 1; \
	fi
	@if ! command -v initdb >/dev/null 2>&1; then \
	  echo; echo "No local PostgreSQL tooling found — use 'make setup' with Docker:"; \
	  echo "  make env deps db-docker migrate seed"; \
	fi

env: ## Create .env from .env.example if it does not exist
	@if [ -f $(ROOT)/.env ]; then echo ".env already exists — left untouched"; \
	else cp $(ROOT)/.env.example $(ROOT)/.env; echo "Created .env from .env.example"; fi

venv: ## Create the Python 3.13 virtual environment
	@test -d $(VENV) || $(SYSTEM_PYTHON) -m venv $(VENV)
	@$(PY) -c 'import sys; assert sys.version_info[:2]==(3,13), "Python 3.13 required, found %d.%d" % sys.version_info[:2]'

deps: venv ## Install backend and web dependencies
	@cd $(ROOT) && $(PIP) install --upgrade pip
	@cd $(ROOT) && $(PIP) install -r backend/requirements.lock
	@npm --prefix $(WEB) ci
	@echo "Dependencies installed"

db: ## Start the isolated native PostgreSQL cluster and create databases
	@cd $(ROOT) && $(SYSTEM_PYTHON) scripts/database.py

db-docker: ## Start PostgreSQL with Docker instead of the native cluster
	@cd $(ROOT) && docker compose up -d postgres
	@until cd $(ROOT) && docker compose exec -T postgres pg_isready -U myshoppe >/dev/null 2>&1; do sleep 1; done
	@cd $(ROOT) && docker compose exec -T postgres createdb -U myshoppe myshoppe_test 2>/dev/null || true
	@echo "Docker PostgreSQL ready on 127.0.0.1:55432"

migrate: ## Apply database migrations
	@cd $(ROOT)/backend && $(ALEMBIC) upgrade head

seed: ## Load the development catalogue (development databases only)
	@cd $(ROOT)/backend && $(PY) -m app.seed

assets: ## Re-download media and fonts (requires internet)
	@cd $(ROOT) && $(SYSTEM_PYTHON) scripts/fetch-fonts.py
	@cd $(ROOT) && $(SYSTEM_PYTHON) scripts/fetch-media.py

run: ## Start API, worker and web together
	@cd $(ROOT) && $(SYSTEM_PYTHON) scripts/dev.py

test: test-backend test-web ## Run backend and browser test suites

test-backend: ## Run the backend suite (only touches myshoppe_test)
	@cd $(ROOT)/backend && $(PYTEST) -q

test-web-install: ## Install the Playwright Chrome browser
	@cd $(WEB) && npx playwright install --with-deps chrome

test-web: ## Run the Playwright browser journeys
	@cd $(WEB) && npm test

lint: ## Lint the backend with Ruff
	@$(RUFF) check $(ROOT)/backend

typecheck: ## Type-check the web application
	@cd $(WEB) && npm run typecheck

build: ## Build the optimised web application
	@cd $(WEB) && npm run build

types-api: ## Regenerate web API types from the running API
	@cd $(WEB) && npm run types:api

check: lint typecheck test-backend ## Lint + typecheck + backend tests (CI parity)

clean: ## Remove build artefacts and caches (keeps the database and media)
	@rm -rf $(WEB)/.next $(WEB)/test-results $(WEB)/playwright-report
	@find $(ROOT)/backend -type d -name __pycache__ -prune -exec rm -rf {} +
	@rm -rf $(ROOT)/backend/.pytest_cache $(ROOT)/backend/.ruff_cache $(ROOT)/.ruff_cache
	@echo "Cleaned"