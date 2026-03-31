"""Map FieldSpec types to Streamlit widgets."""

from __future__ import annotations

import datetime
import enum
from decimal import Decimal, InvalidOperation
from typing import Any, get_args

import streamlit as st
from pydantic import BaseModel

from pydantic_wizard.introspection import FieldSpec, get_type_display_name


def render_field(spec: FieldSpec, key_prefix: str, default: Any = None) -> Any:
    """Render the appropriate Streamlit widget for a FieldSpec and return its value."""
    key = f"{key_prefix}.{spec.name}" if key_prefix else spec.name

    # Dispatch in priority order (mirrors TypeHandlerRegistry)
    if spec.is_optional:
        return _render_optional(spec, key, default)
    if spec.is_union:
        return _render_union(spec, key, default)
    if spec.is_list:
        return _render_list(spec, key, default)
    if spec.is_set:
        return _render_set(spec, key, default)
    if spec.is_dict:
        return _render_dict(spec, key, default)
    if spec.is_enum:
        return _render_enum(spec, key, default)
    if spec.is_literal:
        return _render_literal(spec, key, default)
    if spec.is_pydantic_model:
        return _render_pydantic_model(spec, key, default)

    # Scalar types
    inner = spec.inner_type
    if inner is bool:
        return _render_bool(spec, key, default)
    if inner is int:
        return _render_int(spec, key, default)
    if inner is float:
        return _render_float(spec, key, default)
    if inner is Decimal:
        return _render_decimal(spec, key, default)
    if inner is datetime.datetime:
        return _render_datetime(spec, key, default)
    if inner is datetime.time:
        return _render_time(spec, key, default)
    if inner is datetime.timedelta:
        return _render_timedelta(spec, key, default)

    # Fallback: string input
    return _render_str(spec, key, default)


# ── Scalar renderers ──────────────────────────────────────────────────


def _render_bool(spec: FieldSpec, key: str, default: Any) -> bool:
    default_val = default if isinstance(default, bool) else False
    result: bool = st.checkbox(
        _label(spec),
        value=default_val,
        key=key,
        help=spec.description,
    )
    return result


def _render_str(spec: FieldSpec, key: str, default: Any) -> str:
    default_str = str(default) if default is not None else ""
    help_parts: list[str] = []
    if spec.description:
        help_parts.append(spec.description)
    c = spec.constraints
    if "min_length" in c:
        help_parts.append(f"min length: {c['min_length']}")
    if "max_length" in c:
        help_parts.append(f"max length: {c['max_length']}")
    if "pattern" in c:
        help_parts.append(f"pattern: `{c['pattern']}`")
    help_text = " | ".join(help_parts) if help_parts else None
    result: str = st.text_input(
        _label(spec),
        value=default_str,
        key=key,
        help=help_text,
    )
    return result


def _render_int(spec: FieldSpec, key: str, default: Any) -> int:
    bounds = _numeric_bounds(spec, is_int=True)
    default_val = int(default) if default is not None else bounds.get("min_value", 0)
    return int(
        st.number_input(
            _label(spec),
            value=default_val,
            step=1,
            key=key,
            help=spec.description,
            **bounds,
        )
    )


def _render_float(spec: FieldSpec, key: str, default: Any) -> float:
    bounds = _numeric_bounds(spec, is_int=False)
    default_val = (
        float(default) if default is not None else bounds.get("min_value", 0.0)
    )
    return float(
        st.number_input(
            _label(spec),
            value=default_val,
            step=0.1,
            key=key,
            help=spec.description,
            **bounds,
        )
    )


def _render_decimal(spec: FieldSpec, key: str, default: Any) -> Decimal:
    default_str = str(default) if default is not None else ""
    raw = st.text_input(
        _label(spec, extra="decimal"),
        value=default_str,
        key=key,
        help=spec.description,
    )
    try:
        return Decimal(raw) if raw.strip() else Decimal("0")
    except InvalidOperation:
        st.warning(f"Invalid decimal for **{spec.name}**, using 0")
        return Decimal("0")


# ── Temporal renderers ────────────────────────────────────────────────


def _render_datetime(spec: FieldSpec, key: str, default: Any) -> datetime.datetime:
    col1, col2 = st.columns(2)
    if isinstance(default, datetime.datetime):
        default_date = default.date()
        default_time = default.time()
    else:
        default_date = datetime.date.today()
        default_time = datetime.time(0, 0)

    with col1:
        d = st.date_input(
            f"{spec.name} (date)",
            value=default_date,
            key=f"{key}.__date",
            help=spec.description,
        )
    with col2:
        t = st.time_input(
            f"{spec.name} (time)",
            value=default_time,
            key=f"{key}.__time",
            help=spec.description,
        )
    return datetime.datetime.combine(d, t)


