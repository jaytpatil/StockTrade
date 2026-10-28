from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas.schemas import StockData

router = APIRouter()

@router.get("/", response_model=List[StockData])
def get_stocks():
    # Stub implementation returning the hardcoded tickers
    return [
        {"id": 1, "ticker": "AAPL", "company_name": "Apple Inc.", "predictions": []},
        {"id": 2, "ticker": "TSLA", "company_name": "Tesla Inc.", "predictions": []},
        {"id": 3, "ticker": "NVDA", "company_name": "NVIDIA Corp.", "predictions": []},
        {"id": 4, "ticker": "BTC", "company_name": "Bitcoin", "predictions": []},
    ]

@router.get("/{ticker}", response_model=StockData)
def get_stock_by_ticker(ticker: str):
    return {"id": 1, "ticker": ticker.upper(), "company_name": "Mock Company", "predictions": []}
