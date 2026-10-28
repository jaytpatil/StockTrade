from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from utils.stock_data import get_historical_data
from utils.indicators import generate_technical_analysis_report
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/")
@router.get("/list")
def get_stocks(db: Session = Depends(get_db)):
    stocks = db.query(models.Stock).all()
    if not stocks:
        default_stocks = [
            {"symbol": "AAPL", "company_name": "Apple Inc."},
            {"symbol": "MSFT", "company_name": "Microsoft Corp."},
            {"symbol": "GOOGL", "company_name": "Alphabet Inc."},
            {"symbol": "NVDA", "company_name": "NVIDIA Corp."},
            {"symbol": "TSLA", "company_name": "Tesla, Inc."}
        ]
        for s in default_stocks:
            db.add(models.Stock(**s))
        db.commit()
        stocks = db.query(models.Stock).all()
    return [{"symbol": s.symbol, "company": s.company_name} for s in stocks]

@router.get("/search")
def search_stocks(q: str = ""):
    """
    Searches for stocks, ETFs, and crypto matching the query using Yahoo Finance Search.
    Supports any existing global ticker.
    """
    import yfinance as yf
    query = q.strip() if q else ""
    if not query:
        # Default popular market equities and crypto
        popular = [
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "type": "EQUITY"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "type": "EQUITY"},
            {"symbol": "TSLA", "name": "Tesla, Inc.", "sector": "Consumer Cyclical", "type": "EQUITY"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "type": "EQUITY"},
            {"symbol": "AMZN", "name": "Amazon.com, Inc.", "sector": "Consumer Cyclical", "type": "EQUITY"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication Services", "type": "EQUITY"},
            {"symbol": "META", "name": "Meta Platforms, Inc.", "sector": "Communication Services", "type": "EQUITY"},
            {"symbol": "BTC-USD", "name": "Bitcoin USD", "sector": "Cryptocurrency", "type": "CRYPTO"}
        ]
        return popular

    try:
        search_res = yf.Search(query, max_results=12)
        quotes = getattr(search_res, "quotes", [])
        results = []
        for quote in quotes:
            symbol = quote.get("symbol")
            if not symbol:
                continue
            name = quote.get("shortname") or quote.get("longname") or symbol
            sector = quote.get("sector") or quote.get("sectorDisp") or quote.get("industry") or "Financial Market"
            quote_type = quote.get("quoteType", "EQUITY")
            results.append({
                "symbol": symbol,
                "name": name,
                "sector": sector,
                "type": quote_type
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/history/{symbol}")
@router.get("/{symbol}/history")
def get_stock_history(symbol: str, timeframe: str = '1y', db: Session = Depends(get_db)):
    symbol = symbol.upper()
    days_map = {
        '1d': 5,
        '5d': 7,
        '1w': 8,
        '1m': 35,
        '3m': 95,
        '1y': 365,
        '5y': 1825
    }
    days = days_map.get(timeframe.lower(), 365)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    df, json_response = get_historical_data(symbol, start_date, end_date)
    if json_response.get("status") == "error":
        raise HTTPException(status_code=400, detail=json_response.get("message"))

    # Auto-register stock in database if not present
    try:
        existing = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
        if not existing:
            new_stock = models.Stock(symbol=symbol, company_name=f"{symbol} Corp")
            db.add(new_stock)
            db.commit()
    except Exception as e:
        db.rollback()

    return json_response

@router.get("/indicators/{symbol}")
@router.get("/{symbol}/technical-indicators")
def get_stock_indicators(symbol: str):
    symbol = symbol.upper()
    end_date = datetime.now().strftime('%Y-%m-%d')
    # 180 calendar days ensures > 120 trading days for accurate 50-day SMA and MACD
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    df, json_response = get_historical_data(symbol, start_date, end_date)
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="Could not fetch data for indicators")
    
    report = generate_technical_analysis_report(df)
    raw_indicators = report.get("indicators", {})
    trend = raw_indicators.get("trend", {})
    momentum = raw_indicators.get("momentum", {})
    macd = momentum.get("MACD", {})

    # Expose both nested and convenient top-level keys for frontend compatibility
    flattened_indicators = {
        **raw_indicators,
        "RSI": momentum.get("RSI_14"),
        "RSI_14": momentum.get("RSI_14"),
        "MACD": macd.get("line"),
        "MACD_Signal": macd.get("signal"),
        "MACD_Hist": macd.get("histogram"),
        "SMA_20": trend.get("SMA_20"),
        "SMA_50": trend.get("SMA_50"),
        "EMA_20": trend.get("EMA_20")
    }
    return {"symbol": symbol, "indicators": flattened_indicators}
import sys
import os

# Ensure the parent directory is reachable if using separated ml_service modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

@router.get("/predict/{symbol}")
def get_prediction(symbol: str, db: Session = Depends(get_db)):
    """
    Core ML Integrated Endpoint.
    1. Triggers ML Inference matching 7-Day horizon.
    2. Stores Target to PostgreSQL.
    3. Outputs structured JSON.
    """
    from utils.ml_pipeline import XGBoostPipeline
    import traceback

    symbol = symbol.upper()
    try:
        # Fetch the stock from DB to associate the foreign key, or create it if missing
        stock = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
        if not stock:
            # Auto-register stock on first inference request
            stock = models.Stock(symbol=symbol, company_name=f"{symbol} INC")
            db.add(stock)
            db.commit()
            db.refresh(stock)

        # 1 & 2 & 3. Fetch Data, Compute Indicators, and Call ML Predict Module natively 
        pipeline = XGBoostPipeline(symbol, horizon=7)
        # Note: If predict_future throws FileNotFoundError, the user hasn't trained the `.pkl` artifact yet!
        prediction_result = pipeline.predict_future()
        
        # 4. Store prediction in database
        target_date = datetime.utcnow() + timedelta(days=7)
        
        db_prediction = models.PredictionResult(
            stock_id=stock.id,
            target_date=target_date,
            predicted_price=prediction_result["predicted_price_7D"],
            model_version=prediction_result.get("model_engine", "XGBoost_v1")
        )
        db.add(db_prediction)
        
        # Record the Recommendation string into DB as well
        db_recommendation = models.Recommendation(
            stock_id=stock.id,
            action=models.ActionEnum.BUY if prediction_result["signal"] == "BUY" else (
                models.ActionEnum.SELL if prediction_result["signal"] == "SELL" else models.ActionEnum.HOLD
            ),
            confidence_score=85.0, # Static mock confidence mapped into XGB pipeline response natively
            reasoning_text=f"AI predicts percentage shift of {prediction_result['percentage_diff']}% across 7 days."
        )
        db.add(db_recommendation)
        
        db.commit()

        # 5. Return JSON payload matching UI specs
        return {
            "symbol": symbol,
            "status": "success",
            "current_price": prediction_result["current_price"],
            "target_horizon_days": 7,
            "predicted_price": prediction_result["predicted_price_7D"],
            "signal": prediction_result["signal"],
            "saved_to_db": True
        }

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404, 
            detail=f"Model artifacts not found for {symbol}. Trigger training pipeline via admin console first."
        )
    except Exception as e:
        db.rollback()
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Prediction Pipeline Failed: {str(e)}")

