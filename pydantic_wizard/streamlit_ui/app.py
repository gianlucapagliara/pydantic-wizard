"""Main Streamlit application for pydantic-wizard."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="Pydantic Wizard",
        page_icon="🧙",
        layout="wide",
    )

    st.title("Pydantic Wizard")
    st.caption("Interactive configuration for Pydantic v2 models")

    page = st.sidebar.radio(
        "Operation",
        ["New Config", "Edit Config", "Validate", "Show Schema"],
        key="page_nav",
    )

    if page == "New Config":
        from pydantic_wizard.streamlit_ui.views.new_config import render

        render()
    elif page == "Edit Config":
        from pydantic_wizard.streamlit_ui.views.edit_config import render

        render()
    elif page == "Validate":
        from pydantic_wizard.streamlit_ui.views.validate_page import render

        render()
    elif page == "Show Schema":
        from pydantic_wizard.streamlit_ui.views.show_schema import render

        render()


if __name__ == "__main__":
    main()
else:
    # When run via `streamlit run`, the module is imported, not executed as __main__
    main()
