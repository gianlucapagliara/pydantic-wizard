from __future__ import annotations

import datetime
import enum
import importlib
import logging
from decimal import Decimal
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from pydantic_wizard.exceptions import ConfigLoadError, ModelResolutionError

logger = logging.getLogger(__name__)

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
    if isinstance(value, list | tuple):
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


def prepare_for_serialization(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare a dict of Pydantic model data for YAML serialization.

    Applies pydantic-wizard's type converters (Decimal->str, Enum->value,
    datetime->ISO, set->sorted list, etc.) without coupling to the full
    serialize_to_yaml flow.
    """
    return _prepare_dict(data)


def dump_yaml(data: dict[str, Any], output_path: Path) -> None:
    """Write a dict to a YAML file using pydantic-wizard's ModelConfigDumper.

    This is a low-level function that uses the custom YAML dumper which handles
    Decimal, Enum, datetime, set, etc. The data should be passed through
    ``prepare_for_serialization`` first for full type normalization.
    """
    prepared = _prepare_dict(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(
            prepared,
            f,
            Dumper=ModelConfigDumper,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


def serialize_to_yaml(
    data: dict[str, Any],
    config_class: type[BaseModel],
    output_path: Path,
    model_name: str = "",
    include_metadata: bool = True,
) -> None:
    """Serialize configuration data to a YAML file.

    Args:
        data: Configuration data dict.
        config_class: The Pydantic model class for metadata.
        output_path: Destination file path.
        model_name: Optional model name for metadata.
        include_metadata: When True (default), wraps data in a metadata/configuration
            envelope. When False, writes just the configuration data at the top level.
    """
    prepared = _prepare_dict(data)

    if include_metadata:
        config_fqn = f"{config_class.__module__}.{config_class.__qualname__}"
        document: dict[str, Any] = {
            METADATA_KEY: {
                "model_type": model_name,
                "configuration_class": config_fqn,
                "version": _get_package_version(),
            },
            CONFIGURATION_KEY: prepared,
        }
    else:
        document = prepared

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

    Raises:
        ConfigLoadError: If the file cannot be read or parsed.
    """
    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        raise ConfigLoadError(f"Failed to load {path}: {e}") from e

    if not isinstance(raw, dict):
        raise ConfigLoadError(
            f"Expected a YAML mapping in {path}, got {type(raw).__name__}"
        )

    metadata = raw.get(METADATA_KEY, {})
    model_type = metadata.get("model_type", "")
    config_class_fqn = metadata.get("configuration_class", "")
    data = raw.get(CONFIGURATION_KEY, {})

    return model_type, config_class_fqn, data


def resolve_config_class(fqn: str) -> type[BaseModel]:
    """Import and return a configuration class from its fully qualified name.

    Raises:
        ModelResolutionError: If the class cannot be imported or is not a BaseModel.
    """
    module_path, _, class_name = fqn.rpartition(".")
    if not module_path:
        raise ModelResolutionError(f"Invalid fully-qualified name: {fqn!r}")
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ModelResolutionError(f"Cannot import module {module_path!r}: {e}") from e
    try:
        cls = getattr(module, class_name)
    except AttributeError as e:
        raise ModelResolutionError(
            f"Module {module_path!r} has no attribute {class_name!r}"
        ) from e
    if not isinstance(cls, type) or not issubclass(cls, BaseModel):
        raise ModelResolutionError(f"{fqn} is not a Pydantic BaseModel subclass")
    return cls


def _get_package_version() -> str:
    try:
        from importlib.metadata import version

        return version("pydantic-wizard")
    except (ImportError, PackageNotFoundError):
        return "unknown"
