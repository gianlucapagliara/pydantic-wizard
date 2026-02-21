from decimal import Decimal

import yaml

from pydantic_wizard.serialization import (
    CONFIGURATION_KEY,
    METADATA_KEY,
    load_from_yaml,
    serialize_to_yaml,
)
from tests.conftest import SampleEnum, SimpleConfig


class TestSerializeToYaml:
    def test_writes_valid_yaml(self, tmp_path):
        data = {
            "label": "test",
            "count": 10,
            "enabled": True,
            "ratio": 1.5,
            "amount": "0.01",
        }
        output = tmp_path / "config.yaml"
        serialize_to_yaml(data, SimpleConfig, output, model_name="TestModel")

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert METADATA_KEY in loaded
        assert CONFIGURATION_KEY in loaded
        assert loaded[METADATA_KEY]["model_type"] == "TestModel"

    def test_preserves_decimal_as_string(self, tmp_path):
        data = {"amount": Decimal("0.00001")}
        output = tmp_path / "config.yaml"
        serialize_to_yaml(data, SimpleConfig, output)

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert loaded[CONFIGURATION_KEY]["amount"] == "0.00001"

    def test_serializes_enum_as_value(self, tmp_path):
        data = {"mode": SampleEnum.OPTION_B}
        output = tmp_path / "config.yaml"
        serialize_to_yaml(data, SimpleConfig, output)

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert loaded[CONFIGURATION_KEY]["mode"] == "b"

    def test_serializes_none(self, tmp_path):
        data = {"optional_field": None}
        output = tmp_path / "config.yaml"
        serialize_to_yaml(data, SimpleConfig, output)

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert loaded[CONFIGURATION_KEY]["optional_field"] is None

    def test_creates_parent_directories(self, tmp_path):
        output = tmp_path / "nested" / "dir" / "config.yaml"
        serialize_to_yaml({"label": "test"}, SimpleConfig, output)
        assert output.exists()


class TestLoadFromYaml:
    def test_loads_metadata_and_data(self, tmp_path):
        data = {
            "label": "loaded",
            "count": 42,
        }
        output = tmp_path / "config.yaml"
        serialize_to_yaml(data, SimpleConfig, output, model_name="TestModel")

        model_type, config_fqn, loaded_data = load_from_yaml(output)

        assert model_type == "TestModel"
        assert "SimpleConfig" in config_fqn
        assert loaded_data["label"] == "loaded"
        assert loaded_data["count"] == 42


class TestRoundTrip:
    def test_simple_config_roundtrip(self, tmp_path):
        original_data = {
            "label": "roundtrip",
            "count": 7,
            "enabled": False,
            "ratio": 3.14,
            "amount": "0.001",
        }
        output = tmp_path / "config.yaml"
        serialize_to_yaml(original_data, SimpleConfig, output, model_name="Test")

        _, _, loaded_data = load_from_yaml(output)

        assert loaded_data["label"] == original_data["label"]
        assert loaded_data["count"] == original_data["count"]
        assert loaded_data["enabled"] == original_data["enabled"]
        # YAML may load amount as string since we serialize Decimal as string
        assert str(loaded_data["amount"]) == str(original_data["amount"])

    def test_nested_model_roundtrip(self, tmp_path):
        data = {
            "inner": {"name": "nested", "value": 42},
            "tags": ["a", "b"],
        }
        output = tmp_path / "config.yaml"
        serialize_to_yaml(data, SimpleConfig, output)

        _, _, loaded = load_from_yaml(output)
        assert loaded["inner"]["name"] == "nested"
        assert loaded["inner"]["value"] == 42
        assert loaded["tags"] == ["a", "b"]
