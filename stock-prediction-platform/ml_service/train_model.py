import os
import numpy as np
import pandas as pd
import logging
import joblib
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Attempt to load TensorFlow for LSTM. If not installed, handle gracefully.
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LSTMPredictor:
    def __init__(self, symbol: str, lookback_window: int = 60, horizon: int = 7):
        self.symbol = symbol.upper()
        self.lookback_window = lookback_window
        self.horizon = horizon
        self.model_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(self.model_dir, "saved_models", f"lstm_{self.symbol}.h5")
        self.scaler_path = os.path.join(self.model_dir, "saved_models", f"scaler_{self.symbol}.pkl")
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    # --- 1. Feature Engineering ---
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Simple Moving Average
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.ewm(com=13, min_periods=14).mean()
        avg_loss = loss.ewm(com=13, min_periods=14).mean()
        rs = avg_gain / avg_loss
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26
        
        df.dropna(inplace=True)
        return df

    # --- 2. Scaling & Dataset Formatting for LSTM ---
    def prepare_data(self, df: pd.DataFrame):
        data = df[['Close', 'Volume', 'SMA_20', 'RSI_14', 'MACD']].values
        
        # Normalize Data
        scaled_data = self.scaler.fit_transform(data)
        
        X, y = [], []
        # Target is predict the close 'horizon' days into the future
        for i in range(self.lookback_window, len(scaled_data) - self.horizon):
            X.append(scaled_data[i - self.lookback_window:i])
            # The target is just the Closing price (index 0) shifted by horizon
            y.append(scaled_data[i + self.horizon, 0])
            
        return np.array(X), np.array(y)

    # --- 3. Model Architecture & Training ---
    def build_and_train(self, X_train, y_train, X_test, y_test):
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow/Keras is required to train the LSTM model. Please `pip install tensorflow`")
            
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(units=25))
        model.add(Dense(units=1))
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        
        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        
        logging.info("Training LSTM Neural Network...")
        model.fit(
            X_train, y_train, 
            batch_size=32, 
            epochs=50, 
            validation_data=(X_test, y_test),
            callbacks=[early_stop],
            verbose=1
        )
        return model

    # --- 4. Main Execution ---
    def train_pipeline(self, raw_df: pd.DataFrame):
        logging.info(f"Starting LSTM ML Pipeline for {self.symbol}")
        
        df_featured = self.add_technical_indicators(raw_df)
        X, y = self.prepare_data(df_featured)
        
        # Chronological Train-Test Split (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train
        model = self.build_and_train(X_train, y_train, X_test, y_test)
        
        # Evaluate Metrics
        predictions_scaled = model.predict(X_test)
        
        # Inverse transform to get real actual numbers instead of 0-1 metrics
        # We dummy-fill the other column features to inverse successfully
        dummy_array = np.zeros((len(predictions_scaled), 5))
        dummy_array[:, 0] = predictions_scaled[:, 0]
        predictions_real = self.scaler.inverse_transform(dummy_array)[:, 0]
        
        dummy_y = np.zeros((len(y_test), 5))
        dummy_y[:, 0] = y_test
        y_test_real = self.scaler.inverse_transform(dummy_y)[:, 0]
        
        rmse = np.sqrt(mean_squared_error(y_test_real, predictions_real))
        mae = mean_absolute_error(y_test_real, predictions_real)
        
        logging.info(f"LSTM Evaluated -> RMSE: ${rmse:.2f} | MAE: ${mae:.2f}")
        
        # Save Model and Scaler
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        model.save(self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        logging.info(f"Successfully saved to {self.model_path}")
        
        return {"rmse": rmse, "mae": mae}
        
if __name__ == "__main__":
    # Internal Mock Execution testing pipeline validation
    # Requires a DF passed containing 'Close' and 'Volume' minimum.
    pass
