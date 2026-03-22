import datetime
from decimal import Decimal

import yaml

from pydantic_wizard.serialization import (
    CONFIGURATION_KEY,
    METADATA_KEY,
    dump_yaml,
    load_from_yaml,
    prepare_for_serialization,
    serialize_to_yaml,
)
from tests.conftest import InnerModel, SampleEnum, SimpleConfig


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


class TestSerializeToYamlWithoutMetadata:
    def test_no_metadata_produces_flat_yaml(self, tmp_path):
        data = {
            "label": "flat",
            "count": 5,
            "enabled": True,
        }
        output = tmp_path / "config.yaml"
        serialize_to_yaml(data, SimpleConfig, output, include_metadata=False)

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert METADATA_KEY not in loaded
        assert CONFIGURATION_KEY not in loaded
        assert loaded["label"] == "flat"
        assert loaded["count"] == 5
        assert loaded["enabled"] is True

    def test_no_metadata_still_prepares_types(self, tmp_path):
        data = {
            "amount": Decimal("0.005"),
            "mode": SampleEnum.OPTION_A,
        }
        output = tmp_path / "config.yaml"
        serialize_to_yaml(data, SimpleConfig, output, include_metadata=False)

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert loaded["amount"] == "0.005"
        assert loaded["mode"] == "a"

    def test_include_metadata_true_is_default(self, tmp_path):
        data = {"label": "test"}
        output = tmp_path / "config.yaml"
        serialize_to_yaml(data, SimpleConfig, output)

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert METADATA_KEY in loaded
        assert CONFIGURATION_KEY in loaded


class TestPrepareForSerialization:
    def test_converts_decimal(self):
        result = prepare_for_serialization({"amount": Decimal("1.23")})
        assert result["amount"] == "1.23"

    def test_converts_enum(self):
        result = prepare_for_serialization({"mode": SampleEnum.OPTION_B})
        assert result["mode"] == "b"

    def test_converts_datetime(self):
        dt = datetime.datetime(2025, 1, 15, 10, 30, 0)
        result = prepare_for_serialization({"ts": dt})
        assert result["ts"] == dt.isoformat()

    def test_converts_set(self):
        result = prepare_for_serialization({"tags": {3, 1, 2}})
        assert result["tags"] == [1, 2, 3]

    def test_converts_nested_model(self):
        inner = InnerModel(name="nested", value=42)
        result = prepare_for_serialization({"inner": inner})
        assert result["inner"]["name"] == "nested"
        assert result["inner"]["value"] == 42

    def test_preserves_primitives(self):
        data = {"s": "hello", "i": 5, "f": 1.5, "b": True, "n": None}
        result = prepare_for_serialization(data)
        assert result == data

    def test_nested_dict_with_mixed_types(self):
        data = {
            "outer": {
                "amount": Decimal("9.99"),
                "mode": SampleEnum.OPTION_C,
            }
        }
        result = prepare_for_serialization(data)
        assert result["outer"]["amount"] == "9.99"
        assert result["outer"]["mode"] == "c"


class TestDumpYaml:
    def test_writes_valid_yaml(self, tmp_path):
        data = {"label": "test", "count": 10}
        output = tmp_path / "out.yaml"
        dump_yaml(data, output)

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert loaded["label"] == "test"
        assert loaded["count"] == 10

    def test_handles_decimal_and_enum(self, tmp_path):
        data = {
            "amount": Decimal("0.001"),
            "mode": SampleEnum.OPTION_A,
        }
        output = tmp_path / "out.yaml"
        dump_yaml(data, output)

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert loaded["amount"] == "0.001"
        assert loaded["mode"] == "a"

    def test_creates_parent_directories(self, tmp_path):
        output = tmp_path / "deep" / "nested" / "out.yaml"
        dump_yaml({"key": "value"}, output)
        assert output.exists()

    def test_handles_datetime_and_set(self, tmp_path):
        dt = datetime.datetime(2025, 6, 1, 12, 0, 0)
        data = {"ts": dt, "tags": {"b", "a"}}
        output = tmp_path / "out.yaml"
        dump_yaml(data, output)

        with open(output) as f:
            loaded = yaml.safe_load(f)

        assert loaded["ts"] == dt.isoformat()
        assert loaded["tags"] == ["a", "b"]


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