@router.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Fetches real-time prices for top tracked stocks to populate the Dashboard Live AI Watchlist.
    Uses real stock data with actual change percentages from yfinance.
    """
    from utils.stock_data import get_real_time_price, get_historical_data
    from datetime import datetime, timedelta

    default_tickers = [
        {"ticker": "AAPL", "name": "Apple Inc."},
        {"ticker": "TSLA", "name": "Tesla Inc."},
        {"ticker": "NVDA", "name": "NVIDIA Corp"},
        {"ticker": "MSFT", "name": "Microsoft Corp"}
    ]
    
    watchlist_data = []
    total_balance = 40000.0 # Base balance mock
    
    for item in default_tickers:
        # Get current real-time price
        price_data = get_real_time_price(item["ticker"])
        current_price = price_data.get("current_price", 0.0) if price_data.get("status") == "success" else 0.0
        
        # Calculate real change percentage by fetching previous day's close
        real_change = 0.0
        if current_price > 0:
            try:
                # Fetch last 2 days to get previous close
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
                df, _ = get_historical_data(item["ticker"], start_date, end_date)
                
                if not df.empty and len(df) >= 2:
                    previous_close = df['Close'].iloc[-2]
                    real_change = round(((current_price - previous_close) / previous_close) * 100, 2)
            except Exception as e:
                print(f"Error calculating change for {item['ticker']}: {e}")
                real_change = 0.0
        
        # Get real signal from database recommendations if available
        real_signal = "HOLD"
        try:
            stock = db.query(models.Stock).filter(models.Stock.symbol == item["ticker"]).first()
            if stock:
                latest_rec = db.query(models.Recommendation).filter(
                    models.Recommendation.stock_id == stock.id
                ).order_by(models.Recommendation.created_at.desc()).first()
                if latest_rec:
                    real_signal = latest_rec.action.value if hasattr(latest_rec.action, 'value') else latest_rec.action
        except Exception as e:
            print(f"Error fetching recommendation for {item['ticker']}: {e}")
        
        if current_price > 0:
            total_balance += current_price * 10 # Assume holding 10 shares of each
            
        watchlist_data.append({
            "ticker": item["ticker"],
            "name": item["name"],
            "price": current_price,
            "change": real_change,
            "signal": real_signal
        })
        
    return {
        "balance": round(total_balance, 2),
        "balance_change_pct": 3.2,
        "watchlist": watchlist_data
    }

@router.get("/predictions/recommendations")
def get_recommendations(db: Session = Depends(get_db)):
    """
    Fetches the latest recommendations from the database for the AI Recommendations Matrix.
    """
    try:
        recommendations = db.query(models.Recommendation).all()
        result = []
        for rec in recommendations:
            stock = db.query(models.Stock).filter(models.Stock.id == rec.stock_id).first()
            if stock:
                result.append({
                    "ticker": stock.symbol,
                    "action": rec.action.value if hasattr(rec.action, 'value') else rec.action,
                    "confidence_score": rec.confidence_score,
                    "reasoning_text": rec.reasoning_text,
                    "created_at": rec.created_at.strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # If DB is completely empty (no predictions run yet), provide a fallback 
        if not result:
            from utils.stock_data import get_real_time_price
            fallback = []
            for sym in ["AAPL", "NVDA"]:
                price = get_real_time_price(sym).get("current_price", 100)
                fallback.append({
                    "ticker": sym,
                    "action": "HOLD",
                    "confidence_score": 50.0,
                    "reasoning_text": f"Fallback: No ML data exists yet. Current real price is ${price}.",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            return fallback

        return result
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendations: {str(e)}")