def _render_time(spec: FieldSpec, key: str, default: Any) -> datetime.time:
    default_time = (
        default if isinstance(default, datetime.time) else datetime.time(0, 0)
    )
    result: datetime.time = st.time_input(
        _label(spec),
        value=default_time,
        key=key,
        help=spec.description,
    )
    return result


def _render_timedelta(spec: FieldSpec, key: str, default: Any) -> datetime.timedelta:
    default_seconds = (
        int(default.total_seconds()) if isinstance(default, datetime.timedelta) else 0
    )
    seconds = st.number_input(
        _label(spec, extra="total seconds"),
        value=default_seconds,
        min_value=0,
        step=1,
        key=key,
        help=spec.description,
    )
    return datetime.timedelta(seconds=int(seconds))


# ── Choice renderers ──────────────────────────────────────────────────


def _render_enum(spec: FieldSpec, key: str, default: Any) -> Any:
    enum_type = spec.inner_type
    if not isinstance(enum_type, type) or not issubclass(enum_type, enum.Enum):
        return _render_str(spec, key, default)

    members = list(enum_type)
    labels = [str(m.value) for m in members]
    default_idx = 0
    if isinstance(default, enum_type):
        try:
            default_idx = members.index(default)
        except ValueError:
            pass

    selected_label = st.selectbox(
        _label(spec),
        options=labels,
        index=default_idx,
        key=key,
        help=spec.description,
    )
    # Map back to enum member
    for m in members:
        if str(m.value) == selected_label:
            return m
    return members[0]


def _render_literal(spec: FieldSpec, key: str, default: Any) -> Any:
    choices = list(get_args(spec.annotation))
    if not choices:
        choices = list(spec.args)
    labels = [str(c) for c in choices]
    default_idx = 0
    if default in choices:
        default_idx = choices.index(default)

    selected = st.selectbox(
        _label(spec),
        options=labels,
        index=default_idx,
        key=key,
        help=spec.description,
    )
    # Return the original typed value
    idx = labels.index(selected) if selected in labels else 0
    return choices[idx]


# ── Composite renderers ──────────────────────────────────────────────


def _render_optional(spec: FieldSpec, key: str, default: Any) -> Any:
    enabled = st.checkbox(
        f"Enable {spec.name}?",
        value=default is not None,
        key=f"{key}.__enabled",
        help=f"Optional: {get_type_display_name(spec.annotation)}",
    )
    if not enabled:
        return None

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
    return render_field(inner_spec, key + ".__inner", default)


def _render_list(spec: FieldSpec, key: str, default: Any) -> list[Any]:
    count_key = f"{key}.__count"
    default_list = default if isinstance(default, list) else []
    if count_key not in st.session_state:
        st.session_state[count_key] = len(default_list) if default_list else 0

    st.markdown(f"**{spec.name}** — `{get_type_display_name(spec.annotation)}`")
    if spec.description:
        st.caption(spec.description)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add item", key=f"{key}.__add"):
            st.session_state[count_key] += 1
            st.rerun()
    with col2:
        if st.button("Remove last", key=f"{key}.__remove"):
            if st.session_state[count_key] > 0:
                st.session_state[count_key] -= 1
                st.rerun()

    items: list[Any] = []
    for i in range(st.session_state[count_key]):
        item_default = default_list[i] if i < len(default_list) else None
        inner_spec = _make_inner_spec(spec, f"{spec.name}[{i}]")
        items.append(render_field(inner_spec, f"{key}.{i}", item_default))

    return items


def _render_set(spec: FieldSpec, key: str, default: Any) -> set[Any]:
    inner = spec.inner_type
    default_set = set(default) if isinstance(default, set | list) else set()

    # Enum inner type: use multiselect
    if isinstance(inner, type) and issubclass(inner, enum.Enum):
        members = list(inner)
        labels = [str(m.value) for m in members]
        default_labels = [str(m.value) for m in default_set if isinstance(m, inner)]
        selected = st.multiselect(
            _label(spec),
            options=labels,
            default=default_labels,
            key=key,
            help=spec.description,
        )
        result: set[Any] = set()
        for label in selected:
            for m in members:
                if str(m.value) == label:
                    result.add(m)
                    break
        return result

    # Non-enum: render like a list, then deduplicate
    list_spec = FieldSpec(
        name=spec.name,
        annotation=spec.annotation,
        inner_type=spec.inner_type,
        is_list=True,
        is_required=spec.is_required,
        description=spec.description,
        constraints=spec.constraints,
    )
    result_list = _render_list(list_spec, key, list(default_set))
    return set(result_list)


