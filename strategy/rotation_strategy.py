import time
from typing import List, Dict
from PyQt6.QtCore import pyqtSignal, QObject
from config import config
from database.db_manager import DatabaseManager
from broker.order_manager import OrderManager
from analysis.signals import SignalGenerator
from strategy.base_strategy import BaseStrategy


class RotationStrategy(BaseStrategy):
    def __init__(self, broker, order_manager: OrderManager,
                 signal_generator: SignalGenerator, db_manager: DatabaseManager):
        super().__init__(broker, order_manager, signal_generator, db_manager)

    def execute_with_logs(self, log_signal) -> List[dict]:
        if not self.running:
            return []

        actions = []
        positions = self.db.get_positions()

        log_signal.emit(f"Posiciones actuales: {len(positions)}/{config.trading.max_positions}")

        if positions:
            log_signal.emit("--- Revisando posiciones para VENTA ---")
            for pos in positions:
                log_signal.emit(f"Analizando {pos.symbol}...")
                df = self.broker.get_historical_data(pos.symbol)
                if df is None:
                    log_signal.emit(f"  {pos.symbol}: sin datos, saltando")
                    continue
                analysis = self.signal_generator.analyze(pos.symbol, df)
                if analysis:
                    indicators = analysis.get("indicators", {})
                    rsi = indicators.get("rsi", 0)
                    log_signal.emit(f"  {pos.symbol}: RSI={rsi:.1f}")
                    if analysis["signal"] == "SELL":
                        log_signal.emit(f"  >> SEÑAL VENTA {pos.symbol}: {', '.join(analysis['reasons_sell'])}")
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
                            log_signal.emit(f"  >> VENDIDO {pos.symbol} x{pos.quantity} @ ${order['price']:.2f}")
                    else:
                        log_signal.emit(f"  {pos.symbol}: sin señal de venta")
                else:
                    log_signal.emit(f"  {pos.symbol}: datos insuficientes para análisis")

        if self.order_manager.can_buy():
            log_signal.emit("--- Buscando acciones para COMPRA ---")
            watchlist = config.trading.watchlist
            current_symbols = {p.symbol for p in positions}
            candidates = []
            for symbol in watchlist:
                if not self.running:
                    break
                if symbol in current_symbols:
                    log_signal.emit(f"  {symbol}: ya en cartera, saltando")
                    continue
                log_signal.emit(f"  Analizando {symbol}...")
                df = self.broker.get_historical_data(symbol)
                if df is None:
                    log_signal.emit(f"  {symbol}: sin datos, saltando")
                    continue
                analysis = self.signal_generator.analyze(symbol, df)
                if analysis:
                    indicators = analysis.get("indicators", {})
                    rsi = indicators.get("rsi", 0)
                    macd_hist = indicators.get("macd_hist", 0)
                    log_signal.emit(f"  {symbol}: RSI={rsi:.1f}, MACD={macd_hist:.2f}")
                    if analysis["signal"] == "BUY":
                        log_signal.emit(f"  >> SEÑAL COMPRA {symbol}: {', '.join(analysis['reasons_buy'])}")
                        candidates.append(analysis)
                    else:
                        log_signal.emit(f"  {symbol}: sin señal de compra")
                else:
                    log_signal.emit(f"  {symbol}: datos insuficientes")

            if candidates:
                candidates.sort(key=lambda x: x["buy_score"], reverse=True)
                slots_available = config.trading.max_positions - len(positions)
                log_signal.emit(f"候选股: {len(candidates)}, huecos disponibles: {slots_available}")
                for candidate in candidates[:slots_available]:
                    symbol = candidate["symbol"]
                    price = candidate["indicators"]["price"]
                    quantity = self.order_manager.calculate_quantity(symbol, price)
                    if quantity > 0:
                        order = self.order_manager.buy(symbol, quantity, market=None)
                        if order:
                            actions.append({
                                "action": "BUY",
                                "symbol": symbol,
                                "quantity": quantity,
                                "price": order["price"],
                                "reasons": candidate["reasons_buy"],
                            })
                            log_signal.emit(f"  >> COMPRADO {symbol} x{quantity} @ ${order['price']:.2f}")
            else:
                log_signal.emit("No se encontraron señales de compra")
        else:
            log_signal.emit("Cartera llena, no se buscan nuevas compras")

        log_signal.emit(f"Escaneo completado. Operaciones: {len(actions)}")
        return actions

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
