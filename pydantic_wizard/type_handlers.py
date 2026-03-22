from __future__ import annotations

import datetime
import enum
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol, get_args

import questionary
from pydantic import BaseModel

from pydantic_wizard.introspection import FieldSpec, get_type_display_name


class TypeHandler(Protocol):
    """Protocol for field-type-specific prompt and serialization handlers."""

    def can_handle(self, spec: FieldSpec) -> bool: ...
    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any: ...
    def serialize(self, value: Any) -> Any: ...
    def deserialize(self, raw: Any, spec: FieldSpec) -> Any: ...


class BoolHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.inner_type is bool

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        default_val = default if isinstance(default, bool) else True
        return questionary.confirm(
            f"  {spec.name}?",
            default=default_val,
        ).ask()

    def serialize(self, value: Any) -> Any:
        return bool(value)

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return bool(raw)


class StrHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.inner_type is str

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        default_str = str(default) if default is not None else ""
        result = questionary.text(
            f"  {spec.name}:",
            default=default_str,
            validate=lambda val: (
                True if val.strip() or not spec.is_required else "Value is required"
            ),
        ).ask()
        return result.strip() if result else ""

    def serialize(self, value: Any) -> Any:
        return str(value)

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return str(raw)


class IntHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.inner_type is int

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        default_str = str(default) if default is not None else ""
        constraints = spec.constraints

        def validate_int(val: str) -> bool | str:
            if not val.strip():
                return True if not spec.is_required else "Value is required"
            try:
                n = int(val)
            except ValueError:
                return "Must be an integer"
            if "ge" in constraints and n < constraints["ge"]:
                return f"Must be >= {constraints['ge']}"
            if "le" in constraints and n > constraints["le"]:
                return f"Must be <= {constraints['le']}"
            if "gt" in constraints and n <= constraints["gt"]:
                return f"Must be > {constraints['gt']}"
            if "lt" in constraints and n >= constraints["lt"]:
                return f"Must be < {constraints['lt']}"
            return True

        result = questionary.text(
            f"  {spec.name} (int):",
            default=default_str,
            validate=validate_int,
        ).ask()
        return int(result) if result and result.strip() else default

    def serialize(self, value: Any) -> Any:
        return int(value)

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return int(raw)


class FloatHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.inner_type is float

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        default_str = str(default) if default is not None else ""
        constraints = spec.constraints

        def validate_float(val: str) -> bool | str:
            if not val.strip():
                return True if not spec.is_required else "Value is required"
            try:
                n = float(val)
            except ValueError:
                return "Must be a number"
            if "ge" in constraints and n < constraints["ge"]:
                return f"Must be >= {constraints['ge']}"
            if "le" in constraints and n > constraints["le"]:
                return f"Must be <= {constraints['le']}"
            return True

        result = questionary.text(
            f"  {spec.name} (float):",
            default=default_str,
            validate=validate_float,
        ).ask()
        return float(result) if result and result.strip() else default

    def serialize(self, value: Any) -> Any:
        return float(value)

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return float(raw)


class DecimalHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.inner_type is Decimal

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        default_str = str(default) if default is not None else ""
        constraints = spec.constraints

        def validate_decimal(val: str) -> bool | str:
            if not val.strip():
                return True if not spec.is_required else "Value is required"
            try:
                d = Decimal(val)
            except InvalidOperation:
                return "Must be a valid decimal number"
            if "ge" in constraints and d < Decimal(str(constraints["ge"])):
                return f"Must be >= {constraints['ge']}"
            if "le" in constraints and d > Decimal(str(constraints["le"])):
                return f"Must be <= {constraints['le']}"
            return True

        result = questionary.text(
            f"  {spec.name} (decimal):",
            default=default_str,
            validate=validate_decimal,
        ).ask()
        return Decimal(result) if result and result.strip() else default

    def serialize(self, value: Any) -> Any:
        return str(value)

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return Decimal(str(raw))


class EnumHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.is_enum

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        enum_type = spec.inner_type
        if not isinstance(enum_type, type) or not issubclass(enum_type, enum.Enum):
            return StrHandler().prompt(spec, default)

        members = list(enum_type)
        choices = [questionary.Choice(title=str(m.value), value=m) for m in members]
        default_str = str(default.value) if isinstance(default, enum_type) else None
        result = questionary.select(
            f"  {spec.name}:",
            choices=choices,
            default=default_str,
        ).ask()
        return result

    def serialize(self, value: Any) -> Any:
        if isinstance(value, enum.Enum):
            return value.value
        return value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        enum_type = spec.inner_type
        if isinstance(enum_type, type) and issubclass(enum_type, enum.Enum):
            return enum_type(raw)
        return raw


class LiteralHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.is_literal

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        choices_values = list(get_args(spec.annotation))
        if not choices_values:
            choices_values = list(spec.args)
        choices = [questionary.Choice(title=str(v), value=v) for v in choices_values]
        result = questionary.select(
            f"  {spec.name}:",
            choices=choices,
            default=default,
        ).ask()
        return result

    def serialize(self, value: Any) -> Any:
        return value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return raw


class DatetimeHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.inner_type is datetime.datetime

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        default_str = (
            default.isoformat() if isinstance(default, datetime.datetime) else ""
        )

        def validate_dt(val: str) -> bool | str:
            if not val.strip():
                return True if not spec.is_required else "Value is required"
            try:
                datetime.datetime.fromisoformat(val)
            except ValueError:
                return "Must be a valid ISO datetime (e.g. 2024-01-15T10:30:00)"
            return True

        result = questionary.text(
            f"  {spec.name} (ISO datetime, e.g. 2024-01-15T10:30:00):",
            default=default_str,
            validate=validate_dt,
        ).ask()
        if result and result.strip():
            return datetime.datetime.fromisoformat(result)
        return default

    def serialize(self, value: Any) -> Any:
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        return value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        if isinstance(raw, str):
            return datetime.datetime.fromisoformat(raw)
        return raw


class TimeHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.inner_type is datetime.time

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        default_str = default.isoformat() if isinstance(default, datetime.time) else ""

        def validate_time(val: str) -> bool | str:
            if not val.strip():
                return True if not spec.is_required else "Value is required"
            try:
                datetime.time.fromisoformat(val)
            except ValueError:
                return "Must be a valid time (e.g. 10:30:00)"
            return True

        result = questionary.text(
            f"  {spec.name} (HH:MM:SS):",
            default=default_str,
            validate=validate_time,
        ).ask()
        if result and result.strip():
            return datetime.time.fromisoformat(result)
        return default

    def serialize(self, value: Any) -> Any:
        if isinstance(value, datetime.time):
            return value.isoformat()
        return value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        if isinstance(raw, str):
            return datetime.time.fromisoformat(raw)
        return raw


class TimedeltaHandler:
    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.inner_type is datetime.timedelta

    def prompt(self, spec: FieldSpec, default: Any | None = None) -> Any:
        default_seconds = ""
        if isinstance(default, datetime.timedelta):
            default_seconds = str(int(default.total_seconds()))

        result = questionary.text(
            f"  {spec.name} (total seconds):",
            default=default_seconds,
            validate=lambda v: (
                True
                if not v.strip() and not spec.is_required
                else (True if v.strip().isdigit() else "Must be a non-negative integer")
            ),
        ).ask()
        if result and result.strip():
            return datetime.timedelta(seconds=int(result))
        return default

    def serialize(self, value: Any) -> Any:
        if isinstance(value, datetime.timedelta):
            return value.total_seconds()
        return value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return datetime.timedelta(seconds=float(raw))


# ── Composite handlers (these depend on the registry to recurse) ──


