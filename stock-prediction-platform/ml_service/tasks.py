import os
from celery import Celery
from data_pipeline.fetch_data import fetch_historical_data, fetch_realtime_price

# Configure Celery
# The broker and backend URLs are read from environment variables (fallback to localhost)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "stock_ml_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task
def train_model_task(ticker: str):
    """
    Background task to train the ML prediction model for a specific ticker.
    """
    print(f"Starting model training for {ticker}...")
    # 1. Fetch data
    df = fetch_historical_data(ticker, period="5y")
    
    # 2. Engineer features (RSI, MACD) - STUB
    print(f"Engineered features for {len(df)} rows.")
    
    # 3. Train Model (XGBoost/LSTM) - STUB
    print(f"Model trained successfully. Saving artifact.")
    
    return {"status": "success", "ticker": ticker, "action": "trained"}

@celery_app.task
def generate_daily_predictions():
    """
    Run daily inference across all tracked stocks.
    """
    tickers = ["AAPL", "TSLA", "NVDA", "BTC-USD"]
    results = []
    
    for ticker in tickers:
        print(f"Running inference for {ticker}")
        price = fetch_realtime_price(ticker)
        # 1. Run through inference.py - STUB
        # 2. Save prediction inside DB
        results.append({"ticker": ticker, "predicted": price * 1.05})
        
    return results
