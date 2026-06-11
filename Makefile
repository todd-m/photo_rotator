PYTHON ?= python3
VENV   := .venv
BIN    := $(VENV)/bin

.PHONY: help venv install run test lint audit ci clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

venv: ## Create a virtual environment
	$(PYTHON) -m venv $(VENV)

install: venv ## Install project dependencies
	$(BIN)/pip install -r requirements.txt

# Usage: make run IN=/path/to/photos OUT=output.pdf
run: ## Build a PDF from IN=<dir> to OUT=<file>
	$(BIN)/python photos_to_pdf.py "$(IN)" "$(OUT)"

test: ## Run tests (coverage gate lives in pyproject.toml)
	$(BIN)/python -m pytest

lint: ## Run ruff lint + format check
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

audit: ## Scan dependencies for known vulnerabilities
	$(BIN)/pip-audit -r requirements.txt

ci: test lint audit ## Run tests, lint, and security audit

clean: ## Remove virtual env and caches
	rm -rf $(VENV) __pycache__ .pytest_cache .ruff_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