class OptionalHandler:
    """Wraps another handler, adding a skip prompt for None."""

    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.is_optional

    def prompt(
        self,
        spec: FieldSpec,
        default: Any | None = None,
        registry: TypeHandlerRegistry | None = None,
    ) -> Any:
        should_configure = questionary.confirm(
            f"  Configure {spec.name}? ({get_type_display_name(spec.annotation)})",
            default=default is not None,
        ).ask()
        if not should_configure:
            return None

        # Build a non-optional spec to delegate to the inner handler
        inner_spec = FieldSpec(
            name=spec.name,
            annotation=spec.inner_type or spec.annotation,
            inner_type=spec.inner_type,
            description=spec.description,
            constraints=spec.constraints,
            is_required=False,
            is_optional=False,
            is_enum=spec.is_enum,
            is_literal=spec.is_literal,
            is_pydantic_model=spec.is_pydantic_model,
            is_list=spec.is_list,
            is_set=spec.is_set,
            is_dict=spec.is_dict,
            is_union=spec.is_union,
            union_types=spec.union_types,
            key_type=spec.key_type,
            value_type=spec.value_type,
        )
        if registry:
            handler = registry.get_handler(inner_spec)
            if handler:
                return handler.prompt(inner_spec, default)
        return None

    def serialize(self, value: Any) -> Any:
        return value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return raw


class ListHandler:
    """Handles list[T] fields by prompting for count then each item."""

    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.is_list

    def prompt(
        self,
        spec: FieldSpec,
        default: Any | None = None,
        registry: TypeHandlerRegistry | None = None,
    ) -> Any:
        default_count = str(len(default)) if isinstance(default, list) else "1"
        count_str = questionary.text(
            f"  How many items for {spec.name}?",
            default=default_count,
            validate=lambda v: (
                True if v.strip().isdigit() else "Must be a non-negative integer"
            ),
        ).ask()
        count = int(count_str) if count_str else 0

        items: list[Any] = []
        for i in range(count):
            item_default = (
                default[i] if isinstance(default, list) and i < len(default) else None
            )
            inner_spec = FieldSpec(
                name=f"{spec.name}[{i}]",
                annotation=spec.inner_type,
                inner_type=spec.inner_type,
                is_required=True,
                is_optional=False,
                is_pydantic_model=(
                    isinstance(spec.inner_type, type)
                    and issubclass(spec.inner_type, BaseModel)
                ),
                is_enum=(
                    isinstance(spec.inner_type, type)
                    and issubclass(spec.inner_type, enum.Enum)
                ),
            )
            if registry:
                handler = registry.get_handler(inner_spec)
                if handler:
                    items.append(handler.prompt(inner_spec, item_default))
        return items

    def serialize(self, value: Any) -> Any:
        return value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return list(raw) if raw else []


class SetHandler:
    """Handles set[T] fields. For Enum inner types, uses checkbox multi-select."""

    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.is_set

    def prompt(
        self,
        spec: FieldSpec,
        default: Any | None = None,
        registry: TypeHandlerRegistry | None = None,
    ) -> Any:
        inner = spec.inner_type
        if isinstance(inner, type) and issubclass(inner, enum.Enum):
            members = list(inner)
            default_values = set(default) if isinstance(default, (set, list)) else set()
            choices = [
                questionary.Choice(
                    title=str(m.value),
                    value=m,
                    checked=m in default_values,
                )
                for m in members
            ]
            result = questionary.checkbox(
                f"  {spec.name} (select multiple):",
                choices=choices,
            ).ask()
            return set(result) if result else set()

        # Fallback: prompt like a list
        list_spec = FieldSpec(
            name=spec.name,
            annotation=spec.annotation,
            inner_type=spec.inner_type,
            is_list=True,
            is_required=spec.is_required,
        )
        result = ListHandler().prompt(
            list_spec, list(default) if default else None, registry
        )
        return set(result) if result else set()

    def serialize(self, value: Any) -> Any:
        return list(value) if isinstance(value, set) else value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return set(raw) if raw else set()


