"""Tests for pydantic_wizard.streamlit_ui.utils and widgets helpers."""

from __future__ import annotations

from pydantic import BaseModel, Field

from pydantic_wizard.introspection import FieldSpec, introspect_model
from pydantic_wizard.streamlit_ui.utils import build_yaml, get_package_version
from pydantic_wizard.streamlit_ui.widgets import (
    _label,
    _make_inner_spec,
    _numeric_bounds,
)

# ── get_package_version ──────────────────────────────────────────────


def test_get_package_version_returns_string():
    result = get_package_version()
    assert isinstance(result, str)
    assert result != ""


# ── build_yaml ───────────────────────────────────────────────────────


class _DummyModel(BaseModel):
    name: str = "test"


def test_build_yaml_contains_metadata():
    yaml_str = build_yaml({"name": "hello"}, _DummyModel, "DummyModel")
    assert "_metadata:" in yaml_str
    assert "model_type: DummyModel" in yaml_str
    assert "configuration_class:" in yaml_str
    assert "configuration:" in yaml_str
    assert "name: hello" in yaml_str


def test_build_yaml_preserves_version():
    yaml_str = build_yaml({}, _DummyModel, "DummyModel")
    assert "version:" in yaml_str


# ── _label ───────────────────────────────────────────────────────────


def _make_spec(**overrides: object) -> FieldSpec:
    """Create a minimal FieldSpec for testing."""
    defaults: dict = {
        "name": "test_field",
        "annotation": str,
        "inner_type": str,
        "is_required": False,
    }
    defaults.update(overrides)
    return FieldSpec(**defaults)


def test_label_basic():
    spec = _make_spec(name="host")
    result = _label(spec)
    assert "host" in result


def test_label_required_marker():
    spec = _make_spec(name="host", is_required=True)
    result = _label(spec)
    assert "*" in result


def test_label_not_required():
    spec = _make_spec(name="host", is_required=False)
    result = _label(spec)
    assert "*" not in result


def test_label_extra_overrides_type():
    spec = _make_spec(name="amount")
    result = _label(spec, extra="decimal")
    assert "decimal" in result


# ── _numeric_bounds ──────────────────────────────────────────────────


def test_numeric_bounds_ge_le_int():
    spec = _make_spec(constraints={"ge": 0, "le": 100})
    bounds = _numeric_bounds(spec, is_int=True)
    assert bounds["min_value"] == 0
    assert bounds["max_value"] == 100


def test_numeric_bounds_gt_lt_int():
    spec = _make_spec(constraints={"gt": 0, "lt": 100})
    bounds = _numeric_bounds(spec, is_int=True)
    assert bounds["min_value"] == 1
    assert bounds["max_value"] == 99


def test_numeric_bounds_ge_le_float():
    spec = _make_spec(constraints={"ge": 0.5, "le": 10.5})
    bounds = _numeric_bounds(spec, is_int=False)
    assert bounds["min_value"] == 0.5
    assert bounds["max_value"] == 10.5


def test_numeric_bounds_gt_lt_float():
    spec = _make_spec(constraints={"gt": 0.0, "lt": 1.0})
    bounds = _numeric_bounds(spec, is_int=False)
    # For floats, gt/lt are passed as-is (no epsilon adjustment)
    assert bounds["min_value"] == 0.0
    assert bounds["max_value"] == 1.0


def test_numeric_bounds_empty():
    spec = _make_spec(constraints={})
    bounds = _numeric_bounds(spec, is_int=True)
    assert bounds == {}


def test_numeric_bounds_partial():
    spec = _make_spec(constraints={"ge": 5})
    bounds = _numeric_bounds(spec, is_int=True)
    assert bounds == {"min_value": 5}
    assert "max_value" not in bounds


# ── _make_inner_spec ─────────────────────────────────────────────────


def test_make_inner_spec_basic():
    spec = _make_spec(inner_type=int)
    inner = _make_inner_spec(spec, "items[0]")
    assert inner.name == "items[0]"
    assert inner.inner_type is int
    assert inner.is_required is True
    assert inner.is_optional is False


def test_make_inner_spec_pydantic_model():
    class Inner(BaseModel):
        x: int = 0

    spec = _make_spec(inner_type=Inner)
    inner = _make_inner_spec(spec, "nested")
    assert inner.is_pydantic_model is True
    assert inner.inner_type is Inner


def test_make_inner_spec_not_enum_for_plain_type():
    spec = _make_spec(inner_type=str)
    inner = _make_inner_spec(spec, "item")
    assert inner.is_enum is False


# ── _render_str constraint help text ────────────────────────────────


def test_str_field_spec_constraints_available():
    """Verify that introspected string fields carry constraints through."""

    class M(BaseModel):
        code: str = Field(min_length=2, max_length=10)

    specs = introspect_model(M)
    code_spec = next(s for s in specs if s.name == "code")
    assert "min_length" in code_spec.constraints
    assert "max_length" in code_spec.constraints
