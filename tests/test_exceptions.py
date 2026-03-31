"""Tests for the custom exception hierarchy."""

from pydantic_wizard.exceptions import (
    ConfigLoadError,
    ConfigValidationError,
    ModelResolutionError,
    PydanticWizardError,
)


class TestExceptionHierarchy:
    def test_base_exception_is_exception(self):
        assert issubclass(PydanticWizardError, Exception)

    def test_config_load_error_inherits(self):
        assert issubclass(ConfigLoadError, PydanticWizardError)

    def test_config_validation_error_inherits(self):
        assert issubclass(ConfigValidationError, PydanticWizardError)

    def test_model_resolution_error_inherits(self):
        assert issubclass(ModelResolutionError, PydanticWizardError)

    def test_catch_all_with_base(self):
        """All custom exceptions should be catchable via PydanticWizardError."""
        for exc_cls in (ConfigLoadError, ConfigValidationError, ModelResolutionError):
            try:
                raise exc_cls("test")
            except PydanticWizardError:
                pass  # expected

    def test_message_preserved(self):
        err = ConfigLoadError("bad file")
        assert str(err) == "bad file"
