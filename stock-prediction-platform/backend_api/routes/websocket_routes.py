from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
import time
from typing import List, Dict, Set
from utils.stock_data import get_real_time_price, get_historical_data
from datetime import datetime, timedelta
from database import SessionLocal
import models

router = APIRouter()

# In-memory price cache: symbol -> {"data": dict, "timestamp": float}
PRICE_CACHE: Dict[str, dict] = {}
CACHE_TTL_SECONDS = 5.0

def get_cached_real_time_price(symbol: str) -> dict:
    """Fetch real-time price with 5-second TTL in-memory caching to avoid rate-limiting."""
    now = time.time()
    if symbol in PRICE_CACHE and (now - PRICE_CACHE[symbol]["timestamp"]) < CACHE_TTL_SECONDS:
        return PRICE_CACHE[symbol]["data"]
    
    price_data = get_real_time_price(symbol)
    if price_data.get("status") == "success":
        PRICE_CACHE[symbol] = {"data": price_data, "timestamp": now}
    return price_data

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Map of ticker symbol -> set of subscribed WebSockets
        self.subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"WebSocket Client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        for symbol, sub_set in self.subscriptions.items():
            sub_set.discard(websocket)
        logging.info(f"WebSocket Client disconnected. Active connections: {len(self.active_connections)}")

    def subscribe(self, websocket: WebSocket, symbol: str):
        symbol = symbol.upper()
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = set()
        self.subscriptions[symbol].add(websocket)

    def unsubscribe(self, websocket: WebSocket, symbol: str):
        symbol = symbol.upper()
        if symbol in self.subscriptions:
            self.subscriptions[symbol].discard(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.error(f"Error broadcasting to client: {e}")
                self.disconnect(connection)

    async def send_to_subscribers(self, symbol: str, message: dict):
        symbol = symbol.upper()
        subscribers = list(self.subscriptions.get(symbol, []))
        for connection in subscribers:
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.error(f"Error sending symbol update to subscriber: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

DEFAULT_TICKERS = [
    {"ticker": "AAPL", "name": "Apple Inc."},
    {"ticker": "TSLA", "name": "Tesla Inc."},
    {"ticker": "NVDA", "name": "NVIDIA Corp"},
    {"ticker": "MSFT", "name": "Microsoft Corp"}
]

async def fetch_ticker_metrics(loop, ticker: str, name: str = ""):
    """Helper to fetch price, change percentage, and AI recommendation signal."""
    price_data = await loop.run_in_executor(None, get_cached_real_time_price, ticker)
    current_price = price_data.get("current_price", 0.0) if price_data.get("status") == "success" else 0.0
    
    real_change = 0.0
    if current_price > 0:
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            df, _ = await loop.run_in_executor(None, get_historical_data, ticker, start_date, end_date)
            if not df.empty and len(df) >= 2:
                previous_close = df['Close'].iloc[-2]
                real_change = round(((current_price - previous_close) / previous_close) * 100, 2)
        except Exception as e:
            logging.error(f"Error calculating change for {ticker}: {e}")
    
    real_signal = "HOLD"
    try:
        db = SessionLocal()
        stock = db.query(models.Stock).filter(models.Stock.symbol == ticker).first()
        if stock:
            latest_rec = db.query(models.Recommendation).filter(
                models.Recommendation.stock_id == stock.id
            ).order_by(models.Recommendation.created_at.desc()).first()
            if latest_rec:
                real_signal = latest_rec.action.value if hasattr(latest_rec.action, 'value') else latest_rec.action
        db.close()
    except Exception as e:
        logging.error(f"Error fetching recommendation for {ticker}: {e}")

    import math
    try:
        if current_price is None or math.isnan(float(current_price)):
            current_price = 0.0
        else:
            current_price = round(float(current_price), 2)
    except (ValueError, TypeError):
        current_price = 0.0

    try:
        if real_change is None or math.isnan(float(real_change)):
            real_change = 0.0
        else:
            real_change = round(float(real_change), 2)
    except (ValueError, TypeError):
        real_change = 0.0

    return {
        "ticker": ticker,
        "name": name or f"{ticker} Corp",
        "price": current_price,
        "change": real_change,
        "signal": real_signal,
        "timestamp": datetime.utcnow().isoformat()
    }

async def stock_data_broadcaster():
    """Background task to periodically broadcast market data to clients."""
    loop = asyncio.get_event_loop()
    while True:
        if manager.active_connections:
            try:
                watchlist_data = []
                total_balance = 40000.0
                
                for item in DEFAULT_TICKERS:
                    metrics = await fetch_ticker_metrics(loop, item["ticker"], item["name"])
                    if metrics["price"] > 0:
                        total_balance += metrics["price"] * 10
                    watchlist_data.append(metrics)

                    # Send targeted update to clients subscribed to this ticker
                    await manager.send_to_subscribers(item["ticker"], {
                        "type": "TICKER_UPDATE",
                        "data": metrics
                    })
                
                # Send subscribed updates for non-default active subscriptions
                for subscribed_symbol in list(manager.subscriptions.keys()):
                    if not any(d["ticker"] == subscribed_symbol for d in DEFAULT_TICKERS):
                        sub_metrics = await fetch_ticker_metrics(loop, subscribed_symbol)
                        await manager.send_to_subscribers(subscribed_symbol, {
                            "type": "TICKER_UPDATE",
                            "data": sub_metrics
                        })

                import math
                safe_balance = 40000.0
                try:
                    if total_balance is not None and not math.isnan(float(total_balance)):
                        safe_balance = round(float(total_balance), 2)
                except (ValueError, TypeError):
                    safe_balance = 40000.0

                payload = {
                    "type": "DASHBOARD_UPDATE",
                    "data": {
                        "balance": safe_balance,
                        "balance_change_pct": 3.2,
                        "watchlist": watchlist_data
                    }
                }
                
                await manager.broadcast(payload)
            except Exception as e:
                logging.error(f"Error in stock_data_broadcaster: {e}")
                
        await asyncio.sleep(5)

@router.websocket("/ws/stocks")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data_str = await websocket.receive_text()
            if not data_str:
                continue
            try:
                data = json.loads(data_str)
                action = data.get("action")
                symbol = data.get("symbol")

                if action == "ping":
                    await websocket.send_json({"type": "PONG"})
                elif action == "subscribe" and symbol:
                    manager.subscribe(websocket, symbol)
                    loop = asyncio.get_event_loop()
                    metrics = await fetch_ticker_metrics(loop, symbol)
                    await websocket.send_json({"type": "TICKER_UPDATE", "data": metrics})
                elif action == "unsubscribe" and symbol:
                    manager.unsubscribe(websocket, symbol)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

