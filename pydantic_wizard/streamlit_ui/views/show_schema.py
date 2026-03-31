"""Show Schema page — display model schema as a table."""

from __future__ import annotations

import streamlit as st

from pydantic_wizard.exceptions import ModelResolutionError
from pydantic_wizard.introspection import (
    get_type_display_name,
    introspect_model,
)
from pydantic_wizard.serialization import resolve_config_class


def _format_default(spec) -> str:  # type: ignore[no-untyped-def]
    """Format default value for display."""
    from pydantic_core import PydanticUndefined

    if spec.default is PydanticUndefined:
        if spec.default_factory is not None:
            return f"{spec.default_factory.__name__}()"
        return "—"
    if spec.default is None:
        return "None"
    return str(spec.default)


def render() -> None:
    """Render the Show Schema page."""
    st.header("Model Schema")

    model_fqn = st.text_input(
        "Model class (fully qualified name)",
        placeholder="e.g. myapp.config.DatabaseConfig",
        key="schema_fqn",
    )

    if not model_fqn:
        st.info("Enter a fully qualified Pydantic model class name to view its schema.")
        return

    try:
        config_class = resolve_config_class(model_fqn)
    except ModelResolutionError as e:
        st.error(f"Failed to resolve model: {e}")
        return

    st.subheader(config_class.__name__)

    specs = introspect_model(config_class)
    rows = []
    for spec in specs:
        rows.append(
            {
                "Field": spec.name,
                "Type": get_type_display_name(spec.annotation),
                "Required": "Yes" if spec.is_required else "No",
                "Default": _format_default(spec),
                "Description": spec.description or "",
            }
        )

    if rows:
        st.table(rows)
    else:
        st.warning("No fields found in this model.")

    # Optional: show raw JSON schema
    with st.expander("Raw JSON Schema"):
        st.json(config_class.model_json_schema())
