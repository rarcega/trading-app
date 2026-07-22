import os
import sys
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config, save_config
from database.db_manager import DatabaseManager
from broker.simulation_connector import SimulationConnector
from broker.order_manager import OrderManager
from analysis.signals import SignalGenerator
from strategy.rotation_strategy import RotationStrategy

app = FastAPI(title="Trading App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager(config.db_path)
broker = SimulationConnector(db)
order_manager = OrderManager(broker, db)
signal_generator = SignalGenerator(db)
strategy = RotationStrategy(broker, order_manager, signal_generator, db)

connected_clients: List[WebSocket] = []
strategy_running = False


class ConfigUpdate(BaseModel):
    investment_amount: Optional[float] = None
    max_positions: Optional[int] = None
    check_interval: Optional[int] = None
    buy_threshold: Optional[float] = None
    sell_threshold: Optional[float] = None
    rsi_oversold: Optional[float] = None
    rsi_overbought: Optional[float] = None


class WatchlistUpdate(BaseModel):
    symbol: str


@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("web/templates/index.html")


@app.get("/api/status")
async def get_status():
    summary = broker.get_account_summary()
    return {
        "connected": broker.is_connected(),
        "strategy_running": strategy_running,
        "account": summary,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/connect")
async def connect_broker():
    if broker.connect():
        return {"success": True, "message": "Conectado"}
    return {"success": False, "message": "Error de conexión"}


@app.post("/api/disconnect")
async def disconnect_broker():
    broker.disconnect()
    return {"success": True, "message": "Desconectado"}


@app.post("/api/strategy/start")
async def start_strategy():
    global strategy_running
    strategy.start()
    strategy_running = True
    asyncio.create_task(run_strategy_loop())
    return {"success": True, "message": "Estrategia iniciada"}


@app.post("/api/strategy/stop")
async def stop_strategy():
    global strategy_running
    strategy.stop()
    strategy_running = False
    return {"success": True, "message": "Estrategia detenida"}


async def run_strategy_loop():
    global strategy_running
    while strategy_running:
        try:
            actions = strategy.execute()
            for action in actions:
                await broadcast({"type": "trade", "data": action})
            await broadcast({"type": "scan_complete", "data": {"actions": len(actions)}})
        except Exception as e:
            await broadcast({"type": "error", "data": str(e)})
        broker.update_positions_prices() if hasattr(broker, 'update_positions_prices') else None
        await asyncio.sleep(config.trading.check_interval_seconds)


@app.get("/api/account")
async def get_account():
    return broker.get_account_summary()


@app.get("/api/positions")
async def get_positions():
    positions = db.get_positions()
    return [
        {
            "symbol": p.symbol,
            "quantity": p.quantity,
            "avg_price": p.avg_price,
            "current_price": p.current_price,
            "market_value": p.market_value,
            "unrealized_pnl": p.unrealized_pnl,
            "unrealized_pnl_pct": p.unrealized_pnl_pct,
        }
        for p in positions
    ]


@app.get("/api/trades")
async def get_trades(limit: int = 50):
    trades = db.get_trades(limit=limit)
    return [
        {
            "id": t.id,
            "symbol": t.symbol,
            "type": t.trade_type,
            "quantity": t.quantity,
            "price": t.price,
            "total": t.total_amount,
            "date": str(t.created_at)[:19],
        }
        for t in trades
    ]


@app.get("/api/signals")
async def get_signals(limit: int = 50):
    signals = db.get_signals(limit=limit)
    return [
        {
            "id": s.id,
            "symbol": s.symbol,
            "type": s.signal_type,
            "rsi": s.rsi_value,
            "macd": s.macd_value,
            "price": s.price,
            "quantity": s.quantity,
            "total": s.total_amount,
            "date": str(s.created_at)[:19],
        }
        for s in signals
    ]


@app.get("/api/watchlist")
async def get_watchlist():
    return {"watchlist": config.trading.watchlist}


@app.post("/api/watchlist/add")
async def add_to_watchlist(item: WatchlistUpdate):
    symbol = item.symbol.upper().strip()
    if symbol not in config.trading.watchlist:
        config.trading.watchlist.append(symbol)
        save_config(config)
        return {"success": True, "message": f"{symbol} añadido"}
    return {"success": False, "message": f"{symbol} ya existe"}


@app.post("/api/watchlist/remove")
async def remove_from_watchlist(item: WatchlistUpdate):
    symbol = item.symbol.upper().strip()
    if symbol in config.trading.watchlist:
        config.trading.watchlist.remove(symbol)
        save_config(config)
        return {"success": True, "message": f"{symbol} eliminado"}
    return {"success": False, "message": f"{symbol} no encontrado"}


@app.get("/api/config")
async def get_config():
    return {
        "investment_amount": config.trading.investment_amount,
        "max_positions": config.trading.max_positions,
        "check_interval": config.trading.check_interval_seconds,
        "buy_threshold": config.strategy.buy_threshold,
        "sell_threshold": config.strategy.sell_threshold,
        "rsi_oversold": config.strategy.rsi_oversold,
        "rsi_overbought": config.strategy.rsi_overbought,
    }


@app.post("/api/config")
async def update_config(update: ConfigUpdate):
    if update.investment_amount is not None:
        config.trading.investment_amount = update.investment_amount
        if hasattr(broker, 'cash'):
            broker.cash = update.investment_amount
    if update.max_positions is not None:
        config.trading.max_positions = update.max_positions
    if update.check_interval is not None:
        config.trading.check_interval_seconds = update.check_interval
    if update.buy_threshold is not None:
        config.strategy.buy_threshold = update.buy_threshold
    if update.sell_threshold is not None:
        config.strategy.sell_threshold = update.sell_threshold
    if update.rsi_oversold is not None:
        config.strategy.rsi_oversold = update.rsi_oversold
    if update.rsi_overbought is not None:
        config.strategy.rsi_overbought = update.rsi_overbought
    save_config(config)
    return {"success": True, "message": "Configuración actualizada"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


async def broadcast(message: dict):
    disconnected = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception:
            disconnected.append(client)
    for client in disconnected:
        connected_clients.remove(client)


app.mount("/static", StaticFiles(directory="web/static"), name="static")
