from __future__ import annotations

import enum
import types
from dataclasses import dataclass, field
from typing import Any, Literal, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


@dataclass
class FieldSpec:
    """Extracted metadata about a single Pydantic model field."""

    name: str
    annotation: Any = None
    origin: type | None = None
    args: tuple[Any, ...] = ()
    default: Any = PydanticUndefined
    default_factory: Any = None
    description: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    is_required: bool = True
    is_optional: bool = False
    is_init: bool = True
    inner_type: Any = None
    is_enum: bool = False
    is_literal: bool = False
    is_pydantic_model: bool = False
    is_union: bool = False
    union_types: list[type] = field(default_factory=list)
    is_list: bool = False
    is_set: bool = False
    is_dict: bool = False
    key_type: Any = None
    value_type: Any = None


def _is_none_type(tp: Any) -> bool:
    return tp is type(None)


def _extract_constraints(field_info: FieldInfo) -> dict[str, Any]:
    """Extract numeric constraints (ge, le, gt, lt, etc.) from field metadata."""
    constraints: dict[str, Any] = {}
    for meta in field_info.metadata:
        for attr in ("ge", "le", "gt", "lt", "min_length", "max_length", "pattern"):
            val = getattr(meta, attr, None)
            if val is not None:
                constraints[attr] = val
    return constraints


def _is_pydantic_model(tp: Any) -> bool:
    """Check if a type is a Pydantic BaseModel subclass."""
    try:
        return isinstance(tp, type) and issubclass(tp, BaseModel)
    except TypeError:
        return False


def _is_enum_type(tp: Any) -> bool:
    """Check if a type is an Enum subclass."""
    try:
        return isinstance(tp, type) and issubclass(tp, enum.Enum)
    except TypeError:
        return False


def _resolve_type(annotation: Any) -> FieldSpec:
    """Resolve a type annotation into a partially filled FieldSpec."""
    spec = FieldSpec(name="")

    origin = get_origin(annotation)
    args = get_args(annotation)
    spec.origin = origin
    spec.args = args

    # Handle Union / Optional (X | None, Union[X, None], Union[A, B])
    if origin is types.UnionType or origin is type(int | str):
        non_none = [a for a in args if not _is_none_type(a)]
        has_none = len(non_none) < len(args)
        spec.is_optional = has_none

        if len(non_none) == 1:
            # Optional[X] or X | None
            inner = _resolve_type(non_none[0])
            spec.inner_type = non_none[0]
            spec.is_enum = inner.is_enum
            spec.is_literal = inner.is_literal
            spec.is_pydantic_model = inner.is_pydantic_model
            spec.is_list = inner.is_list
            spec.is_set = inner.is_set
            spec.is_dict = inner.is_dict
            spec.union_types = inner.union_types
            spec.is_union = inner.is_union
            spec.key_type = inner.key_type
            spec.value_type = inner.value_type
            if inner.inner_type is not None:
                spec.inner_type = inner.inner_type
        elif len(non_none) > 1:
            # Union[A, B, C] — real union
            spec.is_union = True
            spec.union_types = list(non_none)
        return spec

    # typing.Union fallback (Python < 3.10 style, but still used)
    if origin is not None and getattr(origin, "__qualname__", None) == "Union":
        non_none = [a for a in args if not _is_none_type(a)]
        has_none = len(non_none) < len(args)
        spec.is_optional = has_none

        if len(non_none) == 1:
            inner = _resolve_type(non_none[0])
            spec.inner_type = non_none[0]
            spec.is_enum = inner.is_enum
            spec.is_literal = inner.is_literal
            spec.is_pydantic_model = inner.is_pydantic_model
            spec.is_list = inner.is_list
            spec.is_set = inner.is_set
            spec.is_dict = inner.is_dict
            spec.union_types = inner.union_types
            spec.is_union = inner.is_union
            spec.key_type = inner.key_type
            spec.value_type = inner.value_type
            if inner.inner_type is not None:
                spec.inner_type = inner.inner_type
        elif len(non_none) > 1:
            spec.is_union = True
            spec.union_types = list(non_none)
        return spec

    # list[X]
    if origin is list:
        spec.is_list = True
        spec.inner_type = args[0] if args else Any
        return spec

    # set[X]
    if origin is set:
        spec.is_set = True
        spec.inner_type = args[0] if args else Any
        return spec

    # dict[K, V]
    if origin is dict:
        spec.is_dict = True
        spec.key_type = args[0] if args else str
        spec.value_type = args[1] if len(args) > 1 else Any
        return spec

    # Literal[...]
    if origin is Literal:
        spec.is_literal = True
        return spec

    # Plain types
    if _is_enum_type(annotation):
        spec.is_enum = True
    elif _is_pydantic_model(annotation):
        spec.is_pydantic_model = True

    spec.inner_type = annotation
    return spec


def introspect_model(model_class: type[BaseModel]) -> list[FieldSpec]:
    """Extract FieldSpec for every field in a Pydantic v2 model."""
    specs: list[FieldSpec] = []

    for name, field_info in model_class.model_fields.items():
        annotation = field_info.annotation
        if annotation is None:
            continue

        resolved = _resolve_type(annotation)
        resolved.name = name
        resolved.annotation = annotation
        resolved.description = field_info.description
        resolved.constraints = _extract_constraints(field_info)

        # Defaults
        if field_info.default is not PydanticUndefined:
            resolved.default = field_info.default
            resolved.is_required = False
        elif field_info.default_factory is not None:
            resolved.default_factory = field_info.default_factory
            resolved.is_required = False

        if resolved.is_optional and resolved.is_required:
            # Optional fields with no default should default to None
            resolved.default = None
            resolved.is_required = False

        # init / frozen
        if field_info.init is False:
            resolved.is_init = False
        if field_info.frozen:
            resolved.is_init = False

        specs.append(resolved)

    return specs


def get_type_display_name(annotation: Any) -> str:
    """Return a human-readable name for a type annotation."""
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is types.UnionType:
        parts = [get_type_display_name(a) for a in args]
        return " | ".join(parts)

    if origin is list:
        inner = get_type_display_name(args[0]) if args else "Any"
        return f"list[{inner}]"

    if origin is set:
        inner = get_type_display_name(args[0]) if args else "Any"
        return f"set[{inner}]"

    if origin is dict:
        k = get_type_display_name(args[0]) if args else "str"
        v = get_type_display_name(args[1]) if len(args) > 1 else "Any"
        return f"dict[{k}, {v}]"

    if origin is Literal:
        return f"Literal{list(args)}"

    if annotation is type(None):
        return "None"

    if isinstance(annotation, type):
        return annotation.__name__

    return str(annotation)
