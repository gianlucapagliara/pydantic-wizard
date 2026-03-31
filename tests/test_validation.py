"""Tests for the validation module."""

from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field

from pydantic_wizard.exceptions import ConfigValidationError
from pydantic_wizard.validation import validate_and_fix, validate_config


class StrictModel(BaseModel):
    name: str
    age: int = Field(ge=0)


class TestValidateConfig:
    def test_valid_data_returns_model(self):
        result = validate_config(StrictModel, {"name": "Alice", "age": 30})
        assert isinstance(result, StrictModel)
        assert result.name == "Alice"
        assert result.age == 30

    def test_invalid_data_raises_config_validation_error(self):
        with pytest.raises(ConfigValidationError):
            validate_config(StrictModel, {"name": "Alice", "age": -1})

    def test_missing_required_field_raises(self):
        with pytest.raises(ConfigValidationError):
            validate_config(StrictModel, {"age": 5})

    def test_error_is_pydantic_wizard_error(self):
        from pydantic_wizard.exceptions import PydanticWizardError

        with pytest.raises(PydanticWizardError):
            validate_config(StrictModel, {})

    def test_error_message_contains_details(self):
        with pytest.raises(ConfigValidationError, match="name"):
            validate_config(StrictModel, {"age": 5})


class TestValidateAndFix:
    def test_valid_data_returns_immediately(self):
        result = validate_and_fix(StrictModel, {"name": "Bob", "age": 25})
        assert isinstance(result, StrictModel)

    @patch("pydantic_wizard.validation.questionary")
    @patch("pydantic_wizard.validation.display_validation_errors")
    def test_user_aborts_returns_none(self, mock_display, mock_q):
        mock_q.confirm.return_value.ask.return_value = False
        result = validate_and_fix(StrictModel, {"age": -1})
        assert result is None
        mock_display.assert_called_once()

    @patch("pydantic_wizard.validation.questionary")
    @patch("pydantic_wizard.validation.display_validation_errors")
    def test_user_fixes_field(self, mock_display, mock_q):
        # First call: confirm fix -> yes; second call won't happen since data is valid
        mock_q.confirm.return_value.ask.return_value = True
        mock_q.text.return_value.ask.return_value = "Alice"

        data = {"age": 5}  # missing name
        result = validate_and_fix(StrictModel, data)
        assert isinstance(result, StrictModel)
        assert result.name == "Alice"
