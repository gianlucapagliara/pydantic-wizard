"""Shared utilities for the Streamlit UI views."""

from __future__ import annotations

import io
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import yaml

from pydantic_wizard.serialization import (
    CONFIGURATION_KEY,
    METADATA_KEY,
    ModelConfigDumper,
    prepare_for_serialization,
)


def get_package_version() -> str:
    """Return the installed pydantic-wizard version."""
    try:
        return version("pydantic-wizard")
    except (ImportError, PackageNotFoundError):
        return "unknown"


def build_yaml(data: dict[str, Any], config_class: type, model_name: str) -> str:
    """Build a YAML string with metadata envelope."""
    prepared = prepare_for_serialization(data)
    config_fqn = f"{config_class.__module__}.{config_class.__qualname__}"
    document = {
        METADATA_KEY: {
            "model_type": model_name,
            "configuration_class": config_fqn,
            "version": get_package_version(),
        },
        CONFIGURATION_KEY: prepared,
    }
    buf = io.StringIO()
    yaml.dump(
        document,
        buf,
        Dumper=ModelConfigDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return buf.getvalue()
