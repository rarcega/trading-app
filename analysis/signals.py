import pandas as pd
from typing import Optional
from ..config import config
from ..database.db_manager import DatabaseManager
from .indicators import TechnicalIndicators


class SignalGenerator:
    def __init__(self, db_manager: DatabaseManager):
        self.indicators = TechnicalIndicators()
        self.db = db_manager
        self.cfg = config.strategy

    def analyze(self, symbol: str, df: pd.DataFrame) -> Optional[dict]:
        if df is None or df.empty or len(df) < 50:
            return None

        df = self.indicators.calculate_all(df.copy())
        latest = self.indicators.get_latest_indicators(df)

        if not latest:
            return None

        buy_score = 0
        sell_score = 0
        reasons_buy = []
        reasons_sell = []

        rsi = latest["rsi"]
        if rsi < self.cfg.rsi_oversold:
            buy_score += 1
            reasons_buy.append(f"RSI={rsi:.1f}<30")
        elif rsi > self.cfg.rsi_overbought:
            sell_score += 1
            reasons_sell.append(f"RSI={rsi:.1f}>70")

        macd_hist = latest["macd_hist"]
        macd_prev = latest["macd_prev_hist"]
        if macd_hist > 0 and macd_prev <= 0:
            buy_score += 1
            reasons_buy.append("MACD cruce alcista")
        elif macd_hist < 0 and macd_prev >= 0:
            sell_score += 1
            reasons_sell.append("MACD cruce bajista")

        price = latest["price"]
        bb_lower = latest["bb_lower"]
        bb_upper = latest["bb_upper"]
        bb_mid = latest["bb_mid"]
        if bb_lower > 0 and bb_upper > 0:
            bb_pos = (price - bb_lower) / (bb_upper - bb_lower)
            if bb_pos < 0.2:
                buy_score += 1
                reasons_buy.append(f"BB pos={bb_pos:.2f}<0.2")
            elif bb_pos > 0.8:
                sell_score += 1
                reasons_sell.append(f"BB pos={bb_pos:.2f}>0.8")

        sma_short = latest["sma_short"]
        sma_long = latest["sma_long"]
        if sma_short > 0 and sma_long > 0:
            if sma_short > sma_long and price > sma_short:
                buy_score += 0.5
                reasons_buy.append("SMA alcista")
            elif sma_short < sma_long and price < sma_short:
                sell_score += 0.5
                reasons_sell.append("SMA bajista")

        signal_type = None
        if buy_score >= 2.5:
            signal_type = "BUY"
        elif sell_score >= 2.5:
            signal_type = "SELL"

        if signal_type:
            self.db.add_signal(
                symbol=symbol,
                signal_type=signal_type,
                rsi_value=rsi,
                macd_value=latest["macd"],
                macd_signal=latest["macd_signal"],
                bb_position=bb_pos if bb_lower > 0 else 0.5,
                sma_short=sma_short,
                sma_long=sma_long,
                price=price,
            )

        return {
            "symbol": symbol,
            "signal": signal_type,
            "buy_score": buy_score,
            "sell_score": sell_score,
            "reasons_buy": reasons_buy,
            "reasons_sell": reasons_sell,
            "indicators": latest,
        }

    def scan_watchlist(self, broker, watchlist: list) -> list:
        results = []
        for symbol in watchlist:
            df = broker.get_historical_data(symbol)
            if df is not None:
                analysis = self.analyze(symbol, df)
                if analysis:
                    results.append(analysis)
        return results
