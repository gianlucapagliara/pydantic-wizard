# pydantic-wizard

Interactive wizard-style CLI for configuring [Pydantic v2](https://docs.pydantic.dev/) models, with YAML serialization.

Point it at any `BaseModel` subclass and it will walk you through every field — with type-aware prompts, constraint validation, and nested model support — then save the result as a clean YAML file.

## Features

- **Zero boilerplate** — works with any Pydantic v2 `BaseModel`, no registration needed
- **Type-aware prompts** — booleans get yes/no, enums get dropdowns, nested models recurse automatically
- **Constraint enforcement** — respects `ge`, `le`, `gt`, `lt` and other Pydantic field validators
- **15+ built-in type handlers** — scalars, `Decimal`, `Enum`, `Literal`, `datetime`, `Optional`, `list`, `set`, `dict`, `Union`, nested models
- **YAML round-trip** — serialize with metadata, load back, edit, and re-save
- **Interactive validation** — on error, re-prompts only the failing fields
- **Extensible** — register custom `TypeHandler` implementations for domain-specific types
- **Rich terminal output** — field panels, summary tables, and colored messages via [Rich](https://github.com/Textualize/rich)

## Installation

```bash
pip install pydantic-wizard
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add pydantic-wizard
```

## Quick Start

### Define a model

```python
# myapp/config.py
from decimal import Decimal
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    host: str = Field(description="Database hostname")
    port: int = Field(default=5432, ge=1, le=65535)
    name: str = Field(description="Database name")
    pool_size: int = Field(default=10, ge=1)
    timeout: Decimal = Field(default=Decimal("30.0"), ge=0)
    ssl_enabled: bool = Field(default=True)
```

### Run the wizard from the CLI

```bash
pydantic-wizard new myapp.config.DatabaseConfig -o db.yaml
```

The wizard will prompt you for each field with type-appropriate inputs, validate the result, and save to `db.yaml`.

### Or use it programmatically

```python
from pydantic_wizard import prompt_model, serialize_to_yaml, validate_and_fix
from myapp.config import DatabaseConfig
from pathlib import Path

# Interactive prompt for all fields
data = prompt_model(DatabaseConfig)

# Validate (re-prompts on errors)
instance = validate_and_fix(DatabaseConfig, data)

# Save to YAML
serialize_to_yaml(data, DatabaseConfig, Path("db.yaml"), model_name="database")
```

## CLI Commands

### `new` — Create a configuration

```bash
pydantic-wizard new <MODEL_FQN> [--output, -o PATH]
```

Walks through every field interactively, validates, and saves to YAML.

### `edit` — Edit an existing configuration

```bash
pydantic-wizard edit <CONFIG_FILE> [--output, -o PATH]
```

Loads an existing YAML file and re-runs the wizard with current values as defaults.

### `validate` — Validate a configuration

```bash
pydantic-wizard validate <CONFIG_FILE> [--model, -m FQN]
```

Validates a YAML file against its Pydantic model. The model class is resolved from YAML metadata or the `--model` flag.

### `show-schema` — Show model schema

```bash
pydantic-wizard show-schema <MODEL_FQN>
```

Displays a formatted table of all fields, types, defaults, and descriptions.

## Supported Types

| Category | Types |
|----------|-------|
| **Scalars** | `str`, `int`, `float`, `bool`, `Decimal` |
| **Enums & Literals** | `Enum` subclasses, `Literal["a", "b", "c"]` |
| **Date & Time** | `datetime`, `time`, `timedelta` |
| **Optional** | `T \| None`, `Optional[T]` |
| **Collections** | `list[T]`, `set[T]`, `dict[K, V]` |
| **Unions** | `A \| B \| C` (type selection prompt) |
| **Nested Models** | Any `BaseModel` subclass (recursive prompting) |

## Programmatic API

### Introspection

```python
from pydantic_wizard import introspect_model, FieldSpec

specs: list[FieldSpec] = introspect_model(DatabaseConfig)
for spec in specs:
    print(f"{spec.name}: {spec.inner_type}, required={spec.is_required}")
```

### Custom Type Handlers

Register custom handlers for domain-specific types:

```python
from pydantic_wizard import TypeHandlerRegistry, prompt_model
from pydantic_wizard.type_handlers import TypeHandler

class MoneyHandler:
    def can_handle(self, spec):
        return spec.inner_type is Money

    def prompt(self, spec, default=None):
        raw = questionary.text(f"  {spec.name} (e.g. 100.00 USD):").ask()
        return Money.parse(raw)

    def serialize(self, value):
        return str(value)

    def deserialize(self, raw, spec):
        return Money.parse(raw)

# Use the custom registry
registry = TypeHandlerRegistry()
registry.register(MoneyHandler())  # inserted at front, takes priority
data = prompt_model(MyConfig, registry=registry)
```

## YAML Output Format

Generated YAML files include metadata for round-trip support:

```yaml
_metadata:
  model_type: DatabaseConfig
  configuration_class: myapp.config.DatabaseConfig
  version: 0.1.0
configuration:
  host: localhost
  port: 5432
  name: mydb
  pool_size: 10
  timeout: "30.0"
  ssl_enabled: true
```

- **Decimals** are serialized as quoted strings to preserve precision
- **Enums** are serialized as their `.value`
- **Sets** are serialized as sorted lists
- **Datetimes** use ISO 8601 format

## License

MIT
