import pytest
from unittest.mock import patch

def test_prediction_endpoint(client):
    """
    Mocks the XGBoost Pipeline directly here to avoid actually downloading 
    YFinance data over the network during unit test evaluations.
    """
    mock_prediction = {
        "symbol": "AAPL",
        "current_price": 150.0,
        "predicted_price_7D": 155.0,
        "percentage_diff": 3.3,
        "signal": "BUY",
        "model_engine": "XGBoost Test"
    }

    # Patching strictly bypassing the actual math execution 
    # to evaluate REST endpoint bindings correctly.
    with patch("utils.ml_pipeline.XGBoostPipeline.predict_future", return_value=mock_prediction):
        response = client.get("/stocks/predict/AAPL")
        
        # Standard responses mapping the JSON dictionary expectations
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["status"] == "success"
        assert data["signal"] == "BUY"
        assert data["saved_to_db"] is True

def test_recommendation_endpoint(client):
    """Hits the recommendation fallback stub directly."""
    response = client.get("/stocks/recommend/MSFT")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "MSFT"
    assert data["recommendation"] in ["BUY", "SELL", "HOLD"]
    assert "confidence" in data
