"""Tests for display module."""

from unittest.mock import patch

from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

from pydantic_wizard.display import (
    _format_default,
    _truncate,
    display_error,
    display_field_header,
    display_model_header,
    display_schema,
    display_success,
    display_summary_table,
    display_validation_errors,
    display_warning,
)
from pydantic_wizard.introspection import FieldSpec, introspect_model


class TestFormatDefault:
    def test_with_concrete_default(self):
        spec = FieldSpec(name="x", default=42)
        assert _format_default(spec) == "42"

    def test_with_none_default(self):
        spec = FieldSpec(name="x", default=None)
        assert _format_default(spec) == "None"

    def test_with_pydantic_undefined(self):
        spec = FieldSpec(name="x", default=PydanticUndefined)
        assert _format_default(spec) == "None"

    def test_with_default_factory(self):
        spec = FieldSpec(name="x", default=PydanticUndefined, default_factory=list)
        assert _format_default(spec) == "[]"

    def test_with_failing_factory(self):
        def bad_factory():
            raise TypeError("boom")

        spec = FieldSpec(
            name="x", default=PydanticUndefined, default_factory=bad_factory
        )
        assert _format_default(spec) == "<factory>"

    def test_with_string_default(self):
        spec = FieldSpec(name="x", default="hello")
        assert _format_default(spec) == "'hello'"


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("short", 80) == "short"

    def test_long_string_truncated(self):
        result = _truncate("a" * 100, 20)
        assert len(result) == 20
        assert result.endswith("...")

    def test_exact_length_unchanged(self):
        assert _truncate("12345", 5) == "12345"


class TestDisplayFunctions:
    """Test that display functions run without errors (output to Rich console)."""

    @patch("pydantic_wizard.display.console")
    def test_display_model_header(self, mock_console):
        class Dummy(BaseModel):
            x: int = 1

        display_model_header(Dummy)
        mock_console.print.assert_called_once()

    @patch("pydantic_wizard.display.console")
    def test_display_model_header_with_path(self, mock_console):
        class Dummy(BaseModel):
            x: int = 1

        display_model_header(Dummy, path="parent")
        call_args = mock_console.print.call_args[0][0]
        assert "parent" in call_args

    @patch("pydantic_wizard.display.console")
    def test_display_field_header(self, mock_console):
        spec = FieldSpec(
            name="my_field",
            annotation=int,
            inner_type=int,
            is_required=True,
        )
        display_field_header(spec)
        mock_console.print.assert_called_once()

    @patch("pydantic_wizard.display.console")
    def test_display_field_header_optional_with_constraints(self, mock_console):
        spec = FieldSpec(
            name="bounded",
            annotation=int,
            inner_type=int,
            is_required=False,
            default=5,
            constraints={"ge": 0, "le": 100},
            description="A bounded int",
        )
        display_field_header(spec, path="config")
        mock_console.print.assert_called_once()

    @patch("pydantic_wizard.display.console")
    def test_display_summary_table(self, mock_console):
        display_summary_table({"key": "value", "num": 42}, "TestModel")
        mock_console.print.assert_called_once()

    @patch("pydantic_wizard.display.console")
    def test_display_model_list(self, mock_console):
        from pydantic_wizard.display import display_model_list

        class A(BaseModel):
            x: int = 1

        class B(BaseModel):
            y: str = ""

        display_model_list({"ModelA": A, "ModelB": B})
        mock_console.print.assert_called_once()

    @patch("pydantic_wizard.display.console")
    def test_display_schema(self, mock_console):
        class M(BaseModel):
            name: str
            count: int = Field(default=0, ge=0, description="A count")

        specs = introspect_model(M)
        display_schema(M, specs)
        mock_console.print.assert_called_once()

    @patch("pydantic_wizard.display.console")
    def test_display_validation_errors(self, mock_console):
        errors = [
            {"loc": ("name",), "msg": "field required"},
            {"loc": ("count",), "msg": "must be >= 0"},
        ]
        display_validation_errors(errors)
        assert mock_console.print.call_count == 3  # header + 2 errors

    @patch("pydantic_wizard.display.console")
    def test_display_success(self, mock_console):
        display_success("All good!")
        mock_console.print.assert_called_once()

    @patch("pydantic_wizard.display.console")
    def test_display_error(self, mock_console):
        display_error("Something broke")
        mock_console.print.assert_called_once()

    @patch("pydantic_wizard.display.console")
    def test_display_warning(self, mock_console):
        display_warning("Watch out")
        mock_console.print.assert_called_once()
