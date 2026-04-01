"""Recursive model form rendering for Streamlit."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from pydantic_wizard.introspection import introspect_model
from pydantic_wizard.streamlit_ui.widgets import render_field


def render_model_form(
    model_class: type[BaseModel],
    defaults: dict[str, Any] | None = None,
    key_prefix: str = "",
) -> dict[str, Any]:
    """Render a complete Streamlit form for a Pydantic model.

    Args:
        model_class: The Pydantic BaseModel subclass to render.
        defaults: Optional dict of default values to pre-populate the form.
        key_prefix: Widget key prefix for nested model support.

    Returns:
        Dict of field name -> current widget value.
    """
    defaults = defaults or {}
    specs = introspect_model(model_class)
    data: dict[str, Any] = {}

    for spec in specs:
        if not spec.is_init:
            continue
        default = defaults.get(spec.name, spec.default)
        # Use default_factory if no explicit default
        if default is None and spec.default_factory is not None:
            default = spec.default_factory()
        data[spec.name] = render_field(spec, key_prefix, default)

    return data
