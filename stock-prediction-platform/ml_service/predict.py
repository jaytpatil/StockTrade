import os
import json
import logging
import numpy as np
import pandas as pd
import joblib

try:
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PredictorService:
    def __init__(self, symbol: str, lookback_window: int = 60, horizon: int = 7):
        self.symbol = symbol.upper()
        self.lookback_window = lookback_window
        self.horizon = horizon
        self.model_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(self.model_dir, "saved_models", f"lstm_{self.symbol}.h5")
        self.scaler_path = os.path.join(self.model_dir, "saved_models", f"scaler_{self.symbol}.pkl")
        
        self.model = None
        self.scaler = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads the saved neural network model and the associated MinMaxScaler."""
        if not os.path.exists(self.model_path) or not os.path.exists(self.scaler_path):
            logging.error(f"Models for {self.symbol} not found. Please train first.")
            return
            
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow/Keras is required for LSTM inference.")
            
        logging.info(f"Loading deep learning artifacts for {self.symbol}...")
        self.model = load_model(self.model_path)
        self.scaler = joblib.load(self.scaler_path)

    def _calculate_confidence(self, volatility: float, trend_strength: float) -> float:
        """Heuristic calculation of model confidence based on market volatility."""
        # Simple proxy: Lower volatility combined with strong trend gives higher ML confidence
        base_confidence = 85.0
        adjusted = base_confidence - (volatility * 10) + (trend_strength * 5)
        # Clamp between 45% and 98%
        return round(float(np.clip(adjusted, 45.0, 98.0)), 2)

    def generate_prediction(self, recent_df: pd.DataFrame) -> dict:
        """
        Accepts the latest stock dataframe, processes the rolling lookback window,
        and returns exactly an array of predictions for the next 7 days.
        """
        if self.model is None or self.scaler is None:
            return {"error": "Model artifacts not loaded properly."}
            
        if len(recent_df) < self.lookback_window:
            return {"error": f"Requires at least {self.lookback_window} days of historical data."}

        # Ensure correct columns exist (Close, Volume, SMA_20, RSI_14, MACD)
        # Note: In a production pipeline, this matches the train_model.py feature engineering exactly.
        features = ['Close', 'Volume', 'SMA_20', 'RSI_14', 'MACD']
        raw_data = recent_df[features].values
        
        # Scale the data using the frozen training scaler
        scaled_data = self.scaler.transform(raw_data)
        
        # Extract the final lookback window to predict from
        final_window = scaled_data[-self.lookback_window:]
        X_infer = np.array([final_window])
        
        # LSTM predict targets the 7th day directly based on our training
        scaled_prediction = self.model.predict(X_infer)
        
        # Inverse Transform
        dummy_array = np.zeros((1, 5))
        dummy_array[0, 0] = scaled_prediction[0, 0]
        real_prediction = self.scaler.inverse_transform(dummy_array)[0, 0]
        
        # Simulated interpolation for the next 7 calendar days mapping to that point
        current_price = recent_df['Close'].iloc[-1]
        trajectory = np.linspace(current_price, real_prediction, self.horizon)
        
        # Build the final 7-day future horizon dict objects
        predictions = []
        for i, price in enumerate(trajectory):
            predictions.append({
                "day_offset": i + 1,
                "predicted_price": round(float(price), 2)
            })
            
        # Optional metadata stats used for dynamic confidence score
        daily_returns = recent_df['Close'].pct_change().dropna()
        volatility = daily_returns.std()
        trend_strength = abs(current_price - recent_df['Close'].iloc[-20]) / recent_df['Close'].iloc[-20]
        
        confidence = self._calculate_confidence(volatility, trend_strength)
        
        # Recommendation Logic Generator
        pct_change_predicted = ((real_prediction - current_price) / current_price) * 100
        signal = "HOLD"
        if pct_change_predicted > 1.2:
            signal = "BUY"
        elif pct_change_predicted < -1.2:
            signal = "SELL"

        response_json = {
            "symbol": self.symbol,
            "status": "success",
            "current_price": round(float(current_price), 2),
            "target_horizon_days": self.horizon,
            "final_target_price": round(float(real_prediction), 2),
            "forecast_trajectory": predictions,
            "recommendation": signal,
            "confidence_score": confidence
        }
        
        return response_json

if __name__ == "__main__":
    # Mock inference loading logic (example)
    pass
