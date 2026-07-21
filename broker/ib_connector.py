import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from ..config import config

try:
    from ib_async import IB, Stock, Forex, MarketOrder, LimitOrder
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False


class IBConnector:
    def __init__(self):
        self.connected = False
        self.ib = None

    def connect(self) -> bool:
        if not IB_AVAILABLE:
            raise ImportError("ib_async no está instalado. Ejecuta: pip install ib_async")
        try:
            self.ib = IB()
            self.ib.connect(
                config.ib.host,
                config.ib.port,
                clientId=config.ib.client_id,
                timeout=config.ib.timeout,
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"Error conectando a IB: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False

    def is_connected(self) -> bool:
        return self.connected and self.ib is not None

    def get_account_summary(self) -> dict:
        if not self.is_connected():
            return {}
        try:
            account_values = self.ib.accountSummary()
            result = {"total_cash": 0, "positions_value": 0, "account_value": 0}
            for av in account_values:
                if av.tag == "TotalCashBalance" and av.currency == "USD":
                    result["total_cash"] = float(av.value)
                elif av.tag == "NetLiquidation" and av.currency == "USD":
                    result["account_value"] = float(av.value)
            result["positions_value"] = result["account_value"] - result["total_cash"]
            return result
        except Exception as e:
            print(f"Error obteniendo resumen de cuenta: {e}")
            return {}

    def get_positions(self) -> List[dict]:
        if not self.is_connected():
            return []
        try:
            positions = self.ib.positions()
            return [
                {
                    "symbol": pos.contract.symbol,
                    "quantity": pos.position,
                    "avg_price": pos.avgCost,
                    "current_price": 0,
                    "market_value": 0,
                    "unrealized_pnl": 0,
                }
                for pos in positions
            ]
        except Exception as e:
            print(f"Error obteniendo posiciones: {e}")
            return []

    def get_historical_data(self, symbol: str, period: str = "3mo",
                            interval: str = "1d") -> Optional[pd.DataFrame]:
        if not self.is_connected():
            return None
        try:
            contract = Stock(symbol, "SMART", "USD")
            self.ib.qualifyContract(contract)
            duration_map = {
                "1mo": "1 M", "3mo": "3 M", "6mo": "6 M",
                "1y": "1 Y", "2y": "2 Y",
            }
            bar_size_map = {
                "1d": "1 day", "1h": "1 hour", "5m": "5 mins",
            }
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr=duration_map.get(period, "3 M"),
                barSizeSetting=bar_size_map.get(interval, "1 day"),
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )
            if not bars:
                return None
            df = pd.DataFrame({
                "open": [b.open for b in bars],
                "high": [b.high for b in bars],
                "low": [b.low for b in bars],
                "close": [b.close for b in bars],
                "volume": [b.volume for b in bars],
            }, index=[b.date for b in bars])
            return df
        except Exception as e:
            print(f"Error obteniendo datos históricos para {symbol}: {e}")
            return None

    def get_current_price(self, symbol: str) -> Optional[float]:
        if not self.is_connected():
            return None
        try:
            contract = Stock(symbol, "SMART", "USD")
            self.ib.qualifyContract(contract)
            ticker = self.ib.reqMktData(contract, snapshot=True)
            self.ib.sleep(2)
            price = ticker.marketPrice()
            self.ib.cancelMktData(contract)
            return float(price) if price else None
        except Exception as e:
            print(f"Error obteniendo precio de {symbol}: {e}")
            return None

    def place_order(self, symbol: str, quantity: int, side: str,
                    order_type: str = "MARKET") -> Optional[dict]:
        if not self.is_connected():
            return None
        try:
            contract = Stock(symbol, "SMART", "USD")
            self.ib.qualifyContract(contract)
            if order_type == "MARKET":
                order = MarketOrder(side, quantity)
            else:
                price = self.get_current_price(symbol)
                order = LimitOrder(side, quantity, price)
            trade = self.ib.placeOrder(contract, order)
            self.ib.sleep(1)
            return {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": trade.orderStatus.avgFillPrice or 0,
                "total": quantity * (trade.orderStatus.avgFillPrice or 0),
                "status": trade.orderStatus.status,
                "timestamp": datetime.now(),
            }
        except Exception as e:
            print(f"Error colocando orden para {symbol}: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        if not self.is_connected():
            return False
        try:
            for trade in self.ib.openTrades():
                if str(trade.order.orderId) == order_id:
                    self.ib.cancelOrder(trade.order)
                    return True
            return False
        except Exception as e:
            print(f"Error cancelando orden: {e}")
            return False

    def get_open_orders(self) -> List[dict]:
        if not self.is_connected():
            return []
        try:
            return [
                {
                    "order_id": str(trade.order.orderId),
                    "symbol": trade.contract.symbol,
                    "side": trade.order.action,
                    "quantity": trade.order.totalQuantity,
                    "status": trade.orderStatus.status,
                }
                for trade in self.ib.openTrades()
            ]
        except Exception as e:
            print(f"Error obteniendo órdenes abiertas: {e}")
            return []
