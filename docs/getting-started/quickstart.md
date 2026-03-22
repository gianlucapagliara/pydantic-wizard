# Quick Start

## Define a Pydantic model

```python
from pydantic import BaseModel

class AppConfig(BaseModel):
    name: str
    debug: bool = False
    port: int = 8080
```

## Create a configuration interactively

```bash
pydantic-wizard new myapp.config.AppConfig
```

## Edit an existing configuration

```bash
pydantic-wizard edit config.yaml
```

## Validate a configuration

```bash
pydantic-wizard validate config.yaml --model myapp.config.AppConfig
```
