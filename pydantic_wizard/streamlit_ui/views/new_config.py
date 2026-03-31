"""New Config page — create a configuration from scratch."""

from __future__ import annotations

import io
from typing import Any

import streamlit as st
import yaml
from pydantic import ValidationError

from pydantic_wizard.exceptions import ModelResolutionError
from pydantic_wizard.serialization import (
    CONFIGURATION_KEY,
    METADATA_KEY,
    ModelConfigDumper,
    prepare_for_serialization,
    resolve_config_class,
)
from pydantic_wizard.streamlit_ui.model_form import render_model_form


def _get_package_version() -> str:
    try:
        from importlib.metadata import version

        return version("pydantic-wizard")
    except Exception:
        return "unknown"


def _build_yaml(data: dict[str, Any], config_class: type, model_name: str) -> str:
    """Build a YAML string with metadata envelope."""
    prepared = prepare_for_serialization(data)
    config_fqn = f"{config_class.__module__}.{config_class.__qualname__}"
    document = {
        METADATA_KEY: {
            "model_type": model_name,
            "configuration_class": config_fqn,
            "version": _get_package_version(),
        },
        CONFIGURATION_KEY: prepared,
    }
    buf = io.StringIO()
    yaml.dump(
        document,
        buf,
        Dumper=ModelConfigDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return buf.getvalue()


def render() -> None:
    """Render the New Config page."""
    st.header("New Configuration")

    model_fqn = st.text_input(
        "Model class (fully qualified name)",
        placeholder="e.g. myapp.config.DatabaseConfig",
        key="new_config_fqn",
    )

    if not model_fqn:
        st.info("Enter a fully qualified Pydantic model class name to begin.")
        return

    # Resolve the model class
    try:
        config_class = resolve_config_class(model_fqn)
    except ModelResolutionError as e:
        st.error(f"Failed to resolve model: {e}")
        return

    st.subheader(f"Configure: {config_class.__name__}")
    st.caption(f"Class: `{model_fqn}`")

    # Render the form
    st.divider()
    data = render_model_form(config_class, key_prefix="new")

    # Actions
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Validate", key="new_validate", type="primary"):
            try:
                config_class.model_validate(data)
                st.session_state["new_valid"] = True
                st.session_state["new_errors"] = None
                st.success("Configuration is valid!")
            except ValidationError as e:
                st.session_state["new_valid"] = False
                st.session_state["new_errors"] = e.errors()

    # Show validation errors if any
    errors = st.session_state.get("new_errors")
    if errors:
        st.error("Validation errors:")
        for err in errors:
            loc = " > ".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "")
            st.markdown(f"- **{loc}**: {msg}")

    # Download button (always available, validation is advisory)
    with col2:
        yaml_content = _build_yaml(data, config_class, config_class.__name__)
        st.download_button(
            "Download YAML",
            data=yaml_content,
            file_name="config.yaml",
            mime="text/yaml",
            key="new_download",
        )
