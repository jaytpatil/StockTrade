from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from database import get_db
import models

router = APIRouter()

@router.get("/global-sentiment")
def get_global_sentiment(db: Session = Depends(get_db)) -> Dict:
    """
    Calculates global market sentiment based on real recommendations in the database.
    """
    try:
        recommendations = db.query(models.Recommendation).all()
        
        if not recommendations:
            return {
                "market_sentiment": "Neutral",
                "score": 0.0,
                "top_articles": []
            }
        
        # Calculate sentiment score based on recommendations
        buy_count = sum(1 for r in recommendations if r.action.value == "BUY")
        sell_count = sum(1 for r in recommendations if r.action.value == "SELL")
        total = len(recommendations)
        
        # Calculate sentiment score (-1 to 1)
        if total > 0:
            sentiment_score = (buy_count - sell_count) / total
        else:
            sentiment_score = 0.0
        
        # Determine market sentiment
        if sentiment_score > 0.3:
            market_sentiment = "Bullish"
        elif sentiment_score < -0.3:
            market_sentiment = "Bearish"
        else:
            market_sentiment = "Neutral"
        
        # Get top recent recommendations as "articles"
        top_articles = []
        recent_recs = sorted(recommendations, key=lambda x: x.created_at, reverse=True)[:5]
        for rec in recent_recs:
            stock = db.query(models.Stock).filter(models.Stock.id == rec.stock_id).first()
            if stock:
                polarity = 0.8 if rec.action.value == "BUY" else (-0.8 if rec.action.value == "SELL" else 0.0)
                top_articles.append({
                    "title": f"{stock.symbol}: {rec.action.value} signal with {rec.confidence_score}% confidence",
                    "polarity": polarity
                })
        
        return {
            "market_sentiment": market_sentiment,
            "score": round(sentiment_score, 2),
            "top_articles": top_articles
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch global sentiment: {str(e)}")

@router.get("/sentiment")
def get_ticker_sentiment(ticker: str, db: Session = Depends(get_db)) -> Dict:
    """
    Fetches real sentiment for a ticker based on database recommendations.
    """
    symbol = ticker.upper()
    
    try:
        # Get the stock from database
        stock = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
        if not stock:
            return {
                "ticker": symbol,
                "sentiment": "Neutral",
                "polarity_score": 0.0
            }
        
        # Get the latest recommendation for this stock
        latest_rec = db.query(models.Recommendation).filter(
            models.Recommendation.stock_id == stock.id
        ).order_by(models.Recommendation.created_at.desc()).first()
        
        if not latest_rec:
            return {
                "ticker": symbol,
                "sentiment": "Neutral",
                "polarity_score": 0.0
            }
        
        # Calculate sentiment based on action
        action = latest_rec.action.value if hasattr(latest_rec.action, 'value') else latest_rec.action
        if action == "BUY":
            sentiment = "Positive"
            polarity_score = 0.5 + (latest_rec.confidence_score / 200.0)  # Scale to 0.5-1.0
        elif action == "SELL":
            sentiment = "Negative"
            polarity_score = -0.5 - (latest_rec.confidence_score / 200.0)  # Scale to -0.5 to -1.0
        else:
            sentiment = "Neutral"
            polarity_score = 0.0
        
        return {
            "ticker": symbol,
            "sentiment": sentiment,
            "polarity_score": round(polarity_score, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker sentiment: {str(e)}")
