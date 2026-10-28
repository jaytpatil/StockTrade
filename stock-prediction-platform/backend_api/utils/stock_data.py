import yfinance as yf
import pandas as pd
import json
import logging
from typing import Tuple, Dict, Any, Union

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_real_time_price(symbol: str) -> Dict[str, Any]:
    """
    Fetches the real-time (or most recent end-of-day) stock price for a given symbol.
    Returns a unified JSON-formatted dict with error handling.
    """
    try:
        logging.info(f"Fetching real-time price for {symbol}")
        ticker = yf.Ticker(symbol)
        
        # Use 5d period fallback to ensure price is retrieved even on weekends/holidays or future system clock
        todays_data = ticker.history(period='5d')
        if todays_data.empty:
            todays_data = ticker.history(period='1mo')
        
        # Clean out any rows with NaN in Close
        todays_data = todays_data.dropna(subset=['Close'])
        if todays_data.empty:
            raise ValueError(f"No valid pricing data found for symbol: {symbol}")
            
        current_price = todays_data['Close'].iloc[-1]
        import math
        if pd.isna(current_price) or math.isnan(float(current_price)):
            raise ValueError(f"Close price is NaN for {symbol}")
            
        return {
            "symbol": symbol.upper(),
            "status": "success",
            "current_price": round(float(current_price), 2),
            "timestamp": todays_data.index[-1].strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        logging.error(f"Failed to fetch price for {symbol}: {str(e)}")
        return {
            "symbol": symbol.upper(),
            "status": "error",
            "message": f"Failed to fetch real-time price: {str(e)}"
        }

def get_historical_data(symbol: str, start_date: str = None, end_date: str = None) -> Tuple[Union[pd.DataFrame, None], Dict[str, Any]]:
    """
    Fetches historical OHLCV data.
    Returns a tuple containing:
      1. the raw pandas DataFrame (or None if failed)
      2. a JSON-ready Python Dictionary containing the metadata and cleanly parsed records
    """
    try:
        logging.info(f"Fetching history for {symbol} (start: {start_date}, end: {end_date})")
        ticker = yf.Ticker(symbol)
        
        df = pd.DataFrame()
        if start_date and end_date:
            try:
                df = ticker.history(start=start_date, end=end_date)
            except Exception as ex:
                logging.warning(f"Date-range fetch failed for {symbol}: {ex}")

        if df.empty:
            # Fallback to period='1mo' or '1y' if date range query returns empty
            df = ticker.history(period='1mo')
        if df.empty:
            df = ticker.history(period='1y')
            
        if df.empty:
            raise ValueError(f"No historical data found for symbol: {symbol}")
            
        # Clean the dataframe
        df.reset_index(inplace=True)
        # Handle timezone-aware datetime index in Pandas to string conversion
        if 'Date' in df.columns:
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        elif 'Datetime' in df.columns:
            df['Datetime'] = df['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
        # Select and standardize standard columns avoiding complex multi-index bugs
        available_cols = [c for c in ['Date', 'Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'] if c in df.columns]
        df = df[available_cols]

        # Convert back to JSON orient records for REST API serving 
        json_records = df.to_dict(orient="records")
        
        json_response = {
            "symbol": symbol.upper(),
            "status": "success",
            "count": len(json_records),
            "data": json_records
        }
        
        return df, json_response
        
    except Exception as e:
        logging.error(f"Failed to fetch history for {symbol}: {str(e)}")
        error_response = {
            "symbol": symbol.upper(),
            "status": "error",
            "message": f"Failed to fetch historical data: {str(e)}"
        }
        return pd.DataFrame(), error_response

if __name__ == "__main__":
    # Internal test script
    print("--- Real Time Fetch ---")
    rt = get_real_time_price("AAPL")
    print(json.dumps(rt, indent=2))
    
    print("\n--- Historical Fetch ---")
    hist_df, hist_json = get_historical_data("AAPL", "2024-01-01", "2024-01-10")
    print(f"Dataframe lines detected: {len(hist_df)}")
    print(json.dumps(hist_json, indent=2))
