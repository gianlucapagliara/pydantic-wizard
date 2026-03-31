"""Example complex configuration model for testing the Streamlit web UI.

Inspired by a real trading agent configuration with nested models, enums,
literals, optionals, sets, dicts, decimals, and datetime fields.

Usage:
    pydantic-wizard web
    # Then enter: examples.trading_config.MirrorExecutorConfig
"""

from __future__ import annotations

import datetime
import enum
from decimal import Decimal

from pydantic import BaseModel, Field


class Exchange(str, enum.Enum):
    BINANCE = "binance"
    KRAKEN = "kraken"
    COINBASE = "coinbase"
    BYBIT = "bybit"


class OrderModifier(str, enum.Enum):
    POST_ONLY = "post_only"
    REDUCE_ONLY = "reduce_only"
    IOC = "ioc"
    FOK = "fok"


class OptimizationType(str, enum.Enum):
    MIRROR = "mirror"
    SPREAD = "spread"
    AGGRESSIVE = "aggressive"


class MarketConfig(BaseModel):
    exchange: Exchange = Field(description="Target exchange")
    symbol: str = Field(description="Trading pair symbol, e.g. BTC/USDT")
    base_currency: str = Field(default="BTC", description="Base currency")
    quote_currency: str = Field(default="USDT", description="Quote currency")


class AccountConfig(BaseModel):
    exchange: Exchange = Field(description="Account exchange")
    api_label: str = Field(description="Label for the API key to use")
    subaccount: str | None = Field(default=None, description="Subaccount name if any")


class SpreadConfig(BaseModel):
    amount: Decimal = Field(
        default=Decimal("0.001"), description="Spread amount as a decimal fraction"
    )
    is_percentage: bool = Field(
        default=True, description="Whether the amount is a percentage"
    )


class DecayConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable time-based decay")
    half_life_seconds: int = Field(
        default=300, ge=1, description="Decay half-life in seconds"
    )
    min_spread: Decimal = Field(
        default=Decimal("0.0001"), description="Minimum spread after decay"
    )


class OptimizationConfig(BaseModel):
    type: OptimizationType = Field(
        default=OptimizationType.MIRROR, description="Optimization strategy type"
    )
    tolerance: SpreadConfig = Field(
        default_factory=SpreadConfig, description="Price tolerance configuration"
    )
    spread: SpreadConfig = Field(
        default_factory=lambda: SpreadConfig(amount=Decimal("-1")),
        description="Spread configuration",
    )
    decay: DecayConfig | None = Field(
        default=None, description="Optional decay configuration"
    )


class OrderExecutionConfig(BaseModel):
    account: AccountConfig = Field(description="Account to execute on")
    market: MarketConfig = Field(description="Market to trade")
    max_slippage: Decimal = Field(
        default=Decimal("0.005"), description="Max allowed slippage"
    )


class TakerConfig(BaseModel):
    account: AccountConfig = Field(description="Taker account")
    market: MarketConfig = Field(description="Taker market")
    target_leverage: int | None = Field(
        default=1, description="Target leverage (None for spot)"
    )
    check_balance: bool = Field(
        default=True, description="Check balance before placing orders"
    )
    reduce_if_no_balance: bool = Field(
        default=True,
        description="Reduce order amount if insufficient balance",
    )
    optimization: OptimizationConfig | None = Field(
        default=None,
        description="Optional price optimization for taker orders",
    )


class ConversionPriceConfig(BaseModel):
    use_conversion: bool = Field(
        default=False, description="Enable price conversion between markets"
    )
    conversion_symbol: str | None = Field(
        default=None, description="Symbol for conversion rate, e.g. ETH/BTC"
    )
    staleness_seconds: int = Field(
        default=60, ge=1, le=3600, description="Max age for conversion price"
    )


class MirrorExecutorConfig(BaseModel):
    """Full mirror executor agent configuration.

    This demonstrates nested models, enums, literals, optionals, sets, dicts,
    and various scalar types that pydantic-wizard supports.
    """

    name: str = Field(description="Human-readable name for this configuration")
    enabled: bool = Field(default=True, description="Whether the agent is enabled")
    mode: OptimizationType = Field(
        default=OptimizationType.MIRROR, description="Execution mode"
    )
    maker: OrderExecutionConfig = Field(description="Maker order configuration")
    taker: TakerConfig = Field(description="Taker order configuration")
    optimization: OptimizationConfig = Field(
        default_factory=OptimizationConfig,
        description="Mirror optimization strategy",
    )
    should_retry: bool = Field(
        default=False, description="Retry on maker subagent failure"
    )
    max_retries: int = Field(
        default=3, ge=0, le=100, description="Maximum retry attempts"
    )
    retry_delay_seconds: float = Field(default=5.0, description="Delay between retries")
    order_modifiers: set[OrderModifier] | None = Field(
        default_factory=lambda: {OrderModifier.POST_ONLY},
        description="Modifiers applied to orders",
    )
    conversion: ConversionPriceConfig = Field(
        default_factory=ConversionPriceConfig,
        description="Price conversion between maker/taker markets",
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    parameters: dict[str, str] = Field(
        default_factory=dict, description="Extra key-value parameters"
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="When this config was created",
    )
    notes: str | None = Field(
        default=None, description="Optional notes about this config"
    )
