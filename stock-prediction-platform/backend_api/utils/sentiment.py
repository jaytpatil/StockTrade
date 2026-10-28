import json
import logging
from typing import Dict, Any

try:
    import yfinance as yf
    from textblob import TextBlob
except ImportError:
    logging.warning("Please run: pip install yfinance textblob")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_and_analyze_sentiment(symbol: str) -> Dict[str, Any]:
    """
    Fetches recent news headlines for a given stock symbol using yfinance,
    processes them through TextBlob NLP, and computes a polarity score.
    Returns a unified JSON-ready dictionary.
    """
    symbol = symbol.upper()
    try:
        logging.info(f"Fetching news explicitly for {symbol}...")
        ticker = yf.Ticker(symbol)
        
        # Latest yfinance returns news as a list of dicts.
        news_data = ticker.news
        
        if not news_data:
            return {
                "symbol": symbol,
                "status": "warning",
                "message": "No recent news headlines found.",
                "sentiment_score": 0.0,
                "sentiment_label": "Neutral",
                "headlines_analyzed": []
            }
            
        headlines = []
        total_polarity = 0.0
        analyzed_count = 0
        
        # Extract parsing based on standard yfinance dictionary structures
        for article in news_data:
            title = article.get('title', '')
            if title:
                # Calculate NLP sentiment natively mapping from -1.0 to 1.0
                blob = TextBlob(title)
                polarity = blob.sentiment.polarity
                
                headlines.append({
                    "title": title,
                    "publisher": article.get('publisher', 'Unknown'),
                    "link": article.get('link', ''),
                    "score": round(polarity, 3)
                })
                
                total_polarity += polarity
                analyzed_count += 1
                
        # Handle zero-division safely
        if analyzed_count == 0:
            avg_sentiment = 0.0
        else:
            avg_sentiment = total_polarity / analyzed_count
            
        # Determine the Categorical String label
        label = "Neutral"
        if avg_sentiment >= 0.15:
            label = "Positive"
        elif avg_sentiment <= -0.15:
            label = "Negative"
            
        response_json = {
            "symbol": symbol,
            "status": "success",
            "aggregate_sentiment_score": round(avg_sentiment, 3),
            "sentiment_label": label,
            "headlines_analyzed": headlines
        }
        
        return response_json
        
    except Exception as e:
        logging.error(f"Failed to fetch or parse sentiment for {symbol}: {str(e)}")
        return {
            "symbol": symbol,
            "status": "error",
            "message": f"NLP/Network exception: {str(e)}",
            "aggregate_sentiment_score": 0.0,
            "sentiment_label": "Neutral",
            "headlines_analyzed": []
        }

if __name__ == "__main__":
    # Test script for isolated validation
    print("NLP Pipeline Booting...")
    result = fetch_and_analyze_sentiment("AAPL")
    print(json.dumps(result, indent=2))
