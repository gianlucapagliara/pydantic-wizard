import datetime
from decimal import Decimal
from enum import Enum

from pydantic_wizard.introspection import FieldSpec
from pydantic_wizard.type_handlers import (
    BoolHandler,
    DatetimeHandler,
    DecimalHandler,
    EnumHandler,
    FloatHandler,
    IntHandler,
    LiteralHandler,
    StrHandler,
    TimedeltaHandler,
    TimeHandler,
    TypeHandlerRegistry,
)


class SampleEnum(Enum):
    X = "x"
    Y = "y"


class TestBoolHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", inner_type=bool)
        assert BoolHandler().can_handle(spec)

    def test_serialize(self):
        assert BoolHandler().serialize(True) is True
        assert BoolHandler().serialize(False) is False

    def test_deserialize(self):
        spec = FieldSpec(name="f", inner_type=bool)
        assert BoolHandler().deserialize(True, spec) is True


class TestStrHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", inner_type=str)
        assert StrHandler().can_handle(spec)

    def test_serialize(self):
        assert StrHandler().serialize("hello") == "hello"

    def test_deserialize(self):
        spec = FieldSpec(name="f", inner_type=str)
        assert StrHandler().deserialize("world", spec) == "world"


class TestIntHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", inner_type=int)
        assert IntHandler().can_handle(spec)

    def test_serialize(self):
        assert IntHandler().serialize(42) == 42

    def test_deserialize(self):
        spec = FieldSpec(name="f", inner_type=int)
        assert IntHandler().deserialize("10", spec) == 10


class TestFloatHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", inner_type=float)
        assert FloatHandler().can_handle(spec)

    def test_serialize(self):
        assert FloatHandler().serialize(3.14) == 3.14


class TestDecimalHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", inner_type=Decimal)
        assert DecimalHandler().can_handle(spec)

    def test_serialize_preserves_precision(self):
        assert DecimalHandler().serialize(Decimal("0.00001")) == "0.00001"

    def test_deserialize(self):
        spec = FieldSpec(name="f", inner_type=Decimal)
        result = DecimalHandler().deserialize("0.00001", spec)
        assert result == Decimal("0.00001")


class TestEnumHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", inner_type=SampleEnum, is_enum=True)
        assert EnumHandler().can_handle(spec)

    def test_serialize(self):
        assert EnumHandler().serialize(SampleEnum.X) == "x"

    def test_deserialize(self):
        spec = FieldSpec(name="f", inner_type=SampleEnum, is_enum=True)
        assert EnumHandler().deserialize("x", spec) == SampleEnum.X


class TestLiteralHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", is_literal=True)
        assert LiteralHandler().can_handle(spec)

    def test_serialize(self):
        assert LiteralHandler().serialize("aggressive") == "aggressive"


class TestDatetimeHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", inner_type=datetime.datetime)
        assert DatetimeHandler().can_handle(spec)

    def test_serialize(self):
        dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
        assert DatetimeHandler().serialize(dt) == "2024-01-15T10:30:00"

    def test_deserialize(self):
        spec = FieldSpec(name="f", inner_type=datetime.datetime)
        result = DatetimeHandler().deserialize("2024-01-15T10:30:00", spec)
        assert result == datetime.datetime(2024, 1, 15, 10, 30, 0)


class TestTimeHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", inner_type=datetime.time)
        assert TimeHandler().can_handle(spec)

    def test_serialize(self):
        t = datetime.time(10, 30, 0)
        assert TimeHandler().serialize(t) == "10:30:00"

    def test_deserialize(self):
        spec = FieldSpec(name="f", inner_type=datetime.time)
        result = TimeHandler().deserialize("10:30:00", spec)
        assert result == datetime.time(10, 30, 0)


class TestTimedeltaHandler:
    def test_can_handle(self):
        spec = FieldSpec(name="f", inner_type=datetime.timedelta)
        assert TimedeltaHandler().can_handle(spec)

    def test_serialize(self):
        td = datetime.timedelta(hours=1, minutes=30)
        assert TimedeltaHandler().serialize(td) == 5400.0

    def test_deserialize(self):
        spec = FieldSpec(name="f", inner_type=datetime.timedelta)
        result = TimedeltaHandler().deserialize(5400.0, spec)
        assert result == datetime.timedelta(seconds=5400)


class TestTypeHandlerRegistry:
    def test_finds_bool_handler(self):
        reg = TypeHandlerRegistry()
        spec = FieldSpec(name="f", inner_type=bool)
        handler = reg.get_handler(spec)
        assert handler is not None
        assert isinstance(handler, BoolHandler)

    def test_finds_str_handler(self):
        reg = TypeHandlerRegistry()
        spec = FieldSpec(name="f", inner_type=str)
        handler = reg.get_handler(spec)
        assert handler is not None
        assert isinstance(handler, StrHandler)

    def test_finds_decimal_handler(self):
        reg = TypeHandlerRegistry()
        spec = FieldSpec(name="f", inner_type=Decimal)
        handler = reg.get_handler(spec)
        assert handler is not None
        assert isinstance(handler, DecimalHandler)

    def test_finds_enum_handler(self):
        reg = TypeHandlerRegistry()
        spec = FieldSpec(name="f", inner_type=SampleEnum, is_enum=True)
        handler = reg.get_handler(spec)
        assert handler is not None
        assert isinstance(handler, EnumHandler)

    def test_optional_has_priority(self):
        from pydantic_wizard.type_handlers import OptionalHandler

        reg = TypeHandlerRegistry()
        spec = FieldSpec(name="f", inner_type=str, is_optional=True)
        handler = reg.get_handler(spec)
        assert handler is not None
        assert isinstance(handler, OptionalHandler)
