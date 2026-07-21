import pandas as pd
import pandas_ta as ta
from config import config


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
        macd_cols = macd.columns.tolist()
        macd_main = [c for c in macd_cols if c.startswith("MACD_") and "signal" not in c.lower() and "hist" not in c.lower()]
        macd_sig = [c for c in macd_cols if c.startswith("MACDs_")]
        macd_hist = [c for c in macd_cols if c.startswith("MACDh_")]
        if macd_main:
            df["MACD"] = macd[macd_main[0]]
        if macd_sig:
            df["MACD_SIGNAL"] = macd[macd_sig[0]]
        if macd_hist:
            df["MACD_HIST"] = macd[macd_hist[0]]
        return df

    def add_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        bb = ta.bbands(df["close"], length=self.cfg.bb_period, std=self.cfg.bb_std)
        bb_cols = bb.columns.tolist()
        bb_upper = [c for c in bb_cols if c.startswith("BBU_")]
        bb_mid = [c for c in bb_cols if c.startswith("BBM_")]
        bb_lower = [c for c in bb_cols if c.startswith("BBL_")]
        if bb_upper:
            df["BB_UPPER"] = bb[bb_upper[0]]
        if bb_mid:
            df["BB_MID"] = bb[bb_mid[0]]
        if bb_lower:
            df["BB_LOWER"] = bb[bb_lower[0]]
        if "BB_UPPER" in df.columns and "BB_LOWER" in df.columns and "BB_MID" in df.columns:
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
