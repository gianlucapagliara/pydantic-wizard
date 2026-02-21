from __future__ import annotations

from typing import Any

import questionary
from pydantic import BaseModel, ValidationError

from pydantic_wizard.display import display_validation_errors


def validate_config(
    model_class: type[BaseModel],
    data: dict[str, Any],
) -> BaseModel:
    """Validate data against a Pydantic model, raising on failure."""
    return model_class.model_validate(data)


def validate_and_fix(
    model_class: type[BaseModel],
    data: dict[str, Any],
) -> BaseModel | None:
    """Validate data, offering interactive repair on failure.

    Returns the validated model instance, or None if the user aborts.
    """
    while True:
        try:
            return model_class.model_validate(data)
        except ValidationError as e:
            display_validation_errors(e.errors())

            should_fix = questionary.confirm(
                "Would you like to fix these errors?",
                default=True,
            ).ask()

            if not should_fix:
                return None

            # Re-prompt for each errored field
            for error in e.errors():
                field_loc = error.get("loc", ())
                if not field_loc:
                    continue

                field_name = str(field_loc[0])
                msg = error.get("msg", "Invalid value")

                new_value = questionary.text(
                    f"  New value for '{field_name}' ({msg}):",
                    default=str(data.get(field_name, "")),
                ).ask()

                if new_value is not None:
                    data[field_name] = new_value
