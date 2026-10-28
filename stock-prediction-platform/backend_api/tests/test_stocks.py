import pytest

def test_get_stock_list(client):
    response = client.get("/stocks/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Validate payload structure
    assert "symbol" in data[0]

def test_get_stock_history(client):
    symbol = "TSLA"
    response = client.get(f"/stocks/history/{symbol}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "TSLA"
    assert isinstance(data["data"], list)

def test_get_stock_technical_indicators(client):
    symbol = "NVDA"
    response = client.get(f"/stocks/indicators/{symbol}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert "indicators" in data
    
    # Check if RSI/MACD keys actually generate mathematically
    indicators = data["indicators"]
    assert "RSI" in indicators
    assert "MACD" in indicators
    assert "SMA_50" in indicators
