from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Trade, Position, Signal


class DatabaseManager:
    def __init__(self, db_path: str = "data/trading.db"):
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_trade(self, symbol: str, trade_type: str, quantity: float,
                  price: float, market: str = None, is_simulated: bool = True,
                  notes: str = None) -> Trade:
        session = self.Session()
        try:
            trade = Trade(
                symbol=symbol,
                trade_type=trade_type,
                quantity=quantity,
                price=price,
                total_amount=quantity * price,
                market=market,
                is_simulated=is_simulated,
                notes=notes,
            )
            session.add(trade)
            session.commit()
            return trade
        finally:
            session.close()

    def get_trades(self, limit: int = 100) -> List[Trade]:
        session = self.Session()
        try:
            return session.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def add_or_update_position(self, symbol: str, quantity: float, avg_price: float,
                                current_price: float, market: str = None,
                                is_simulated: bool = True) -> Position:
        session = self.Session()
        try:
            position = session.query(Position).filter_by(symbol=symbol).first()
            if position:
                position.quantity = quantity
                position.avg_price = avg_price
                position.current_price = current_price
                position.market_value = quantity * current_price
                position.unrealized_pnl = (current_price - avg_price) * quantity
                position.unrealized_pnl_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
                position.updated_at = datetime.utcnow()
            else:
                position = Position(
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=avg_price,
                    current_price=current_price,
                    market_value=quantity * current_price,
                    unrealized_pnl=(current_price - avg_price) * quantity,
                    unrealized_pnl_pct=((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0,
                    market=market,
                    is_simulated=is_simulated,
                )
                session.add(position)
            session.commit()
            return position
        finally:
            session.close()

    def remove_position(self, symbol: str):
        session = self.Session()
        try:
            position = session.query(Position).filter_by(symbol=symbol).first()
            if position:
                session.delete(position)
                session.commit()
        finally:
            session.close()

    def get_positions(self) -> List[Position]:
        session = self.Session()
        try:
            return session.query(Position).all()
        finally:
            session.close()

    def add_signal(self, symbol: str, signal_type: str, rsi_value: float = None,
                   macd_value: float = None, macd_signal: float = None,
                   bb_position: float = None, sma_short: float = None,
                   sma_long: float = None, price: float = None) -> Signal:
        session = self.Session()
        try:
            signal = Signal(
                symbol=symbol,
                signal_type=signal_type,
                rsi_value=rsi_value,
                macd_value=macd_value,
                macd_signal=macd_signal,
                bb_position=bb_position,
                sma_short=sma_short,
                sma_long=sma_long,
                price=price,
            )
            session.add(signal)
            session.commit()
            return signal
        finally:
            session.close()

    def get_signals(self, limit: int = 50) -> List[Signal]:
        session = self.Session()
        try:
            return session.query(Signal).order_by(Signal.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def get_portfolio_summary(self) -> dict:
        positions = self.get_positions()
        total_value = sum(p.market_value for p in positions)
        total_pnl = sum(p.unrealized_pnl for p in positions)
        return {
            "total_positions": len(positions),
            "total_value": total_value,
            "total_pnl": total_pnl,
            "positions": positions,
        }
