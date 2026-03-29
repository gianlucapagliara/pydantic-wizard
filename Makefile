UV ?= uv
PACKAGE ?= pydantic_wizard

VERSION := $(shell grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)"/\1/')

# ── Help ────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Setup ───────────────────────────────────────────────────────────
.PHONY: install
install: ## Install all dependencies (frozen lockfile) and set up hooks
	$(UV) sync --frozen --group dev
	$(UV) run pre-commit install

.PHONY: sync
sync: ## Install all dependencies (allow lockfile updates)
	$(UV) sync --group dev

.PHONY: precommit-install
precommit-install: ## Set up pre-commit and pre-push hooks
	$(UV) run pre-commit install

# ── Quality ─────────────────────────────────────────────────────────
.PHONY: lint
lint: ## Run ruff linter
	$(UV) run ruff check .

.PHONY: format
format: ## Auto-format code with ruff
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

.PHONY: format-check
format-check: ## Check formatting without modifying files
	$(UV) run ruff format --check .

.PHONY: type-check
type-check: ## Run mypy type checking
	$(UV) run mypy --strict $(PACKAGE)/

.PHONY: test
test: ## Run test suite
	$(UV) run pytest

.PHONY: check
check: lint format-check type-check test ## Run all quality checks

.PHONY: precommit-run
precommit-run: ## Run pre-commit hooks on all files
	$(UV) run pre-commit run --all-files

# ── Version ─────────────────────────────────────────────────────────
.PHONY: version
version: ## Print current version
	@echo $(VERSION)

# ── Release ─────────────────────────────────────────────────────────
.PHONY: release
release: ## Release a new version (BUMP=patch|minor|major, YES=1 to skip confirm)
	@scripts/release.sh $(if $(YES),--yes) $(BUMP)

# ── Docs ────────────────────────────────────────────────────────────
.PHONY: docs-serve
docs-serve: ## Serve documentation locally with live reload
	$(UV) run --group docs mkdocs serve

.PHONY: docs-build
docs-build: ## Build documentation site
	$(UV) run --group docs mkdocs build

.PHONY: docs-deploy
docs-deploy: ## Deploy documentation to GitHub Pages
	$(UV) run --group docs mkdocs gh-deploy --force
