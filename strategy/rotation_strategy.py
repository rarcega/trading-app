import time
from typing import List, Dict
from config import config
from database.db_manager import DatabaseManager
from broker.order_manager import OrderManager
from analysis.signals import SignalGenerator
from strategy.base_strategy import BaseStrategy


class RotationStrategy(BaseStrategy):
    def __init__(self, broker, order_manager: OrderManager,
                 signal_generator: SignalGenerator, db_manager: DatabaseManager):
        super().__init__(broker, order_manager, signal_generator, db_manager)

    def execute(self) -> List[dict]:
        if not self.running:
            return []

        actions = []
        positions = self.db.get_positions()

        for pos in positions:
            df = self.broker.get_historical_data(pos.symbol)
            if df is None:
                continue
            analysis = self.signal_generator.analyze(pos.symbol, df)
            if analysis and analysis["signal"] == "SELL":
                order = self.order_manager.sell(
                    pos.symbol, pos.quantity, market=pos.market
                )
                if order:
                    actions.append({
                        "action": "SELL",
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "price": order["price"],
                        "reasons": analysis["reasons_sell"],
                    })

        if self.order_manager.can_buy():
            watchlist = config.trading.watchlist
            current_symbols = {p.symbol for p in positions}
            candidates = []
            for symbol in watchlist:
                if symbol in current_symbols:
                    continue
                df = self.broker.get_historical_data(symbol)
                if df is None:
                    continue
                analysis = self.signal_generator.analyze(symbol, df)
                if analysis and analysis["signal"] == "BUY":
                    candidates.append(analysis)

            candidates.sort(key=lambda x: x["buy_score"], reverse=True)
            slots_available = config.trading.max_positions - len(positions)
            for candidate in candidates[:slots_available]:
                price = candidate["indicators"]["price"]
                quantity = self.order_manager.calculate_quantity(candidate["symbol"], price)
                if quantity > 0:
                    order = self.order_manager.buy(
                        candidate["symbol"], quantity, market=None
                    )
                    if order:
                        actions.append({
                            "action": "BUY",
                            "symbol": candidate["symbol"],
                            "quantity": quantity,
                            "price": order["price"],
                            "reasons": candidate["reasons_buy"],
                        })

        return actions
