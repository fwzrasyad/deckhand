# Makefile for Deckhand monorepo
# Targets defined in SRD Section 5.4

.PHONY: setup check lint fmt typecheck daemon-test mobile-test \
        protocol-check import-check run-daemon mock-daemon \
        package-daemon audit

PYTHON := python
DAEMON_DIR := daemon
MOBILE_DIR := mobile

# Detect the OS once. Windows virtualenvs use Scripts/, POSIX uses bin/.
ifeq ($(OS),Windows_NT)
VENV_BIN := .venv/Scripts
else
VENV_BIN := .venv/bin
endif

# ── Setup ──────────────────────────────────────────────────────────────────────

setup:
	@echo "==> Setting up daemon venv..."
	cd $(DAEMON_DIR) && $(PYTHON) -m venv .venv
	cd $(DAEMON_DIR) && $(VENV_BIN)/pip install --upgrade pip
	cd $(DAEMON_DIR) && $(VENV_BIN)/pip install -e ".[dev]"
	@echo "==> Setting up mobile dependencies..."
	cd $(MOBILE_DIR) && flutter pub get
	@echo "==> Installing pre-commit hooks..."
	pre-commit install
	@echo "==> Setup complete."

# ── Master check (everything) ──────────────────────────────────────────────────

check: lint fmt typecheck import-check daemon-test mobile-test protocol-check
	@echo "==> All checks passed."

# ── Lint ───────────────────────────────────────────────────────────────────────

lint:
	@echo "==> Ruff lint..."
	cd $(DAEMON_DIR) && $(VENV_BIN)/ruff check src/ tests/
	@echo "==> Dart analyze..."
	cd $(MOBILE_DIR) && dart analyze --fatal-infos lib/ test/

# ── Format ─────────────────────────────────────────────────────────────────────

fmt:
	@echo "==> Ruff format check..."
	cd $(DAEMON_DIR) && $(VENV_BIN)/ruff format --check src/ tests/
	@echo "==> Dart format check..."
	cd $(MOBILE_DIR) && dart format --set-exit-if-changed lib/ test/

# ── Type check ─────────────────────────────────────────────────────────────────

typecheck:
	@echo "==> mypy --strict..."
	cd $(DAEMON_DIR) && $(VENV_BIN)/mypy src/

# ── Import linter ──────────────────────────────────────────────────────────────

import-check:
	@echo "==> import-linter (daemon layer contracts)..."
	cd $(DAEMON_DIR) && $(VENV_BIN)/lint-imports
	@echo "==> check_imports.py (mobile layer contracts)..."
	$(PYTHON) tools/scripts/check_imports.py $(MOBILE_DIR)/lib
	@echo "==> check_imports.py tests..."
	$(PYTHON) -m pytest tools/tests -q

# ── Tests ──────────────────────────────────────────────────────────────────────

daemon-test:
	@echo "==> pytest daemon..."
	cd $(DAEMON_DIR) && $(VENV_BIN)/pytest tests/ -v --tb=short \
	    --cov=src/deckhand --cov-report=term-missing

mobile-test:
	@echo "==> Flutter tests..."
	cd $(MOBILE_DIR) && flutter test --coverage

# ── Protocol ───────────────────────────────────────────────────────────────────

protocol-check:
	@echo "==> Validating protocol schemas and fixtures..."
	$(PYTHON) tools/scripts/validate_protocol.py \
	    protocol/schemas protocol/fixtures

# ── Run ────────────────────────────────────────────────────────────────────────

run-daemon:
	@echo "==> Starting deckhand daemon..."
	cd $(DAEMON_DIR) && $(VENV_BIN)/python -m deckhand serve

mock-daemon:
	@echo "==> Starting mock daemon..."
	$(PYTHON) tools/mock_daemon/main.py

# ── Package ────────────────────────────────────────────────────────────────────

package-daemon:
	@echo "==> Building PyInstaller bundle..."
	cd $(DAEMON_DIR) && $(VENV_BIN)/pyinstaller packaging/pyinstaller.spec

# ── Security audit ─────────────────────────────────────────────────────────────

audit:
	@echo "==> pip-audit..."
	cd $(DAEMON_DIR) && $(VENV_BIN)/pip-audit
	@echo "==> gitleaks..."
	gitleaks detect --source . --no-git
	@echo "==> bandit..."
	cd $(DAEMON_DIR) && $(VENV_BIN)/bandit -r src/ -ll
