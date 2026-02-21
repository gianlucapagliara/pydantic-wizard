from decimal import Decimal

from pydantic_wizard.introspection import (
    get_type_display_name,
    introspect_model,
)
from tests.conftest import (
    ComplexConfig,
    InnerModel,
    SampleEnum,
    SimpleConfig,
)


class TestIntrospectSimpleModel:
    def test_all_fields_extracted(self):
        specs = introspect_model(SimpleConfig)
        names = [s.name for s in specs]
        assert "label" in names
        assert "count" in names
        assert "enabled" in names
        assert "ratio" in names
        assert "amount" in names

    def test_str_field(self):
        specs = {s.name: s for s in introspect_model(SimpleConfig)}
        label = specs["label"]
        assert label.inner_type is str
        assert label.is_required is True
        assert label.description == "A label"

    def test_int_field_with_constraints(self):
        specs = {s.name: s for s in introspect_model(SimpleConfig)}
        count = specs["count"]
        assert count.inner_type is int
        assert count.is_required is False
        assert count.default == 5
        assert count.constraints.get("ge") == 0

    def test_bool_field(self):
        specs = {s.name: s for s in introspect_model(SimpleConfig)}
        enabled = specs["enabled"]
        assert enabled.inner_type is bool
        assert enabled.default is True

    def test_decimal_field(self):
        specs = {s.name: s for s in introspect_model(SimpleConfig)}
        amount = specs["amount"]
        assert amount.inner_type is Decimal
        assert amount.default == Decimal("0.01")


class TestIntrospectComplexModel:
    def test_enum_field(self):
        specs = {s.name: s for s in introspect_model(ComplexConfig)}
        mode = specs["mode"]
        assert mode.is_enum is True

    def test_literal_field(self):
        specs = {s.name: s for s in introspect_model(ComplexConfig)}
        strategy = specs["strategy"]
        assert strategy.is_literal is True

    def test_nested_pydantic_model(self):
        specs = {s.name: s for s in introspect_model(ComplexConfig)}
        inner = specs["inner"]
        assert inner.is_pydantic_model is True
        assert inner.inner_type is InnerModel

    def test_optional_model(self):
        specs = {s.name: s for s in introspect_model(ComplexConfig)}
        opt = specs["optional_inner"]
        assert opt.is_optional is True
        assert opt.is_pydantic_model is True
        assert opt.is_required is False

    def test_list_of_str(self):
        specs = {s.name: s for s in introspect_model(ComplexConfig)}
        tags = specs["tags"]
        assert tags.is_list is True
        assert tags.inner_type is str

    def test_list_of_model(self):
        specs = {s.name: s for s in introspect_model(ComplexConfig)}
        scores = specs["scores"]
        assert scores.is_list is True
        assert scores.inner_type is InnerModel

    def test_set_of_enum(self):
        specs = {s.name: s for s in introspect_model(ComplexConfig)}
        modifiers = specs["modifiers"]
        assert modifiers.is_set is True
        assert modifiers.inner_type is SampleEnum

    def test_dict_field(self):
        specs = {s.name: s for s in introspect_model(ComplexConfig)}
        metadata = specs["metadata"]
        assert metadata.is_dict is True
        assert metadata.key_type is str
        assert metadata.value_type is Decimal

    def test_union_field(self):
        specs = {s.name: s for s in introspect_model(ComplexConfig)}
        alt = specs["alt"]
        assert alt.is_optional is True
        assert alt.is_union is True
        assert InnerModel in alt.union_types
        assert SimpleConfig in alt.union_types


class TestGetTypeDisplayName:
    def test_simple_types(self):
        assert get_type_display_name(str) == "str"
        assert get_type_display_name(int) == "int"
        assert get_type_display_name(bool) == "bool"

    def test_optional(self):
        result = get_type_display_name(int | None)
        assert "int" in result
        assert "None" in result

    def test_list(self):
        assert get_type_display_name(list[str]) == "list[str]"

    def test_enum(self):
        assert get_type_display_name(SampleEnum) == "SampleEnum"
