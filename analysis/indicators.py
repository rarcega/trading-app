import pandas as pd
import pandas_ta as ta
from ..config import config


class TechnicalIndicators:
    def __init__(self):
        self.cfg = config.strategy

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.add_rsi(df)
        df = self.add_macd(df)
        df = self.add_bollinger_bands(df)
        df = self.add_sma(df)
        df = self.add_ema(df)
        df = self.add_volume_indicators(df)
        return df

    def add_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        df["RSI"] = ta.rsi(df["close"], length=self.cfg.rsi_period)
        return df

    def add_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        macd = ta.macd(
            df["close"],
            fast=self.cfg.macd_fast,
            slow=self.cfg.macd_slow,
            signal=self.cfg.macd_signal,
        )
        df["MACD"] = macd[f"MACD_{self.cfg.macd_fast}_{self.cfg.macd_slow}_{self.cfg.macd_signal}"]
        df["MACD_SIGNAL"] = macd[f"MACDs_{self.cfg.macd_fast}_{self.cfg.macd_slow}_{self.cfg.macd_signal}"]
        df["MACD_HIST"] = macd[f"MACDh_{self.cfg.macd_fast}_{self.cfg.macd_slow}_{self.cfg.macd_signal}"]
        return df

    def add_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        bb = ta.bbands(df["close"], length=self.cfg.bb_period, std=self.cfg.bb_std)
        df["BB_UPPER"] = bb[f"BBU_{self.cfg.bb_period}_{self.cfg.bb_std}"]
        df["BB_MID"] = bb[f"BBM_{self.cfg.bb_period}_{self.cfg.bb_std}"]
        df["BB_LOWER"] = bb[f"BBL_{self.cfg.bb_period}_{self.cfg.bb_std}"]
        df["BB_WIDTH"] = (df["BB_UPPER"] - df["BB_LOWER"]) / df["BB_MID"]
        return df

    def add_sma(self, df: pd.DataFrame) -> pd.DataFrame:
        df["SMA_SHORT"] = ta.sma(df["close"], length=self.cfg.sma_short)
        df["SMA_LONG"] = ta.sma(df["close"], length=self.cfg.sma_long)
        return df

    def add_ema(self, df: pd.DataFrame) -> pd.DataFrame:
        df["EMA_SHORT"] = ta.ema(df["close"], length=self.cfg.sma_short)
        df["EMA_LONG"] = ta.ema(df["close"], length=self.cfg.sma_long)
        return df

    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["OBV"] = ta.obv(df["close"], df["volume"])
        df["VWAP"] = ta.vwap(df["high"], df["low"], df["close"], df["volume"])
        return df

    def get_latest_indicators(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        return {
            "price": last.get("close", 0),
            "rsi": last.get("RSI", 50),
            "macd": last.get("MACD", 0),
            "macd_signal": last.get("MACD_SIGNAL", 0),
            "macd_hist": last.get("MACD_HIST", 0),
            "macd_prev_hist": prev.get("MACD_HIST", 0),
            "bb_upper": last.get("BB_UPPER", 0),
            "bb_mid": last.get("BB_MID", 0),
            "bb_lower": last.get("BB_LOWER", 0),
            "bb_width": last.get("BB_WIDTH", 0),
            "sma_short": last.get("SMA_SHORT", 0),
            "sma_long": last.get("SMA_LONG", 0),
            "ema_short": last.get("EMA_SHORT", 0),
            "ema_long": last.get("EMA_LONG", 0),
            "volume": last.get("volume", 0),
            "obv": last.get("OBV", 0),
        }
