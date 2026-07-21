from typing import Optional
from ..config import config
from ..database.db_manager import DatabaseManager


class OrderManager:
    def __init__(self, broker, db_manager: DatabaseManager):
        self.broker = broker
        self.db = db_manager

    def buy(self, symbol: str, quantity: int, market: str = None) -> Optional[dict]:
        order = self.broker.place_order(symbol, quantity, "BUY")
        if order:
            self.db.add_trade(
                symbol=symbol,
                trade_type="BUY",
                quantity=quantity,
                price=order["price"],
                market=market,
                is_simulated=config.trading.use_simulation,
            )
            self.db.add_or_update_position(
                symbol=symbol,
                quantity=quantity,
                avg_price=order["price"],
                current_price=order["price"],
                market=market,
                is_simulated=config.trading.use_simulation,
            )
        return order

    def sell(self, symbol: str, quantity: int, market: str = None) -> Optional[dict]:
        order = self.broker.place_order(symbol, quantity, "SELL")
        if order:
            self.db.add_trade(
                symbol=symbol,
                trade_type="SELL",
                quantity=quantity,
                price=order["price"],
                market=market,
                is_simulated=config.trading.use_simulation,
            )
            self.db.remove_position(symbol)
        return order

    def calculate_quantity(self, symbol: str, price: float) -> int:
        position_size = config.trading.investment_amount / config.trading.max_positions
        if price <= 0:
            return 0
        quantity = int(position_size / price)
        return max(0, quantity)

    def can_buy(self) -> bool:
        positions = self.db.get_positions()
        return len(positions) < config.trading.max_positions
