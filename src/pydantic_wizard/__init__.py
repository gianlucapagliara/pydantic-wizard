"""pydantic-wizard: Interactive wizard-style CLI for configuring Pydantic v2 models."""

from pydantic_wizard.display import (
    display_model_list,
    display_schema,
    display_summary_table,
    display_validation_errors,
)
from pydantic_wizard.introspection import (
    FieldSpec,
    get_type_display_name,
    introspect_model,
)
from pydantic_wizard.prompts import prompt_model
from pydantic_wizard.serialization import (
    load_from_yaml,
    resolve_config_class,
    serialize_to_yaml,
)
from pydantic_wizard.type_handlers import TypeHandler, TypeHandlerRegistry
from pydantic_wizard.validation import validate_and_fix, validate_config

__all__ = [
    # Introspection
    "FieldSpec",
    "introspect_model",
    "get_type_display_name",
    # Prompting
    "prompt_model",
    # Serialization
    "serialize_to_yaml",
    "load_from_yaml",
    "resolve_config_class",
    # Validation
    "validate_config",
    "validate_and_fix",
    # Type handlers
    "TypeHandler",
    "TypeHandlerRegistry",
    # Display
    "display_model_list",
    "display_schema",
    "display_summary_table",
    "display_validation_errors",
]
