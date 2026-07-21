import random
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from ..config import config


class SimulationConnector:
    def __init__(self):
        self.connected = False
        self.cash = config.trading.investment_amount
        self.positions: Dict[str, dict] = {}
        self.account_value = self.cash

    def connect(self) -> bool:
        self.connected = True
        return True

    def disconnect(self):
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def get_account_summary(self) -> dict:
        positions_value = sum(
            pos["quantity"] * pos["current_price"]
            for pos in self.positions.values()
        )
        self.account_value = self.cash + positions_value
        return {
            "total_cash": self.cash,
            "positions_value": positions_value,
            "account_value": self.account_value,
        }

    def get_positions(self) -> List[dict]:
        return [
            {
                "symbol": symbol,
                "quantity": pos["quantity"],
                "avg_price": pos["avg_price"],
                "current_price": pos["current_price"],
                "market_value": pos["quantity"] * pos["current_price"],
                "unrealized_pnl": (pos["current_price"] - pos["avg_price"]) * pos["quantity"],
            }
            for symbol, pos in self.positions.items()
        ]

    def get_historical_data(self, symbol: str, period: str = "3mo",
                            interval: str = "1d") -> Optional[pd.DataFrame]:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return None
            df = df.rename(columns={
                "Open": "open", "High": "high", "Low": "low",
                "Close": "close", "Volume": "volume"
            })
            return df[["open", "high", "low", "close", "volume"]]
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return None

    def get_current_price(self, symbol: str) -> Optional[float]:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data["Close"].iloc[-1])
        except Exception:
            pass
        return None

    def place_order(self, symbol: str, quantity: int, side: str,
                    order_type: str = "MARKET") -> Optional[dict]:
        price = self.get_current_price(symbol)
        if price is None:
            return None

        if side == "BUY":
            total_cost = quantity * price
            if total_cost > self.cash:
                return None
            self.cash -= total_cost
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_qty = pos["quantity"] + quantity
                pos["avg_price"] = ((pos["avg_price"] * pos["quantity"]) + (price * quantity)) / total_qty
                pos["quantity"] = total_qty
                pos["current_price"] = price
            else:
                self.positions[symbol] = {
                    "quantity": quantity,
                    "avg_price": price,
                    "current_price": price,
                }
        elif side == "SELL":
            if symbol not in self.positions:
                return None
            pos = self.positions[symbol]
            if quantity > pos["quantity"]:
                return None
            revenue = quantity * price
            self.cash += revenue
            pos["quantity"] -= quantity
            if pos["quantity"] == 0:
                del self.positions[symbol]

        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "total": quantity * price,
            "status": "FILLED",
            "timestamp": datetime.now(),
        }

    def cancel_order(self, order_id: str) -> bool:
        return True

    def get_open_orders(self) -> List[dict]:
        return []

    def update_positions_prices(self):
        for symbol, pos in self.positions.items():
            price = self.get_current_price(symbol)
            if price:
                pos["current_price"] = price
