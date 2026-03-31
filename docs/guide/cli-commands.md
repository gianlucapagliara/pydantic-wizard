# CLI Commands

## `pydantic-wizard new`

Create a new configuration file interactively.

```bash
pydantic-wizard new <MODEL_FQN> [--output FILE]
```

## `pydantic-wizard edit`

Edit an existing YAML configuration file.

```bash
pydantic-wizard edit <CONFIG_FILE>
```

## `pydantic-wizard validate`

Validate a configuration file against a Pydantic model.

```bash
pydantic-wizard validate <CONFIG_FILE>
```

## `pydantic-wizard show-schema`

Display the schema for a Pydantic model.

```bash
pydantic-wizard show-schema <MODEL_FQN>
```

## `pydantic-wizard web`

Launch the Streamlit-based web UI for visual configuration. Requires the `[web]` extra.

```bash
pydantic-wizard web
```

The web UI provides four pages:

- **New Config** — create a configuration from scratch by entering a model class name
- **Edit Config** — upload and modify an existing YAML file
- **Validate** — upload a YAML file and validate it against its model
- **Show Schema** — display a model's fields, types, and defaults
