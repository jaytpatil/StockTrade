import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_historical_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetches historical OHLCV data for a given ticker using Yahoo Finance.
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    
    if df.empty:
        raise ValueError(f"No data found for {ticker}")
        
    df.reset_index(inplace=True)
    # Ensure standard column naming
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    return df

def fetch_realtime_price(ticker: str) -> float:
    """
    Fetches the latest available price for a given ticker.
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d", interval="1m")
    if not data.empty:
        return data['Close'].iloc[-1]
    return 0.0
