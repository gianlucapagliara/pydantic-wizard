"""New Config page — create a configuration from scratch."""

from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from pydantic_wizard.exceptions import ModelResolutionError
from pydantic_wizard.serialization import resolve_config_class
from pydantic_wizard.streamlit_ui.model_form import render_model_form
from pydantic_wizard.streamlit_ui.utils import build_yaml


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
        yaml_content = build_yaml(data, config_class, config_class.__name__)
        file_name = f"{config_class.__name__.lower()}.yaml"
        st.download_button(
            "Download YAML",
            data=yaml_content,
            file_name=file_name,
            mime="text/yaml",
            key="new_download",
        )
