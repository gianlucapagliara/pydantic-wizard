"""Generic CLI for interactively configuring any Pydantic v2 model."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import questionary
import typer
from pydantic import ValidationError

from pydantic_wizard.display import (
    console,
    display_error,
    display_schema,
    display_success,
    display_summary_table,
    display_validation_errors,
)
from pydantic_wizard.introspection import introspect_model
from pydantic_wizard.prompts import prompt_model
from pydantic_wizard.serialization import (
    load_from_yaml,
    resolve_config_class,
    serialize_to_yaml,
)
from pydantic_wizard.validation import validate_and_fix

app = typer.Typer(
    name="pydantic-wizard",
    help="Interactive wizard-style CLI for configuring Pydantic v2 models.",
    no_args_is_help=True,
)


@app.command("new")
def new_config(
    model_fqn: Annotated[
        str,
        typer.Argument(
            help="Fully qualified model class name (e.g. myapp.config.DatabaseConfig)"
        ),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output YAML file path"),
    ] = Path("config.yaml"),
) -> None:
    """Create a new configuration interactively for a Pydantic model."""
    try:
        config_class = resolve_config_class(model_fqn)
    except (ImportError, ValueError, AttributeError) as e:
        display_error(f"Failed to resolve model class: {e}")
        raise typer.Exit(1) from e

    console.print(f"\n[bold]Configuring: {config_class.__name__}[/bold]")
    console.print(f"[dim]Class: {model_fqn}[/dim]\n")

    # Run the wizard
    data = prompt_model(config_class)

    # Validate
    instance = validate_and_fix(config_class, data)
    if instance is None:
        display_error("Configuration not saved due to validation errors.")
        raise typer.Exit(1)

    # Summary
    display_summary_table(data, config_class.__name__)

    # Confirm save
    should_save = questionary.confirm("Save configuration?", default=True).ask()
    if not should_save:
        display_error("Configuration not saved.")
        raise typer.Exit(0)

    serialize_to_yaml(data, config_class, output, model_name=config_class.__name__)
    display_success(f"Configuration saved to {output}")


@app.command("edit")
def edit_config(
    config_file: Annotated[
        Path,
        typer.Argument(help="Path to existing YAML config"),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output path (default: overwrite)"),
    ] = None,
) -> None:
    """Edit an existing YAML configuration."""
    if not config_file.exists():
        display_error(f"File not found: {config_file}")
        raise typer.Exit(1)

    model_name, config_fqn, data = load_from_yaml(config_file)

    if not config_fqn:
        display_error("No configuration class found in YAML metadata.")
        raise typer.Exit(1)

    try:
        config_class = resolve_config_class(config_fqn)
    except (ImportError, ValueError, AttributeError) as e:
        display_error(f"Failed to resolve configuration class: {e}")
        raise typer.Exit(1) from e

    console.print(f"\n[bold]Editing: {model_name or config_class.__name__}[/bold]")
    console.print(f"[dim]Class: {config_class.__name__}[/dim]\n")

    # Re-run wizard with existing values as defaults
    new_data = prompt_model(config_class, defaults=data)

    # Validate
    instance = validate_and_fix(config_class, new_data)
    if instance is None:
        display_error("Configuration not saved due to validation errors.")
        raise typer.Exit(1)

    display_summary_table(new_data, config_class.__name__)

    should_save = questionary.confirm("Save configuration?", default=True).ask()
    if not should_save:
        display_error("Configuration not saved.")
        raise typer.Exit(0)

    output_path = output or config_file
    serialize_to_yaml(
        new_data,
        config_class,
        output_path,
        model_name=model_name or config_class.__name__,
    )
    display_success(f"Configuration saved to {output_path}")


@app.command("validate")
def validate_config_cmd(
    config_file: Annotated[
        Path,
        typer.Argument(help="Path to YAML config to validate"),
    ],
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="Model class FQN to validate against"),
    ] = None,
) -> None:
    """Validate a YAML config against its Pydantic model."""
    if not config_file.exists():
        display_error(f"File not found: {config_file}")
        raise typer.Exit(1)

    model_name, config_fqn, data = load_from_yaml(config_file)

    # Determine which class to validate against
    fqn = model or config_fqn
    if not fqn:
        display_error(
            "No model class specified and no metadata in YAML. "
            "Use --model to specify the model class FQN."
        )
        raise typer.Exit(1)

    try:
        config_class = resolve_config_class(fqn)
    except (ImportError, ValueError, AttributeError) as e:
        display_error(f"Failed to resolve configuration class: {e}")
        raise typer.Exit(1) from e

    try:
        config_class.model_validate(data)
        display_success(
            f"Valid {config_class.__name__} configuration"
            + (f" for {model_name}" if model_name else "")
        )
    except ValidationError as e:
        display_validation_errors(e.errors())
        raise typer.Exit(1) from e


@app.command("show-schema")
def show_schema(
    model_fqn: Annotated[
        str,
        typer.Argument(
            help="Fully qualified model class name (e.g. myapp.config.DatabaseConfig)"
        ),
    ],
) -> None:
    """Show the configuration schema for a Pydantic model."""
    try:
        config_class = resolve_config_class(model_fqn)
    except (ImportError, ValueError, AttributeError) as e:
        display_error(f"Failed to resolve model class: {e}")
        raise typer.Exit(1) from e

    specs = introspect_model(config_class)
    display_schema(config_class, specs)


if __name__ == "__main__":
    app()
