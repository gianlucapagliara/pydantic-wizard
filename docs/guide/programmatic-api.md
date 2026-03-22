# Programmatic API

Pydantic Wizard can be used programmatically in addition to the CLI.

## Introspection

```python
from pydantic_wizard.introspection import inspect_model

fields = inspect_model(MyModel)
```

## Serialization

```python
from pydantic_wizard.serialization import serialize_config, deserialize_config

# Save
serialize_config(model_instance, "config.yaml")

# Load
instance = deserialize_config("config.yaml", MyModel)
```

## Validation

```python
from pydantic_wizard.validation import validate_config

errors = validate_config("config.yaml", MyModel)
```