class DictHandler:
    """Handles dict[K, V] fields."""

    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.is_dict

    def prompt(
        self,
        spec: FieldSpec,
        default: Any | None = None,
        registry: TypeHandlerRegistry | None = None,
    ) -> Any:
        default_count = str(len(default)) if isinstance(default, dict) else "0"
        count_str = questionary.text(
            f"  How many entries for {spec.name}?",
            default=default_count,
            validate=lambda v: (
                True if v.strip().isdigit() else "Must be a non-negative integer"
            ),
        ).ask()
        count = int(count_str) if count_str else 0

        result: dict[Any, Any] = {}
        default_items = list(default.items()) if isinstance(default, dict) else []
        for i in range(count):
            key_default = str(default_items[i][0]) if i < len(default_items) else ""
            val_default = default_items[i][1] if i < len(default_items) else None

            key = questionary.text(
                f"  Key [{i}]:",
                default=key_default,
            ).ask()

            val_spec = FieldSpec(
                name=f"{spec.name}[{key}]",
                annotation=spec.value_type,
                inner_type=spec.value_type,
                is_required=True,
            )
            if registry:
                handler = registry.get_handler(val_spec)
                if handler:
                    result[key] = handler.prompt(val_spec, val_default)
            else:
                result[key] = questionary.text(f"  Value for '{key}':").ask()
        return result

    def serialize(self, value: Any) -> Any:
        return dict(value) if value else {}

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return dict(raw) if raw else {}


class UnionHandler:
    """Handles Union[A, B, C] fields by letting the user pick the concrete type."""

    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.is_union and not spec.is_optional

    def prompt(
        self,
        spec: FieldSpec,
        default: Any | None = None,
        registry: TypeHandlerRegistry | None = None,
    ) -> Any:
        type_names = []
        type_map: dict[str, type] = {}
        for tp in spec.union_types:
            name = tp.__name__ if hasattr(tp, "__name__") else str(tp)
            type_names.append(name)
            type_map[name] = tp

        default_name = None
        if default is not None and hasattr(type(default), "__name__"):
            default_name = type(default).__name__

        chosen_name = questionary.select(
            f"  {spec.name} - which type?",
            choices=type_names,
            default=default_name,
        ).ask()

        chosen_type = type_map[chosen_name]

        inner_spec = FieldSpec(
            name=spec.name,
            annotation=chosen_type,
            inner_type=chosen_type,
            is_required=True,
            is_pydantic_model=(
                isinstance(chosen_type, type) and issubclass(chosen_type, BaseModel)
            ),
            is_enum=(
                isinstance(chosen_type, type) and issubclass(chosen_type, enum.Enum)
            ),
        )
        if registry:
            handler = registry.get_handler(inner_spec)
            if handler:
                return handler.prompt(inner_spec, default)
        return None

    def serialize(self, value: Any) -> Any:
        return value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return raw


class PydanticModelHandler:
    """Handles nested Pydantic BaseModel fields by recursively prompting."""

    def can_handle(self, spec: FieldSpec) -> bool:
        return spec.is_pydantic_model

    def prompt(
        self,
        spec: FieldSpec,
        default: Any | None = None,
        registry: TypeHandlerRegistry | None = None,
        prompt_model_fn: Any | None = None,
    ) -> Any:
        if prompt_model_fn is None:
            return None

        default_dict = None
        if isinstance(default, BaseModel):
            default_dict = default.model_dump()
        elif isinstance(default, dict):
            default_dict = default

        return prompt_model_fn(
            spec.inner_type,
            defaults=default_dict,
            path=spec.name,
        )

    def serialize(self, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump()
        return value

    def deserialize(self, raw: Any, spec: FieldSpec) -> Any:
        return raw


class TypeHandlerRegistry:
    """Registry mapping field types to their handlers, in priority order."""

    def __init__(self) -> None:
        self._handlers: list[Any] = [
            OptionalHandler(),
            UnionHandler(),
            ListHandler(),
            SetHandler(),
            DictHandler(),
            BoolHandler(),
            EnumHandler(),
            LiteralHandler(),
            DecimalHandler(),
            IntHandler(),
            FloatHandler(),
            DatetimeHandler(),
            TimeHandler(),
            TimedeltaHandler(),
            PydanticModelHandler(),
            StrHandler(),
        ]

    def register(self, handler: Any, *, priority: bool = True) -> None:
        """Register a custom type handler.

        Args:
            handler: A handler implementing the TypeHandler protocol.
            priority: If True (default), insert at the front so it takes
                precedence over built-in handlers. If False, append to the end.
        """
        if priority:
            self._handlers.insert(0, handler)
        else:
            self._handlers.append(handler)

    def get_handler(self, spec: FieldSpec) -> Any | None:
        for handler in self._handlers:
            if handler.can_handle(spec):
                return handler
        return None