def _render_dict(spec: FieldSpec, key: str, default: Any) -> dict[Any, Any]:
    count_key = f"{key}.__count"
    default_dict = default if isinstance(default, dict) else {}
    default_items = list(default_dict.items())
    if count_key not in st.session_state:
        st.session_state[count_key] = len(default_items)

    st.markdown(f"**{spec.name}** — `{get_type_display_name(spec.annotation)}`")
    if spec.description:
        st.caption(spec.description)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add entry", key=f"{key}.__add"):
            st.session_state[count_key] += 1
            st.rerun()
    with col2:
        if st.button("Remove last", key=f"{key}.__remove"):
            if st.session_state[count_key] > 0:
                st.session_state[count_key] -= 1
                st.rerun()

    result: dict[Any, Any] = {}
    for i in range(st.session_state[count_key]):
        key_default = str(default_items[i][0]) if i < len(default_items) else ""
        val_default = default_items[i][1] if i < len(default_items) else None

        kcol, vcol = st.columns(2)
        with kcol:
            k = st.text_input(f"Key [{i}]", value=key_default, key=f"{key}.{i}.__key")
        with vcol:
            val_spec = FieldSpec(
                name=f"{spec.name}[{k or i}]",
                annotation=spec.value_type,
                inner_type=spec.value_type,
                is_required=True,
            )
            v = render_field(val_spec, f"{key}.{i}.__val", val_default)

        if k:
            result[k] = v

    return result


def _render_union(spec: FieldSpec, key: str, default: Any) -> Any:
    type_names: list[str] = []
    type_map: dict[str, type] = {}
    for tp in spec.union_types:
        name = tp.__name__ if hasattr(tp, "__name__") else str(tp)
        type_names.append(name)
        type_map[name] = tp

    default_idx = 0
    if default is not None and hasattr(type(default), "__name__"):
        default_name = type(default).__name__
        if default_name in type_names:
            default_idx = type_names.index(default_name)

    chosen_name = st.selectbox(
        f"{spec.name} — choose type",
        options=type_names,
        index=default_idx,
        key=f"{key}.__union_type",
        help=spec.description,
    )
    if chosen_name is None:
        chosen_name = type_names[0]

    chosen_type = type_map[chosen_name]
    inner_spec = FieldSpec(
        name=spec.name,
        annotation=chosen_type,
        inner_type=chosen_type,
        is_required=True,
        is_pydantic_model=(
            isinstance(chosen_type, type) and issubclass(chosen_type, BaseModel)
        ),
        is_enum=(isinstance(chosen_type, type) and issubclass(chosen_type, enum.Enum)),
    )
    return render_field(inner_spec, f"{key}.__union_val", default)


def _render_pydantic_model(spec: FieldSpec, key: str, default: Any) -> dict[str, Any]:
    # Lazy import to avoid circular dependency
    from pydantic_wizard.streamlit_ui.model_form import render_model_form

    model_class = spec.inner_type
    default_dict: dict[str, Any] | None = None
    if isinstance(default, BaseModel):
        default_dict = default.model_dump()
    elif isinstance(default, dict):
        default_dict = default

    with st.expander(f"{spec.name} ({model_class.__name__})", expanded=True):
        result: dict[str, Any] = render_model_form(
            model_class, defaults=default_dict, key_prefix=key
        )
        return result


# ── Helpers ───────────────────────────────────────────────────────────


def _label(spec: FieldSpec, extra: str | None = None) -> str:
    """Build a widget label from a FieldSpec."""
    type_name = get_type_display_name(spec.annotation)
    parts = [spec.name]
    if extra:
        parts.append(f"({extra})")
    elif type_name:
        parts.append(f"({type_name})")
    if spec.is_required:
        parts.append("*")
    return " ".join(parts)


def _numeric_bounds(spec: FieldSpec, *, is_int: bool) -> dict[str, Any]:
    """Convert FieldSpec constraints to st.number_input kwargs.

    For integers, ``gt``/``lt`` are adjusted by +1/-1 to become inclusive bounds.
    For floats, ``gt``/``lt`` are passed as-is since Streamlit has no exclusive
    bound option and adjusting by epsilon is unreliable.
    """
    kwargs: dict[str, Any] = {}
    c = spec.constraints
    if "ge" in c:
        kwargs["min_value"] = int(c["ge"]) if is_int else float(c["ge"])
    elif "gt" in c:
        kwargs["min_value"] = int(c["gt"]) + 1 if is_int else float(c["gt"])
    if "le" in c:
        kwargs["max_value"] = int(c["le"]) if is_int else float(c["le"])
    elif "lt" in c:
        kwargs["max_value"] = int(c["lt"]) - 1 if is_int else float(c["lt"])
    return kwargs


def _make_inner_spec(spec: FieldSpec, name: str) -> FieldSpec:
    """Create an inner FieldSpec for collection item rendering."""
    inner = spec.inner_type
    return FieldSpec(
        name=name,
        annotation=inner,
        inner_type=inner,
        is_required=True,
        is_optional=False,
        is_pydantic_model=(isinstance(inner, type) and issubclass(inner, BaseModel)),
        is_enum=(isinstance(inner, type) and issubclass(inner, enum.Enum)),
    )
