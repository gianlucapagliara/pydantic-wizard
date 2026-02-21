from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pydantic_wizard.introspection import FieldSpec, get_type_display_name

console = Console()


def display_field_header(spec: FieldSpec, path: str = "") -> None:
    """Show a Rich panel with field metadata before prompting."""
    breadcrumb = f"{path} > {spec.name}" if path else spec.name
    type_name = get_type_display_name(spec.annotation)

    lines: list[str] = [f"[bold]{type_name}[/bold]"]
    if spec.description:
        lines.append(f"[dim]{spec.description}[/dim]")
    if spec.constraints:
        parts = [f"{k}={v}" for k, v in spec.constraints.items()]
        lines.append(f"[dim]Constraints: {', '.join(parts)}[/dim]")
    if not spec.is_required:
        default_display = _format_default(spec)
        lines.append(f"[dim]Optional (default: {default_display})[/dim]")

    content = "\n".join(lines)
    console.print(Panel(content, title=breadcrumb, border_style="cyan", expand=False))


def _format_default(spec: FieldSpec) -> str:
    if spec.default is not None and str(spec.default) != "PydanticUndefined":
        return repr(spec.default)
    if spec.default_factory is not None:
        try:
            return repr(spec.default_factory())
        except Exception:
            return "<factory>"
    return "None"


def display_model_header(model_class: type[BaseModel], path: str = "") -> None:
    """Show a header when entering a nested model."""
    title = path if path else model_class.__name__
    console.print(f"\n[bold cyan]--- {title} ({model_class.__name__}) ---[/bold cyan]")


def display_summary_table(
    data: dict[str, Any], model_name: str = "Configuration"
) -> None:
    """Display a summary table of collected values."""
    table = Table(title=f"{model_name} Summary", show_lines=True)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    for key, value in data.items():
        table.add_row(key, _truncate(repr(value), 80))

    console.print(table)


def display_model_list(
    models: dict[str, type[BaseModel]],
) -> None:
    """Display a table of available model types."""
    table = Table(title="Available Model Types")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Configuration Class")
    table.add_column("Fields", justify="right")

    for i, (name, config_cls) in enumerate(sorted(models.items()), 1):
        field_count = len(config_cls.model_fields)
        table.add_row(str(i), name, config_cls.__name__, str(field_count))

    console.print(table)


def display_schema(model_class: type[BaseModel], specs: list[FieldSpec]) -> None:
    """Display the configuration schema for a model."""
    table = Table(title=f"Schema: {model_class.__name__}", show_lines=True)
    table.add_column("Field", style="bold")
    table.add_column("Type")
    table.add_column("Required", justify="center")
    table.add_column("Default")
    table.add_column("Description")

    for spec in specs:
        type_name = get_type_display_name(spec.annotation)
        required = "yes" if spec.is_required else "no"
        default_str = _format_default(spec) if not spec.is_required else "-"
        desc = spec.description or ""
        if not spec.is_init:
            required = "[dim]auto[/dim]"

        table.add_row(spec.name, type_name, required, default_str, _truncate(desc, 50))

    console.print(table)


def display_validation_errors(errors: list[Any]) -> None:
    """Display Pydantic validation errors."""
    console.print("\n[bold red]Validation Errors:[/bold red]")
    for err in errors:
        loc = " > ".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "Unknown error")
        console.print(f"  [red]{loc}[/red]: {msg}")


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"\n[bold green]{message}[/bold green]")


def display_error(message: str) -> None:
    """Display an error message."""
    console.print(f"\n[bold red]{message}[/bold red]")


def display_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"\n[bold yellow]{message}[/bold yellow]")


def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[: max_len - 3] + "..."
