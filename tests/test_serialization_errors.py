"""Tests for serialization error paths and resolve_config_class."""

import pytest

from pydantic_wizard.exceptions import ConfigLoadError, ModelResolutionError
from pydantic_wizard.serialization import load_from_yaml, resolve_config_class


class TestResolveConfigClass:
    def test_valid_fqn(self):
        cls = resolve_config_class("pydantic.BaseModel")
        from pydantic import BaseModel

        assert cls is BaseModel

    def test_invalid_fqn_no_dot(self):
        with pytest.raises(ModelResolutionError, match="Invalid fully-qualified name"):
            resolve_config_class("NoDotHere")

    def test_nonexistent_module(self):
        with pytest.raises(ModelResolutionError, match="Cannot import module"):
            resolve_config_class("nonexistent.module.Class")

    def test_nonexistent_attribute(self):
        with pytest.raises(ModelResolutionError, match="has no attribute"):
            resolve_config_class("pydantic.NonExistentClass")

    def test_non_basemodel_class(self):
        with pytest.raises(ModelResolutionError, match="not a Pydantic BaseModel"):
            resolve_config_class("pathlib.Path")

    def test_error_is_pydantic_wizard_error(self):
        from pydantic_wizard.exceptions import PydanticWizardError

        with pytest.raises(PydanticWizardError):
            resolve_config_class("no_module")


class TestLoadFromYamlErrors:
    def test_nonexistent_file(self, tmp_path):
        with pytest.raises(ConfigLoadError, match="Failed to load"):
            load_from_yaml(tmp_path / "nonexistent.yaml")

    def test_invalid_yaml(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text(":\n  :\n    - [invalid yaml{{{")
        with pytest.raises(ConfigLoadError, match="Failed to load"):
            load_from_yaml(bad_file)

    def test_non_dict_yaml(self, tmp_path):
        list_file = tmp_path / "list.yaml"
        list_file.write_text("- item1\n- item2\n")
        with pytest.raises(ConfigLoadError, match="Expected a YAML mapping"):
            load_from_yaml(list_file)

    def test_yaml_with_no_metadata(self, tmp_path):
        plain = tmp_path / "plain.yaml"
        plain.write_text("key: value\n")
        model_type, fqn, data = load_from_yaml(plain)
        assert model_type == ""
        assert fqn == ""
        assert data == {}
