import os
import json
from dataclasses import dataclass, field, asdict
from typing import List

CONFIG_FILE = "data/config.json"


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
    rsi_oversold: float = 35.0
    rsi_overbought: float = 65.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_period: int = 20
    bb_std: float = 2.0
    sma_short: int = 20
    sma_long: int = 50
    buy_threshold: float = 2.0
    sell_threshold: float = 2.0


@dataclass
class AppConfig:
    ib: IBConfig = field(default_factory=IBConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    db_path: str = "data/trading.db"
    log_level: str = "INFO"


def save_config(cfg: AppConfig):
    os.makedirs("data", exist_ok=True)
    data = {
        "ib": asdict(cfg.ib),
        "trading": asdict(cfg.trading),
        "strategy": asdict(cfg.strategy),
        "db_path": cfg.db_path,
        "log_level": cfg.log_level,
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_config() -> AppConfig:
    cfg = AppConfig()
    if not os.path.exists(CONFIG_FILE):
        return cfg
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "ib" in data:
            for k, v in data["ib"].items():
                if hasattr(cfg.ib, k):
                    setattr(cfg.ib, k, v)
        if "trading" in data:
            for k, v in data["trading"].items():
                if hasattr(cfg.trading, k):
                    setattr(cfg.trading, k, v)
        if "strategy" in data:
            for k, v in data["strategy"].items():
                if hasattr(cfg.strategy, k):
                    setattr(cfg.strategy, k, v)
        if "db_path" in data:
            cfg.db_path = data["db_path"]
        if "log_level" in data:
            cfg.log_level = data["log_level"]
    except Exception as e:
        print(f"Error cargando config: {e}")
    return cfg


config = load_config()
