"""Validate page — upload a YAML and validate against a Pydantic model."""

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


def render() -> None:
    """Render the Validate page."""
    st.header("Validate Configuration")

    uploaded = st.file_uploader(
        "Upload a YAML configuration file",
        type=["yaml", "yml"],
        key="validate_upload",
    )

    if uploaded is None:
        st.info("Upload a YAML file to validate it against its Pydantic model.")
        return

    # Parse
    try:
        raw = yaml.safe_load(uploaded.getvalue())
    except yaml.YAMLError as e:
        st.error(f"Failed to parse YAML: {e}")
        return

    if not isinstance(raw, dict):
        st.error(f"Expected a YAML mapping, got {type(raw).__name__}")
        return

    metadata = raw.get(METADATA_KEY, {})
    config_fqn = metadata.get("configuration_class", "")
    model_name = metadata.get("model_type", "")
    data = raw.get(CONFIGURATION_KEY, {})

    # FQN override
    fqn_input = st.text_input(
        "Model class (override if needed)",
        value=config_fqn,
        key="validate_fqn",
    )

    if not fqn_input:
        st.warning("No model class specified. Enter the fully qualified name above.")
        return

    try:
        config_class = resolve_config_class(fqn_input)
    except ModelResolutionError as e:
        st.error(f"Failed to resolve model: {e}")
        return

    # Validate
    if st.button("Validate", key="validate_run", type="primary"):
        try:
            config_class.model_validate(data)
            st.success(
                f"Valid **{config_class.__name__}** configuration"
                + (f" for {model_name}" if model_name else "")
            )
        except ValidationError as e:
            st.error(f"Validation failed — {len(e.errors())} error(s):")
            for err in e.errors():
                loc = " > ".join(str(x) for x in err.get("loc", []))
                msg = err.get("msg", "")
                st.markdown(f"- **{loc}**: {msg}")
