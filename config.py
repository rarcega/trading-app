import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class IBConfig:
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 1
    timeout: int = 10


@dataclass
class TradingConfig:
    max_positions: int = 5
    investment_amount: float = 10000.0
    use_simulation: bool = True
    check_interval_seconds: int = 60
    markets: List[str] = field(default_factory=lambda: ["US", "EU"])
    watchlist: List[str] = field(default_factory=lambda: list([
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "TSLA", "META", "JPM", "V", "JNJ",
        "SAP.DE", "ASML.AS", "NESN.SW", "SIE.DE", "ALV.DE",
    ]))


@dataclass
class StrategyConfig:
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_period: int = 20
    bb_std: float = 2.0
    sma_short: int = 20
    sma_long: int = 50


@dataclass
class AppConfig:
    ib: IBConfig = field(default_factory=IBConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    db_path: str = "data/trading.db"
    log_level: str = "INFO"


config = AppConfig()
