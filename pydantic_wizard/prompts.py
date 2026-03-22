from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from pydantic_wizard.display import display_field_header, display_model_header
from pydantic_wizard.introspection import FieldSpec, introspect_model
from pydantic_wizard.type_handlers import (
    DictHandler,
    ListHandler,
    OptionalHandler,
    PydanticModelHandler,
    SetHandler,
    TypeHandlerRegistry,
    UnionHandler,
)


def prompt_model(
    model_class: type[BaseModel],
    defaults: dict[str, Any] | None = None,
    path: str = "",
    registry: TypeHandlerRegistry | None = None,
) -> dict[str, Any]:
    """Recursively prompt for all fields of a Pydantic model.

    Returns a dict that can be passed to model_class.model_validate(result).
    """
    if registry is None:
        registry = TypeHandlerRegistry()

    if defaults is None:
        defaults = {}

    display_model_header(model_class, path)
    specs = introspect_model(model_class)
    result: dict[str, Any] = {}

    for spec in specs:
        # Skip non-init fields (computed / frozen)
        if not spec.is_init:
            continue

        # Determine effective default
        effective_default = defaults.get(spec.name)
        if effective_default is None:
            if spec.default is not None and str(spec.default) != "PydanticUndefined":
                effective_default = spec.default
            elif spec.default_factory is not None:
                try:
                    effective_default = spec.default_factory()
                except Exception:
                    effective_default = None

        display_field_header(spec, path)

        handler = registry.get_handler(spec)
        if handler is None:
            # Fallback: try as string
            from pydantic_wizard.type_handlers import StrHandler

            handler = StrHandler()

        value = _call_handler(handler, spec, effective_default, registry, path)
        result[spec.name] = value

    return result


def _call_handler(
    handler: Any,
    spec: FieldSpec,
    default: Any,
    registry: TypeHandlerRegistry,
    path: str,
) -> Any:
    """Call a handler's prompt method, passing extra args for composite handlers."""
    if isinstance(handler, PydanticModelHandler):
        return handler.prompt(
            spec,
            default,
            registry=registry,
            prompt_model_fn=lambda cls, defaults=None, path="": prompt_model(
                cls,
                defaults,
                path=f"{path} > {path}" if path else path,
                registry=registry,
            ),
        )
    if isinstance(
        handler, (OptionalHandler, ListHandler, SetHandler, UnionHandler, DictHandler)
    ):
        return handler.prompt(spec, default, registry=registry)
    return handler.prompt(spec, default)
