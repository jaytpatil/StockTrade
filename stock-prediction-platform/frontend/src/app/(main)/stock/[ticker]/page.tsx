"use client";
import React, { use, useState, useEffect, useCallback } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowUpRight, ArrowDownRight, Activity, ArrowRight, Loader2, Wifi, Wallet, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { MarketService, TradingService, AuthService } from '@/services/api';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function StockDetailsPage({ params }: { params: Promise<{ ticker: string }> }) {
  const resolvedParams = use(params);
  const ticker = resolvedParams.ticker.toUpperCase();

  const [priceData, setPriceData] = useState<any[]>([]);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [priceChange, setPriceChange] = useState<number>(0.0);
  const [indicators, setIndicators] = useState<any>({});
  const [timeframe, setTimeframe] = useState<string>('1M');
  const [loading, setLoading] = useState<boolean>(true);

  // Trading Widget State
  const [userBalance, setUserBalance] = useState<number | null>(null);
  const [ownedShares, setOwnedShares] = useState<number>(0);
  const [tradeTab, setTradeTab] = useState<'BUY' | 'SELL'>('BUY');
  const [orderShares, setOrderShares] = useState<string>('1');
  const [tradeLoading, setTradeLoading] = useState<boolean>(false);
  const [tradeMessage, setTradeMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [guestLoading, setGuestLoading] = useState<boolean>(false);

  // Handle live socket price tick
  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'TICKER_UPDATE' && message.data?.ticker === ticker) {
      const { price, change } = message.data;
      if (price) {
        setCurrentPrice(price);
        setPriceChange(change || 0.0);
      }
    }
  }, [ticker]);

  const { isConnected } = useWebSocket({
    subscribeTicker: ticker,
    onMessage: handleWebSocketMessage
  });

  const loadUserData = async () => {
    try {
      const portfolio = await TradingService.fetchPortfolio();
      if (portfolio) {
        setUserBalance(portfolio.cash_balance);
        const pos = portfolio.positions?.find((p: any) => p.symbol === ticker);
        setOwnedShares(pos ? pos.shares : 0);
      }
    } catch (e) {
      // User might be unauthenticated
      setUserBalance(null);
    }
  };

  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      setLoading(true);
      try {
        const [historyRes, indicatorRes] = await Promise.allSettled([
          MarketService.fetchHistoricalData(ticker, timeframe.toLowerCase()),
          MarketService.fetchIndicators(ticker)
        ]);

        if (isMounted) {
          if (historyRes.status === 'fulfilled' && historyRes.value?.data) {
            const formatted = historyRes.value.data.map((item: any) => ({
              date: item.Date || item.date,
              price: item.Close || item.close || item.price
            }));
            setPriceData(formatted);
            if (formatted.length > 0) {
              const last = formatted[formatted.length - 1].price;
              const prev = formatted.length > 1 ? formatted[formatted.length - 2].price : last;
              setCurrentPrice(last);
              setPriceChange(Number((((last - prev) / prev) * 100).toFixed(2)));
            }
          }

          if (indicatorRes.status === 'fulfilled' && indicatorRes.value?.indicators) {
            setIndicators(indicatorRes.value.indicators);
          }
        }
      } catch (err) {
        console.error("Failed loading stock detail data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadData();
    loadUserData();

    const handlePortfolioUpdate = () => {
      loadUserData();
    };
    window.addEventListener('portfolio-updated', handlePortfolioUpdate);

    return () => { 
      isMounted = false; 
      window.removeEventListener('portfolio-updated', handlePortfolioUpdate);
    };
  }, [ticker, timeframe]);

  const handleGuestQuickStart = async () => {
    setGuestLoading(true);
    setTradeMessage(null);
    try {
      await AuthService.loginAsGuest();
      await loadUserData();
      window.dispatchEvent(new Event('portfolio-updated'));
      window.dispatchEvent(new Event('auth-changed'));
      setTradeMessage({ text: "Demo session active! $100,000 ready to trade.", type: "success" });
    } catch (err) {
      setTradeMessage({ text: "Failed to initialize guest demo session.", type: "error" });
    } finally {
      setGuestLoading(false);
    }
  };

  const handleExecuteTrade = async (e: React.FormEvent) => {
    e.preventDefault();
    setTradeMessage(null);

    const sharesNum = parseFloat(orderShares);
    if (isNaN(sharesNum) || sharesNum <= 0) {
      setTradeMessage({ text: "Please enter a valid positive number of shares.", type: "error" });
      return;
    }

    setTradeLoading(true);
    try {
      if (tradeTab === 'BUY') {
        const res = await TradingService.buy(ticker, sharesNum);
        setTradeMessage({ text: res.message || `Successfully purchased ${sharesNum} shares of ${ticker}!`, type: 'success' });
      } else {
        const res = await TradingService.sell(ticker, sharesNum);
        setTradeMessage({ text: res.message || `Successfully sold ${sharesNum} shares of ${ticker}!`, type: 'success' });
      }

      await loadUserData();
      window.dispatchEvent(new Event('portfolio-updated'));
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setTradeMessage({
        text: typeof detail === 'string' ? detail : `Failed to execute ${tradeTab} order. Check your balance or credentials.`,
        type: 'error'
      });
    } finally {
      setTradeLoading(false);
    }
  };

  const parsedShares = parseFloat(orderShares) || 0;
  const estimatedTotal = (currentPrice || 0) * parsedShares;

  const rsiValue = indicators?.RSI ?? indicators?.RSI_14 ?? indicators?.momentum?.RSI_14 ?? null;
  const macdValue = indicators?.MACD ?? indicators?.momentum?.MACD?.line ?? null;
  const sma50Value = indicators?.SMA_50 ?? indicators?.trend?.SMA_50 ?? null;

  return (
    <div className="space-y-6">
      
      {/* Header Profile */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-4xl font-extrabold">{ticker}</h1>
            <span className="px-3 py-1 bg-teal-500/10 text-teal-400 border border-teal-500/20 rounded-full text-xs font-bold tracking-widest uppercase flex items-center gap-1.5">
              {isConnected ? <Wifi className="w-3 h-3 animate-pulse" /> : null}
              {isConnected ? 'LIVE FEED' : 'ACTIVE TRADING'}
            </span>
          </div>
          <div className="text-3xl font-light flex items-center gap-3">
            {currentPrice !== null ? `$${currentPrice.toFixed(2)}` : '$--.--'} 
            <span className={`text-lg flex items-center font-medium ${priceChange >= 0 ? 'text-teal-400' : 'text-red-400'}`}>
              {priceChange >= 0 ? <ArrowUpRight className="w-5 h-5" /> : <ArrowDownRight className="w-5 h-5" />}
              {Math.abs(priceChange)}%
            </span>
          </div>
        </div>

        <div className="flex gap-3">
          <Link href={`/stock/${ticker}/prediction`} className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2 shadow-[0_0_15px_rgba(79,70,229,0.4)] transition-all">
            <Activity className="w-5 h-5" />
            View AI Forecast
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>

      {/* Main Grid: Chart + Live Trading Execution Widget */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Interactive Area Chart */}
        <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-bold text-gray-300 flex items-center gap-2">
              Price Action ({timeframe})
              {loading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
            </h3>
            <div className="flex gap-2">
              {['1D', '1W', '1M', '3M', '1Y'].map(t => (
                <button 
                  key={t} 
                  onClick={() => setTimeframe(t)}
                  className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors ${
                    t === timeframe ? 'bg-white/20 text-white' : 'text-gray-500 hover:text-gray-300'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          <div className="h-[380px] w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <AreaChart data={priceData}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" stroke="#6b7280" tick={{fill: '#6b7280'}} axisLine={false} tickLine={false} />
                <YAxis stroke="#6b7280" tick={{fill: '#6b7280'}} axisLine={false} tickLine={false} domain={['dataMin - 2', 'dataMax + 2']} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(10, 10, 15, 0.9)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', backdropFilter: 'blur(10px)' }}
                  itemStyle={{ color: '#e5e7eb' }}
                />
                <Area type="monotone" dataKey="price" stroke="#4f46e5" strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right Column: Live Trading Execution Widget */}
        <div className="bg-[#0f111a]/90 border border-white/10 rounded-2xl p-6 backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <span className="font-bold text-white text-base flex items-center gap-2">
                <Wallet className="w-4 h-4 text-teal-400" /> Trade {ticker}
              </span>
              <span className="text-xs text-gray-400 font-mono">
                {currentPrice ? `$${currentPrice.toFixed(2)}/share` : 'Loading...'}
              </span>
            </div>

            {/* If user has no active account/token */}
            {userBalance === null ? (
              <div className="my-6 p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-center">
                <p className="text-xs text-gray-300 mb-3">Sign in or activate guest demo to trade with $100k virtual cash.</p>
                <button
                  type="button"
                  onClick={handleGuestQuickStart}
                  disabled={guestLoading}
                  className="w-full py-2.5 bg-teal-500 hover:bg-teal-400 text-black text-xs font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(45,212,191,0.3)] flex items-center justify-center gap-1.5 disabled:opacity-50"
                >
                  {guestLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  Instant Guest Trading Mode
                </button>
              </div>
            ) : (
              <div className="mt-4 mb-4">
                {/* Buying Power & Owned Shares Banner */}
                <div className="grid grid-cols-2 gap-2 p-3 bg-white/5 rounded-xl border border-white/5 text-xs mb-4">
                  <div>
                    <span className="text-gray-400 block text-[11px]">Buying Power</span>
                    <span className="font-bold text-teal-400 font-mono text-sm">
                      ${userBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400 block text-[11px]">Shares Owned</span>
                    <span className="font-bold text-white font-mono text-sm">
                      {ownedShares.toLocaleString()} {ticker}
                    </span>
                  </div>
                </div>

                {/* BUY / SELL Switcher */}
                <div className="flex rounded-xl bg-white/5 p-1 mb-4 border border-white/5">
                  <button
                    type="button"
                    onClick={() => { setTradeTab('BUY'); setTradeMessage(null); }}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                      tradeTab === 'BUY'
                        ? 'bg-teal-500 text-black shadow-lg shadow-teal-500/30'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    BUY {ticker}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setTradeTab('SELL'); setTradeMessage(null); }}
                    className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                      tradeTab === 'SELL'
                        ? 'bg-red-500 text-white shadow-lg shadow-red-500/30'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    SELL {ticker}
                  </button>
                </div>

                {/* Trade Form */}
                <form onSubmit={handleExecuteTrade} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1.5">Number of Shares</label>
                    <div className="relative">
                      <input
                        type="number"
                        step="any"
                        min="0.0001"
                        value={orderShares}
                        onChange={(e) => setOrderShares(e.target.value)}
                        placeholder="1.0"
                        className="w-full bg-[#0a0a0f] border border-white/10 rounded-xl px-4 py-2.5 text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
                        required
                      />
                    </div>
                  </div>

                  {/* Quick Share Buttons */}
                  <div className="flex gap-2">
                    {[1, 5, 10, 25].map(cnt => (
                      <button
                        key={cnt}
                        type="button"
                        onClick={() => setOrderShares(cnt.toString())}
                        className="flex-1 py-1 bg-white/5 hover:bg-white/10 text-gray-300 text-xs rounded-lg border border-white/5 transition-all font-mono"
                      >
                        +{cnt}
                      </button>
                    ))}
                    {tradeTab === 'SELL' && ownedShares > 0 && (
                      <button
                        type="button"
                        onClick={() => setOrderShares(ownedShares.toString())}
                        className="flex-1 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs rounded-lg border border-red-500/30 transition-all font-bold"
                      >
                        MAX
                      </button>
                    )}
                  </div>

                  {/* Summary Box */}
                  <div className="p-3 bg-white/5 rounded-xl border border-white/5 space-y-2 text-xs">
                    <div className="flex justify-between text-gray-400">
                      <span>Market Price</span>
                      <span className="text-white font-mono">${currentPrice ? currentPrice.toFixed(2) : '--.--'}</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Order Quantity</span>
                      <span className="text-white font-mono">{parsedShares} shares</span>
                    </div>
                    <div className="border-t border-white/10 pt-2 flex justify-between font-bold">
                      <span className="text-gray-200">{tradeTab === 'BUY' ? 'Total Cost' : 'Total Proceeds'}</span>
                      <span className={`font-mono text-sm ${tradeTab === 'BUY' ? 'text-teal-400' : 'text-emerald-400'}`}>
                        ${estimatedTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>

                  {/* Alerts */}
                  {tradeMessage && (
                    <div className={`p-3 rounded-xl flex items-center gap-2 text-xs ${
                      tradeMessage.type === 'success'
                        ? 'bg-teal-500/10 border border-teal-500/30 text-teal-300'
                        : 'bg-red-500/10 border border-red-500/30 text-red-300'
                    }`}>
                      {tradeMessage.type === 'success' ? (
                        <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-teal-400" />
                      ) : (
                        <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-400" />
                      )}
                      <span>{tradeMessage.text}</span>
                    </div>
                  )}

                  {/* Action Button */}
                  <button
                    type="submit"
                    disabled={tradeLoading || !currentPrice || parsedShares <= 0}
                    className={`w-full py-3 px-4 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50 ${
                      tradeTab === 'BUY'
                        ? 'bg-teal-500 hover:bg-teal-400 text-black shadow-[0_0_20px_rgba(45,212,191,0.4)]'
                        : 'bg-red-600 hover:bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)]'
                    }`}
                  >
                    {tradeLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                    Confirm {tradeTab} {ticker}
                  </button>
                </form>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-white/10 text-center">
            <span className="text-[11px] text-gray-500">
              Virtual paper trading • Live market prices • Zero risk
            </span>
          </div>
        </div>

      </div>

      {/* Technical Indicators */}
      <h3 className="text-xl font-bold pt-4 mb-4">Technical Indicators</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/10 rounded-bl-full blur-2xl" />
          <h4 className="text-gray-400 text-sm font-medium mb-1">RSI (14)</h4>
          <div className="text-3xl font-black mb-2">
            {rsiValue != null ? Number(rsiValue).toFixed(1) : (loading ? '--' : 'N/A')}
          </div>
          <div className={`text-xs font-bold tracking-widest uppercase ${
            rsiValue != null ? (Number(rsiValue) > 70 ? 'text-red-400' : (Number(rsiValue) < 30 ? 'text-teal-400' : 'text-yellow-400')) : 'text-gray-400'
          }`}>
            {rsiValue != null ? (Number(rsiValue) > 70 ? 'Overbought' : (Number(rsiValue) < 30 ? 'Oversold' : 'Neutral')) : (loading ? 'Calculating' : 'No Data')}
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/10 rounded-bl-full blur-2xl" />
          <h4 className="text-gray-400 text-sm font-medium mb-1">MACD</h4>
          <div className="text-3xl font-black mb-2">
            {macdValue != null ? (Number(macdValue) >= 0 ? `+${Number(macdValue).toFixed(2)}` : Number(macdValue).toFixed(2)) : (loading ? '--' : 'N/A')}
          </div>
          <div className="text-xs text-teal-400 font-bold tracking-widest uppercase">
            {macdValue != null ? (Number(macdValue) >= 0 ? 'Bullish Momentum' : 'Bearish Divergence') : (loading ? 'Calculating' : 'Signal')}
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-bl-full blur-2xl" />
          <h4 className="text-gray-400 text-sm font-medium mb-1">SMA (50)</h4>
          <div className="text-3xl font-black mb-2">
            {sma50Value != null ? `$${Number(sma50Value).toFixed(2)}` : (currentPrice ? `$${Number(currentPrice).toFixed(2)}` : (loading ? '--' : 'N/A'))}
          </div>
          <div className="text-xs text-indigo-400 font-bold tracking-widest uppercase">50-Day Moving Avg</div>
        </div>
      </div>

    </div>
  );
}
