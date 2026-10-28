from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from database import get_db
import models
from utils.stock_data import get_real_time_price, get_historical_data
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/{ticker}/forecast")
def get_prediction_forecast(ticker: str, db: Session = Depends(get_db)) -> Dict:
    """
    Fetches real ML predictions from the database for a ticker.
    Returns actual prediction data from the ML pipeline instead of mock data.
    """
    symbol = ticker.upper()
    
    try:
        # Get the stock from database
        stock = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found in database")
        
        # Get the latest prediction for this stock
        latest_prediction = db.query(models.PredictionResult).filter(
            models.PredictionResult.stock_id == stock.id
        ).order_by(models.PredictionResult.created_at.desc()).first()
        
        if not latest_prediction:
            raise HTTPException(status_code=404, detail=f"No predictions found for {symbol}. Run prediction endpoint first.")
        
        # Get current real-time price
        price_data = get_real_time_price(symbol)
        current_price = price_data.get("current_price", 0.0) if price_data.get("status") == "success" else latest_prediction.predicted_price
        
        # Get recommendation for signal
        latest_rec = db.query(models.Recommendation).filter(
            models.Recommendation.stock_id == stock.id
        ).order_by(models.Recommendation.created_at.desc()).first()
        
        signal = "HOLD"
        confidence = 50.0
        if latest_rec:
            signal = latest_rec.action.value if hasattr(latest_rec.action, 'value') else latest_rec.action
            confidence = latest_rec.confidence_score
        
        # Generate forecast based on the prediction
        predicted_price = latest_prediction.predicted_price
        forecast = []
        days_to_target = (latest_prediction.target_date - datetime.utcnow()).days
        
        for i in range(1, min(15, days_to_target + 1)):
            # Linear interpolation from current price to predicted price
            progress = i / days_to_target
            expected = current_price + (predicted_price - current_price) * progress
            forecast.append({
                "date": f"Day {i}",
                "expected": round(expected, 2),
                "upperBand": round(expected * 1.02, 2),
                "lowerBand": round(expected * 0.98, 2)
            })
        
        return {
            "ticker": symbol,
            "signal": signal,
            "confidence": round(confidence, 1),
            "forecast": forecast
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch forecast: {str(e)}")

@router.get("/recommendations")
def get_all_recommendations(db: Session = Depends(get_db)) -> List[Dict]:
    """
    Fetches real recommendations from the database instead of static mock data.
    """
    try:
        recommendations = db.query(models.Recommendation).all()
        result = []
        for rec in recommendations:
            stock = db.query(models.Stock).filter(models.Stock.id == rec.stock_id).first()
            if stock:
                result.append({
                    "ticker": stock.symbol,
                    "recommendation": rec.action.value if hasattr(rec.action, 'value') else rec.action,
                    "confidence": rec.confidence_score
                })
        
        # If no recommendations in DB, return empty list
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendations: {str(e)}")
