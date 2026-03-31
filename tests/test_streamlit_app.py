"""Integration tests for the Streamlit web UI using AppTest."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def app() -> AppTest:
    """Boot the Streamlit app in headless test mode."""
    at = AppTest.from_file(
        "pydantic_wizard/streamlit_ui/app.py",
        default_timeout=10,
    )
    at.run()
    return at


# ── App boot & navigation ───────────────────────────────────────────


def test_app_boots_without_error(app: AppTest):
    assert not app.exception


def test_app_title_present(app: AppTest):
    assert any("Pydantic Wizard" in el.value for el in app.title)


def test_sidebar_navigation_present(app: AppTest):
    radio = app.sidebar.radio
    assert len(radio) == 1
    assert radio[0].value == "New Config"


def test_navigate_to_show_schema(app: AppTest):
    app.sidebar.radio[0].set_value("Show Schema").run()
    assert not app.exception
    assert any("Model Schema" in el.value for el in app.header)


def test_navigate_to_validate(app: AppTest):
    app.sidebar.radio[0].set_value("Validate").run()
    assert not app.exception
    assert any("Validate" in el.value for el in app.header)


def test_navigate_to_edit_config(app: AppTest):
    app.sidebar.radio[0].set_value("Edit Config").run()
    assert not app.exception
    assert any("Edit" in el.value for el in app.header)


# ── New Config page ─────────────────────────────────────────────────


def test_new_config_shows_info_when_empty(app: AppTest):
    """Without a model FQN, the page should show an info message."""
    assert any("Enter a fully qualified" in el.value for el in app.info)


def test_new_config_shows_error_for_bad_fqn(app: AppTest):
    app.text_input[0].set_value("nonexistent.module.Model").run()
    assert not app.exception
    assert any("Failed to resolve" in el.value for el in app.error)


def test_new_config_renders_form_for_valid_model(app: AppTest):
    app.text_input[0].set_value("tests.conftest.SimpleConfig").run()
    assert not app.exception
    # Should have form widgets for SimpleConfig fields
    assert any("SimpleConfig" in el.value for el in app.subheader)


# ── Show Schema page ────────────────────────────────────────────────


def test_show_schema_renders_table(app: AppTest):
    app.sidebar.radio[0].set_value("Show Schema").run()
    app.text_input[0].set_value("tests.conftest.SimpleConfig").run()
    assert not app.exception
    # Should display the model name
    assert any("SimpleConfig" in el.value for el in app.subheader)


def test_show_schema_error_for_bad_fqn(app: AppTest):
    app.sidebar.radio[0].set_value("Show Schema").run()
    app.text_input[0].set_value("bad.module.Nope").run()
    assert not app.exception
    assert any("Failed to resolve" in el.value for el in app.error)


# ── Validate page ───────────────────────────────────────────────────


def test_validate_page_shows_info_when_no_file(app: AppTest):
    app.sidebar.radio[0].set_value("Validate").run()
    assert not app.exception
    assert any("Upload a YAML" in el.value for el in app.info)
