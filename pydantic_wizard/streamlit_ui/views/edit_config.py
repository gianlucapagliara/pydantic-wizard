"""Edit Config page — load and edit an existing YAML configuration."""

from __future__ import annotations

import streamlit as st
import yaml
from pydantic import ValidationError

from pydantic_wizard.exceptions import ModelResolutionError
from pydantic_wizard.serialization import (
    CONFIGURATION_KEY,
    METADATA_KEY,
    resolve_config_class,
)
from pydantic_wizard.streamlit_ui.model_form import render_model_form
from pydantic_wizard.streamlit_ui.utils import build_yaml


def render() -> None:
    """Render the Edit Config page."""
    st.header("Edit Configuration")

    uploaded = st.file_uploader(
        "Upload a YAML configuration file",
        type=["yaml", "yml"],
        key="edit_upload",
    )

    if uploaded is None:
        st.info("Upload an existing pydantic-wizard YAML file to edit it.")
        return

    # Parse uploaded YAML
    try:
        raw = yaml.safe_load(uploaded.getvalue())
    except yaml.YAMLError as e:
        st.error(f"Failed to parse YAML: {e}")
        return

    if not isinstance(raw, dict):
        st.error(f"Expected a YAML mapping, got {type(raw).__name__}")
        return

    # Extract metadata and data
    metadata = raw.get(METADATA_KEY, {})
    model_name = metadata.get("model_type", "")
    config_fqn = metadata.get("configuration_class", "")
    data = raw.get(CONFIGURATION_KEY, {})

    # Allow FQN override
    fqn_input = st.text_input(
        "Model class (auto-detected from metadata)",
        value=config_fqn,
        key="edit_fqn",
    )

    if not fqn_input:
        st.warning(
            "No model class found in metadata. Enter the fully qualified name above."
        )
        return

    try:
        config_class = resolve_config_class(fqn_input)
    except ModelResolutionError as e:
        st.error(f"Failed to resolve model: {e}")
        return

    st.subheader(f"Editing: {model_name or config_class.__name__}")
    st.caption(f"Class: `{fqn_input}`")

    # Render form with existing values as defaults
    st.divider()
    new_data = render_model_form(config_class, defaults=data, key_prefix="edit")

    # Actions
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Validate", key="edit_validate", type="primary"):
            try:
                config_class.model_validate(new_data)
                st.session_state["edit_valid"] = True
                st.session_state["edit_errors"] = None
                st.success("Configuration is valid!")
            except ValidationError as e:
                st.session_state["edit_valid"] = False
                st.session_state["edit_errors"] = e.errors()

    errors = st.session_state.get("edit_errors")
    if errors:
        st.error("Validation errors:")
        for err in errors:
            loc = " > ".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "")
            st.markdown(f"- **{loc}**: {msg}")

    with col2:
        yaml_content = build_yaml(
            new_data, config_class, model_name or config_class.__name__
        )
        file_name = uploaded.name if uploaded.name else "config.yaml"
        st.download_button(
            "Download YAML",
            data=yaml_content,
            file_name=file_name,
            mime="text/yaml",
            key="edit_download",
        )
