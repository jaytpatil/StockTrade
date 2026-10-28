import os
import joblib
import pandas as pd
import numpy as np
import logging
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from utils.stock_data import get_historical_data
from utils.indicators import calculate_sma, calculate_ema, calculate_rsi, calculate_macd, calculate_bollinger_bands

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Storage path for serialized models
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

class XGBoostPipeline:
    def __init__(self, symbol: str, horizon: int = 7):
        self.symbol = symbol.upper()
        self.horizon = horizon
        self.model_path = os.path.join(MODEL_DIR, f"xgb_model_{self.symbol}.pkl")
        self.scaler_path = os.path.join(MODEL_DIR, f"xgb_scaler_{self.symbol}.pkl")
        self.model = None
        self.scaler = None

    def feature_engineering(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """Calculate technical indicators to act as features for the tree."""
        logging.info("Generating feature engineering vectors...")
        df = df.copy()
        
        df['SMA_20'] = calculate_sma(df, 20)
        df['EMA_20'] = calculate_ema(df, 20)
        df['RSI_14'] = calculate_rsi(df, 14)
        
        macd_line, sig_line, macd_hist = calculate_macd(df)
        df['MACD_Line'] = macd_line
        df['MACD_Hist'] = macd_hist
        
        upper, _, lower = calculate_bollinger_bands(df, 20, 2)
        df['BB_Upper'] = upper
        df['BB_Lower'] = lower

        if is_training:
            # Target Creation: Predicting the closing price 'horizon' days into the future
            df['Target'] = df['Close'].shift(-self.horizon)
            df.dropna(inplace=True)
        else:
            # For inference, fill initial rolling feature NaNs without dropping recent rows
            df.bfill(inplace=True)
            df.ffill(inplace=True)

        return df

    def train(self, start_date: str = None, end_date: str = None):
        """Downloads data, builds features, splits, scales, trains, and serializes."""
        from datetime import datetime
        if start_date is None:
            start_date = "2018-01-01"
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        logging.info(f"Initiating Training Pipeline for {self.symbol} from {start_date} to {end_date}")
        
        # 1. Fetch raw data
        raw_df, _ = get_historical_data(self.symbol, start_date, end_date)
        if raw_df is None or raw_df.empty:
            raise ValueError(f"Could not fetch historical data for {self.symbol}")
            
        # 2. Build Features
        df = self.feature_engineering(raw_df)
        
        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_20', 'EMA_20', 'RSI_14', 'MACD_Line', 'MACD_Hist', 'BB_Upper', 'BB_Lower']
        X = df[features]
        y = df['Target']
        
        # 3. Train/Test Split (Strictly chronological, avoiding random shuffle to prevent look-ahead bias)
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # 4. Scaling
        self.scaler = StandardScaler()
        # Crucial: Fit scaler ONLY on the training data
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 5. Algorithm Execution & Hyperparameters
        logging.info("Training XGBRegressor...")
        self.model = XGBRegressor(
            n_estimators=200, 
            learning_rate=0.05,
            max_depth=5, 
            subsample=0.8,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train, eval_set=[(X_test_scaled, y_test)], verbose=False)
        
        # 6. Evaluation
        predictions = self.model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        
        logging.info(f"Model Evaluation -> MAE: ${mae:.2f} | RMSE: ${rmse:.2f}")
        
        # 7. Serialization (Saving the models)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        logging.info(f"Successfully serialized Model and Scaler to {MODEL_DIR}")
        
        return {"status": "success", "mae": mae, "rmse": rmse}

    def predict_future(self) -> dict:
        """Loads serialized models to output the final 7-day future horizon price target."""
        if not os.path.exists(self.model_path) or not os.path.exists(self.scaler_path):
            logging.warning(f"Models for {self.symbol} not found. Initiating auto-training fallback.")
            self.train()
            
        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)
        
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Fetch only the recent data needed to establish the feature vectors
        recent_df, _ = get_historical_data(self.symbol, start_date, end_date)
        features_df = self.feature_engineering(recent_df, is_training=False)
        
        # Pluck the absolute most recent vector for inference 
        latest_vector = features_df.iloc[-1:]
        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_20', 'EMA_20', 'RSI_14', 'MACD_Line', 'MACD_Hist', 'BB_Upper', 'BB_Lower']
        
        X_latest_scaled = self.scaler.transform(latest_vector[features])
        
        # Prediction
        prediction = self.model.predict(X_latest_scaled)[0]
        current_price = latest_vector['Close'].iloc[0]
        
        signal = "HOLD"
        predicted_pct_change = ((prediction - current_price) / current_price) * 100
        
        if predicted_pct_change > 1.5:
            signal = "BUY"
        elif predicted_pct_change < -1.5:
            signal = "SELL"
            
        return {
            "symbol": self.symbol,
            "current_price": round(float(current_price), 2),
            "predicted_price_7D": round(float(prediction), 2),
            "percentage_diff": round(float(predicted_pct_change), 2),
            "signal": signal,
            "model_engine": "XGBoost"
        }

if __name__ == "__main__":
    # Test local execution
    pipeline = XGBoostPipeline("AAPL", horizon=7)
    results = pipeline.train()
    print("Training Complete:", results)
    
    forecast = pipeline.predict_future()
    print("\nLive Forecast Context:")
    print(forecast)
