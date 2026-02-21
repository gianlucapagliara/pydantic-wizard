from decimal import Decimal
from enum import Enum
from typing import Literal

import pytest
from pydantic import BaseModel, Field


class SampleEnum(Enum):
    OPTION_A = "a"
    OPTION_B = "b"
    OPTION_C = "c"


class InnerModel(BaseModel):
    name: str = Field(description="Name of the inner model")
    value: int = Field(default=0, ge=0, le=100, description="A bounded integer")


class SimpleConfig(BaseModel):
    """A simple config with primitive fields for testing."""

    label: str = Field(description="A label")
    count: int = Field(default=5, ge=0)
    enabled: bool = Field(default=True)
    ratio: float = Field(default=1.0)
    amount: Decimal = Field(default=Decimal("0.01"), ge=0)


class ComplexConfig(BaseModel):
    """A complex config for testing nested, optional, union, enum, list fields."""

    name: str
    mode: SampleEnum = SampleEnum.OPTION_A
    strategy: Literal["aggressive", "passive", "balanced"] = "balanced"
    inner: InnerModel = Field(
        default_factory=lambda: InnerModel(name="default", value=10)
    )
    optional_inner: InnerModel | None = None
    tags: list[str] = Field(default_factory=list)
    scores: list[InnerModel] = Field(default_factory=list)
    modifiers: set[SampleEnum] = Field(default_factory=set)
    metadata: dict[str, Decimal] = Field(default_factory=dict)
    alt: InnerModel | SimpleConfig | None = None


@pytest.fixture
def simple_config_class():
    return SimpleConfig


@pytest.fixture
def complex_config_class():
    return ComplexConfig


@pytest.fixture
def inner_model_class():
    return InnerModel


@pytest.fixture
def sample_simple_data():
    return {
        "label": "test",
        "count": 10,
        "enabled": False,
        "ratio": 2.5,
        "amount": Decimal("1.5"),
    }


@pytest.fixture
def sample_complex_data():
    return {
        "name": "test-model",
        "mode": "a",
        "strategy": "aggressive",
        "inner": {"name": "nested", "value": 42},
        "optional_inner": None,
        "tags": ["fast", "reliable"],
        "scores": [{"name": "s1", "value": 10}],
        "modifiers": ["a", "b"],
        "metadata": {"key1": "100.5"},
        "alt": None,
    }
