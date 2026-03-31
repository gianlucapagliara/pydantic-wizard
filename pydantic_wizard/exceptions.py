"""Custom exception hierarchy for pydantic-wizard."""

from __future__ import annotations


class PydanticWizardError(Exception):
    """Base exception for all pydantic-wizard errors."""


class ConfigLoadError(PydanticWizardError):
    """Raised when a YAML configuration file cannot be loaded or parsed."""


class ConfigValidationError(PydanticWizardError):
    """Raised when configuration data fails Pydantic model validation."""


class ModelResolutionError(PydanticWizardError):
    """Raised when a fully-qualified model class name cannot be imported or resolved."""
