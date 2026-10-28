import pandas as pd
import numpy as np
import json

def calculate_sma(df: pd.DataFrame, period: int) -> pd.Series:
    """Calculate Simple Moving Average (SMA)."""
    return df['Close'].rolling(window=period).mean()

def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
    """Calculate Exponential Moving Average (EMA)."""
    return df['Close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = df['Close'].diff()
    
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    # Calculate exponential moving averages for gain and loss
    avg_gain = gain.ewm(com=(period - 1), min_periods=period).mean()
    avg_loss = loss.ewm(com=(period - 1), min_periods=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculate MACD (Moving Average Convergence Divergence).
    Returns MACD Line, Signal Line, and Histogram as Series.
    """
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, num_std: int = 2):
    """
    Calculate Bollinger Bands.
    Returns Upper Band, Middle Band (SMA), and Lower Band.
    """
    middle_band = df['Close'].rolling(window=period).mean()
    std_dev = df['Close'].rolling(window=period).std()
    
    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)
    
    return upper_band, middle_band, lower_band

def calculate_support_resistance(df: pd.DataFrame, period: int = 20):
    """
    Calculate static proxy Support and Resistance using rolling min/max.
    """
    resistance = df['High'].rolling(window=period).max()
    support = df['Low'].rolling(window=period).min()
    
    return support, resistance

def generate_technical_analysis_report(df: pd.DataFrame) -> dict:
    """
    Parses a DataFrame containing OHLC data and appends all indicators.
    Returns the most recent row's indicators formatted cleanly as a JSON serializable dict.
    """
    df = df.copy()
    
    # Calculate tracking metrics
    df['SMA_20'] = calculate_sma(df, 20)
    df['SMA_50'] = calculate_sma(df, 50)
    df['EMA_20'] = calculate_ema(df, 20)
    df['RSI_14'] = calculate_rsi(df, 14)
    
    macd_line, signal_line, macd_hist = calculate_macd(df)
    df['MACD_Line'] = macd_line
    df['MACD_Signal'] = signal_line
    df['MACD_Hist'] = macd_hist
    
    upper, middle, lower = calculate_bollinger_bands(df)
    df['BB_Upper'] = upper
    df['BB_Lower'] = lower
    
    support, resistance = calculate_support_resistance(df)
    df['Support'] = support
    df['Resistance'] = resistance
    
    # Extract the latest complete row of data
    latest = df.iloc[-1]
    
    # Drop any potential NaN values safely and convert to native python types
    latest = latest.replace({np.nan: None})
    
    return {
        "status": "success",
        "latest_price": round(float(latest.get('Close', 0)), 2),
        "indicators": {
            "trend": {
                "SMA_20": round(float(latest.get('SMA_20') or 0), 2),
                "SMA_50": round(float(latest.get('SMA_50') or 0), 2),
                "EMA_20": round(float(latest.get('EMA_20') or 0), 2)
            },
            "momentum": {
                "RSI_14": round(float(latest.get('RSI_14') or 0), 2),
                "MACD": {
                    "line": round(float(latest.get('MACD_Line') or 0), 2),
                    "signal": round(float(latest.get('MACD_Signal') or 0), 2),
                    "histogram": round(float(latest.get('MACD_Hist') or 0), 2)
                }
            },
            "volatility": {
                "Bollinger_Upper": round(float(latest.get('BB_Upper') or 0), 2),
                "Bollinger_Lower": round(float(latest.get('BB_Lower') or 0), 2)
            },
            "levels": {
                "Support": round(float(latest.get('Support') or 0), 2),
                "Resistance": round(float(latest.get('Resistance') or 0), 2)
            }
        }
    }

if __name__ == "__main__":
    # Internal mock execution
    dates = pd.date_range('2024-01-01', periods=100)
    mock_data = {
        'Close': np.random.uniform(140, 160, 100).cumsum().astype(float),
        'High': np.random.uniform(140, 160, 100).cumsum().astype(float) + 5,
        'Low': np.random.uniform(140, 160, 100).cumsum().astype(float) - 5
    }
    mock_df = pd.DataFrame(mock_data, index=dates)
    
    result = generate_technical_analysis_report(mock_df)
    print(json.dumps(result, indent=2))
