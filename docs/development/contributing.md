# Contributing

## Development Setup

```bash
git clone https://github.com/gianlucapagliara/pydantic-wizard.git
cd pydantic-wizard
uv sync
uv run pre-commit install
```

## Running Tests

```bash
uv run pytest tests/
```

## Linting

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict pydantic_wizard/
```

## Releasing

```bash
./scripts/release.sh [major|minor|patch]
```
