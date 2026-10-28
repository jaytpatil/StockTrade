from typing import Dict, Any

def generate_recommendation(
    current_price: float, 
    predicted_target: float, 
    rsi: float, 
    macd_line: float, 
    macd_signal: float, 
    sma_20: float, 
    sma_50: float, 
    sentiment_score: float = 0.0
) -> Dict[str, Any]:
    """
    Multifactorial Recommendation Engine combining Machine Learning targets 
    with standard Technical Analysis indicators and NLP polarity.
    """
    
    # Trackers for conviction scoring
    bullish_signals = 0
    bearish_signals = 0
    total_signals = 5
    reasons = []

    # 1. AI Future Prediction Trend
    predicted_pct_change = ((predicted_target - current_price) / current_price) * 100
    if predicted_pct_change > 1.5:
        bullish_signals += 1.5  # Heavy weight on the ML pipeline
        reasons.append(f"AI Prediction targets {predicted_pct_change:.2f}% upside.")
    elif predicted_pct_change < -1.5:
        bearish_signals += 1.5
        reasons.append(f"AI Prediction detects {predicted_pct_change:.2f}% downside crash risk.")
    else:
        reasons.append("AI Prediction expects flat consolidation.")

    # 2. RSI (Relative Strength Index)
    if rsi < 30:
        bullish_signals += 1
        reasons.append(f"RSI ({rsi:.1f}) indicates historically Oversold momentum.")
    elif rsi > 70:
        bearish_signals += 1
        reasons.append(f"RSI ({rsi:.1f}) indicates heavily Overbought exhaustion.")
    else:
        reasons.append(f"RSI ({rsi:.1f}) is neutral.")

    # 3. MACD Crossover
    if macd_line > macd_signal:
        bullish_signals += 1
        reasons.append("MACD is showing a bullish divergence crossover.")
    elif macd_line < macd_signal:
        bearish_signals += 1
        reasons.append("MACD triggered a bearish downside crossover signal.")

    # 4. Moving Average Crossover (Golden/Death Cross proxy)
    if sma_20 > sma_50:
        bullish_signals += 1
        reasons.append("Short-term SMA20 is trading above SMA50, sustaining a breakout trend.")
    elif sma_20 < sma_50:
        bearish_signals += 1
        reasons.append("Short-term SMA20 breached below SMA50 (Death Cross behavior).")

    # 5. NLP Sentiment Adjustment
    if sentiment_score > 0.4:
         bullish_signals += 0.5
         reasons.append("Market NLP sentiment analysis is strongly positive.")
    elif sentiment_score < -0.4:
         bearish_signals += 0.5
         reasons.append("Global news sentiment reads largely negative/fearful.")

    # Mathematical Scoring Matrix
    # Normalizing conviction scale 0 to 100
    conviction_weight = bullish_signals - bearish_signals
    
    # Dynamic confidence calculation bounding logic
    if conviction_weight > 2:
        recommendation = "BUY"
        # Confidence scales upwards as more signals align (Max score roughly ~96%)
        confidence = 65.0 + ((bullish_signals / total_signals) * 31.0)
    elif conviction_weight < -1.5:
        recommendation = "SELL"
        confidence = 65.0 + ((bearish_signals / total_signals) * 31.0)
    else:
        recommendation = "HOLD"
        # Holds have higher confidence when signals perfectly conflict perfectly nullifying each other
        conflict_ratio = abs(bullish_signals - bearish_signals)
        confidence = 85.0 - (conflict_ratio * 10) 

    return {
        "recommendation": recommendation,
        "confidence": round(min(confidence, 99.9), 1), # Clamp safety
        "reason": " | ".join(reasons),
        "risk_warning": (
            "DISCLAIMER: The information provided creates algorithmic signals based on rigid technical calculations "
            "and machine learning estimates. It is strictly for educational purposes and DOES NOT constitute financial advice. "
            "Past patterns do not guarantee future market behavior. Trading equities or crypto is highly risky."
        )
    }

if __name__ == "__main__":
    # Test internal execution
    analysis = generate_recommendation(
        current_price=150.0,
        predicted_target=156.0, # Bullish prediction
        rsi=28.5,               # Bullish oversold
        macd_line=1.2,          
        macd_signal=0.8,        # Bullish cross
        sma_20=148.0,
        sma_50=142.0,           # Bullish trend
        sentiment_score=0.6     # Bullish news
    )
    
    print(f"Signal: {analysis['recommendation']} ({analysis['confidence']}%)")
    print("\nReasons:")
    for rule in analysis['reason'].split(' | '):
        print(f"- {rule}")
    print(f"\n{analysis['risk_warning']}")
