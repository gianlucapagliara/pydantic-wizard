from __future__ import annotations

import datetime
import enum
import importlib
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

METADATA_KEY = "_metadata"
CONFIGURATION_KEY = "configuration"
UNION_TYPE_KEY = "_type"


class ModelConfigDumper(yaml.SafeDumper):
    """Custom YAML dumper that handles Pydantic model types."""

    def ignore_aliases(self, data: Any) -> bool:
        return True


def _represent_decimal(dumper: yaml.SafeDumper, data: Decimal) -> Any:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


def _represent_enum(dumper: yaml.SafeDumper, data: enum.Enum) -> Any:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data.value))


def _represent_set(dumper: yaml.SafeDumper, data: set[Any]) -> Any:
    return dumper.represent_sequence("tag:yaml.org,2002:seq", sorted(data, key=str))


def _represent_datetime(dumper: yaml.SafeDumper, data: datetime.datetime) -> Any:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data.isoformat())


def _represent_time(dumper: yaml.SafeDumper, data: datetime.time) -> Any:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data.isoformat())


def _represent_timedelta(dumper: yaml.SafeDumper, data: datetime.timedelta) -> Any:
    return dumper.represent_scalar("tag:yaml.org,2002:float", str(data.total_seconds()))


# Register representers
ModelConfigDumper.add_representer(Decimal, _represent_decimal)
ModelConfigDumper.add_representer(set, _represent_set)
ModelConfigDumper.add_representer(datetime.datetime, _represent_datetime)
ModelConfigDumper.add_representer(datetime.time, _represent_time)
ModelConfigDumper.add_representer(datetime.timedelta, _represent_timedelta)

# Register all Enum subclasses via a multi-representer
ModelConfigDumper.add_multi_representer(enum.Enum, _represent_enum)


def _prepare_value(value: Any) -> Any:
    """Recursively convert a value to a YAML-serializable form."""
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return _prepare_dict(value.model_dump())
    if isinstance(value, dict):
        return _prepare_dict(value)
    if isinstance(value, (list, tuple)):
        return [_prepare_value(v) for v in value]
    if isinstance(value, set):
        return [_prepare_value(v) for v in sorted(value, key=str)]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.time):
        return value.isoformat()
    if isinstance(value, datetime.timedelta):
        return value.total_seconds()
    return value


def _prepare_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively prepare a dict for YAML serialization."""
    return {k: _prepare_value(v) for k, v in data.items()}


def serialize_to_yaml(
    data: dict[str, Any],
    config_class: type[BaseModel],
    output_path: Path,
    model_name: str = "",
) -> None:
    """Serialize configuration data to a YAML file with metadata."""
    config_fqn = f"{config_class.__module__}.{config_class.__qualname__}"

    document: dict[str, Any] = {
        METADATA_KEY: {
            "model_type": model_name,
            "configuration_class": config_fqn,
            "version": _get_package_version(),
        },
        CONFIGURATION_KEY: _prepare_dict(data),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(
            document,
            f,
            Dumper=ModelConfigDumper,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


def load_from_yaml(path: Path) -> tuple[str, str, dict[str, Any]]:
    """Load a YAML config file and return (model_type, config_class_fqn, data).

    Returns:
        Tuple of (model_type, configuration_class FQN, configuration data dict).
    """
    with open(path) as f:
        raw = yaml.safe_load(f)

    metadata = raw.get(METADATA_KEY, {})
    model_type = metadata.get("model_type", "")
    config_class_fqn = metadata.get("configuration_class", "")
    data = raw.get(CONFIGURATION_KEY, {})

    return model_type, config_class_fqn, data


def resolve_config_class(fqn: str) -> type[BaseModel]:
    """Import and return a configuration class from its fully qualified name."""
    module_path, _, class_name = fqn.rpartition(".")
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    if not isinstance(cls, type) or not issubclass(cls, BaseModel):
        raise ValueError(f"{fqn} is not a Pydantic BaseModel subclass")
    return cls


def _get_package_version() -> str:
    try:
        from importlib.metadata import version

        return version("pydantic-wizard")
    except Exception:
        return "unknown"
