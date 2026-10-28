"use client";
import React, { useState, useEffect, useCallback } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { 
  DollarSign, ArrowUpRight, ArrowDownRight, ShieldAlert, Loader2, Wifi, WifiOff, 
  PlusCircle, Wallet, TrendingUp, History, Briefcase, ArrowRight, X, CheckCircle2, Sparkles
} from 'lucide-react';
import Link from 'next/link';
import { MarketService, TradingService, AuthService } from '@/services/api';
import { useWebSocket } from '@/hooks/useWebSocket';

const portfolioData = [
  { name: 'Mon', value: 98000 },
  { name: 'Tue', value: 99400 },
  { name: 'Wed', value: 98900 },
  { name: 'Thu', value: 101200 },
  { name: 'Fri', value: 102500 },
  { name: 'Sat', value: 102100 },
  { name: 'Sun', value: 103850 },
];

export default function DashboardPage() {
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Deposit Modal State
  const [isDepositOpen, setIsDepositOpen] = useState(false);
  const [depositAmount, setDepositAmount] = useState('25000');
  const [depositLoading, setDepositLoading] = useState(false);
  const [depositMessage, setDepositMessage] = useState<string | null>(null);

  const fetchPortfolioData = async () => {
    try {
      const data = await TradingService.fetchPortfolio();
      if (data) {
        setPortfolio(data);
      }
    } catch (err) {
      console.warn("Could not fetch user portfolio, using defaults:", err);
    }
  };

  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'DASHBOARD_UPDATE') {
      const { watchlist } = message.data;
      if (watchlist) setWatchlist(watchlist);
    }
  }, []);

  const { isConnected } = useWebSocket({
    onMessage: handleWebSocketMessage
  });

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const [summary, portRes] = await Promise.allSettled([
          MarketService.fetchDashboardSummary(),
          TradingService.fetchPortfolio()
        ]);

        if (summary.status === 'fulfilled' && summary.value?.watchlist) {
          setWatchlist(summary.value.watchlist);
        }

        if (portRes.status === 'fulfilled' && portRes.value) {
          setPortfolio(portRes.value);
        }
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();

    const handlePortfolioUpdate = () => {
      fetchPortfolioData();
    };
    window.addEventListener('portfolio-updated', handlePortfolioUpdate);

    return () => {
      window.removeEventListener('portfolio-updated', handlePortfolioUpdate);
    };
  }, []);

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();
    const amountNum = parseFloat(depositAmount);
    if (isNaN(amountNum) || amountNum <= 0) return;

    setDepositLoading(true);
    setDepositMessage(null);
    try {
      const res = await TradingService.deposit(amountNum);
      setDepositMessage(res.message || `Deposited $${amountNum.toLocaleString()} successfully!`);
      await fetchPortfolioData();
      window.dispatchEvent(new Event('portfolio-updated'));
      setTimeout(() => {
        setIsDepositOpen(false);
        setDepositMessage(null);
      }, 1200);
    } catch (err: any) {
      setDepositMessage("Failed to deposit virtual funds.");
    } finally {
      setDepositLoading(false);
    }
  };

  const cashBalance = portfolio?.cash_balance ?? 100000.0;
  const portfolioValue = portfolio?.portfolio_value ?? 0.0;
  const netWorth = portfolio?.net_worth ?? cashBalance;
  const positions = portfolio?.positions || [];
  const transactions = portfolio?.transactions || [];

  return (
    <div className="space-y-6">
      
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              Trading Dashboard
            </h1>
            <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
              isConnected 
                ? 'bg-teal-500/10 text-teal-400 border-teal-500/30' 
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}>
              {isConnected ? <Wifi className="w-3.5 h-3.5 animate-pulse" /> : <WifiOff className="w-3.5 h-3.5" />}
              {isConnected ? 'LIVE FEED' : 'CONNECTING...'}
            </div>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            Real-time simulated trading environment • Real stock prices • Zero risk
          </p>
        </div>

        {/* Add Funds Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsDepositOpen(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 text-white font-bold text-sm rounded-xl shadow-[0_0_20px_rgba(45,212,191,0.3)] transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            Add Virtual Funds
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>Total Net Worth</span>
            <Wallet className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            ${netWorth.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-teal-400 mt-1 font-semibold flex items-center">
            <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> Cash + Stock Positions
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>Virtual Cash Balance</span>
            <DollarSign className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-black text-teal-400 font-mono">
            ${cashBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            Available buying power
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>Invested in Stocks</span>
            <Briefcase className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            ${portfolioValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {positions.length} active holding{positions.length === 1 ? '' : 's'}
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-md">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>Platform Accuracy (30D)</span>
            <TrendingUp className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-black text-white">84.2%</div>
          <div className="text-xs text-gray-400 mt-1">Validated against market close</div>
        </div>
      </div>

      {/* Main Grid: Chart + Watchlist */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Main Chart Section */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md">
            <div className="flex justify-between items-center mb-6">
              <div>
                <div className="text-sm text-gray-400 font-medium">Portfolio Growth Trajectory</div>
                <div className="text-3xl font-extrabold flex items-center gap-3">
                  ${netWorth.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  <span className="text-sm font-semibold flex items-center bg-teal-500/10 text-teal-400 px-2 py-1 rounded-lg">
                    <ArrowUpRight className="w-4 h-4 mr-1" /> Active
                  </span>
                </div>
              </div>
            </div>

            <div className="h-[280px] w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <AreaChart data={portfolioData} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'rgba(10, 10, 15, 0.9)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', backdropFilter: 'blur(10px)' }}
                    itemStyle={{ color: '#e5e7eb' }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#4f46e5" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Watchlist Sidebar */}
        <div className="bg-white/5 border border-white/10 rounded-2xl flex flex-col overflow-hidden backdrop-blur-md">
          <div className="p-5 border-b border-white/10 flex justify-between items-center">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              Live AI Watchlist
              {loading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
            </h3>
            <Link href="/search" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">
              View All
            </Link>
          </div>
          <div className="flex-1 overflow-y-auto max-h-[340px]">
            {!loading && watchlist.length === 0 ? (
              <div className="p-8 text-center text-gray-400 text-sm">Failed to load real-time market data.</div>
            ) : (
              watchlist.map((item, idx) => (
                <Link href={`/stock/${item.ticker}`} key={idx}>
                  <div className="flex items-center justify-between p-3.5 border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer group">
                    <div>
                      <div className="font-bold text-white group-hover:text-indigo-400 transition-colors text-sm">{item.ticker}</div>
                      <div className="text-[11px] text-gray-500 max-w-[120px] truncate">{item.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium text-sm">${Number(item.price).toFixed(2)}</div>
                      <div className={`text-[11px] flex items-center justify-end gap-0.5 font-bold ${item.change >= 0 ? 'text-teal-400' : 'text-red-400'}`}>
                        {item.change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {Math.abs(item.change)}%
                      </div>
                    </div>
                    <div className={`px-2 py-0.5 rounded text-[10px] font-black tracking-wider ${
                      item.signal === 'BUY' ? 'bg-teal-500/20 text-teal-400' : 
                      item.signal === 'SELL' ? 'bg-red-500/20 text-red-400' : 
                      'bg-yellow-500/20 text-yellow-500'
                    }`}>
                      {item.signal}
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

      </div>

      {/* Active Holdings Section */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-indigo-400" />
              Active Stock Positions
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">Your currently held shares with real-time valuation and profit/loss.</p>
          </div>
          <Link
            href="/search"
            className="text-xs text-teal-400 hover:text-teal-300 font-bold flex items-center gap-1"
          >
            Find Stocks <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {positions.length === 0 ? (
          <div className="text-center py-10 border border-dashed border-white/10 rounded-xl">
            <p className="text-gray-400 text-sm mb-3">You do not own any stock shares yet.</p>
            <Link
              href="/stock/AAPL"
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)]"
            >
              Trade AAPL Now <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-gray-400 uppercase border-b border-white/10">
                <tr>
                  <th className="py-3 px-4">Asset</th>
                  <th className="py-3 px-4">Shares</th>
                  <th className="py-3 px-4">Avg Buy Price</th>
                  <th className="py-3 px-4">Current Price</th>
                  <th className="py-3 px-4">Current Value</th>
                  <th className="py-3 px-4">Profit / Loss</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono">
                {positions.map((pos: any, idx: number) => (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 px-4 font-bold text-white font-sans flex items-center gap-2">
                      <span className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-300 flex items-center justify-center font-bold text-xs">
                        {pos.symbol.slice(0, 2)}
                      </span>
                      {pos.symbol}
                    </td>
                    <td className="py-3 px-4 text-gray-200">{pos.shares}</td>
                    <td className="py-3 px-4 text-gray-300">${Number(pos.average_buy_price).toFixed(2)}</td>
                    <td className="py-3 px-4 text-white font-bold">${Number(pos.current_price).toFixed(2)}</td>
                    <td className="py-3 px-4 text-teal-400 font-bold">${Number(pos.current_value).toFixed(2)}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                        pos.profit_loss >= 0 ? 'bg-teal-500/10 text-teal-400' : 'bg-red-500/10 text-red-400'
                      }`}>
                        {pos.profit_loss >= 0 ? '+' : ''}${Number(pos.profit_loss).toFixed(2)} ({pos.profit_loss_pct}%)
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-sans">
                      <Link
                        href={`/stock/${pos.symbol}`}
                        className="px-3 py-1 bg-white/10 hover:bg-white/20 text-white text-xs font-bold rounded-lg transition-colors inline-block"
                      >
                        Trade
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Trade Ledger / Recent Activity */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-teal-400" />
            Recent Trading Ledger
          </h3>
          <span className="text-xs text-gray-400">Audit trail of all simulated orders</span>
        </div>

        {transactions.length === 0 ? (
          <div className="text-center py-6 text-gray-400 text-sm">
            No transactions recorded yet. Execute your first trade or deposit virtual funds!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-gray-400 uppercase border-b border-white/10">
                <tr>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Symbol</th>
                  <th className="py-3 px-4">Shares</th>
                  <th className="py-3 px-4">Execution Price</th>
                  <th className="py-3 px-4">Total Amount</th>
                  <th className="py-3 px-4 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-xs">
                {transactions.map((tx: any, idx: number) => (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="py-2.5 px-4 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-black tracking-wider ${
                        tx.type === 'BUY' ? 'bg-teal-500/20 text-teal-400' :
                        tx.type === 'SELL' ? 'bg-red-500/20 text-red-400' :
                        'bg-indigo-500/20 text-indigo-400'
                      }`}>
                        {tx.type}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 font-bold text-white font-sans">{tx.symbol}</td>
                    <td className="py-2.5 px-4 text-gray-300">{tx.shares > 0 ? tx.shares : '—'}</td>
                    <td className="py-2.5 px-4 text-gray-300">
                      {tx.price_per_share > 0 ? `$${Number(tx.price_per_share).toFixed(2)}` : '—'}
                    </td>
                    <td className="py-2.5 px-4 font-bold text-teal-400">
                      ${Number(tx.total_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-4 text-right text-gray-500">{tx.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Deposit Virtual Currency Modal */}
      {isDepositOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
          <div className="bg-[#10121d] border border-white/15 rounded-3xl max-w-md w-full p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-200">
            <button
              onClick={() => setIsDepositOpen(false)}
              className="absolute top-5 right-5 text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-2xl bg-teal-500/20 flex items-center justify-center text-teal-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">Add Virtual Funds</h3>
                <p className="text-xs text-gray-400">Top up your simulated trading balance</p>
              </div>
            </div>

            <p className="text-xs text-gray-400 mb-4">
              All currency in this environment is 100% virtual and free. You can add as much as you need to test algorithms and practice trading strategies!
            </p>

            {/* Presets */}
            <div className="grid grid-cols-4 gap-2 mb-4">
              {['10000', '25000', '50000', '100000'].map(val => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setDepositAmount(val)}
                  className={`py-2 text-xs font-bold rounded-xl border transition-all ${
                    depositAmount === val
                      ? 'bg-teal-500 text-black border-teal-400 shadow-md shadow-teal-500/30'
                      : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'
                  }`}
                >
                  +${parseInt(val) / 1000}k
                </button>
              ))}
            </div>

            <form onSubmit={handleDeposit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1.5">Deposit Amount (USD)</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-gray-400 font-bold">$</div>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    className="w-full bg-[#0a0a0f] border border-white/10 rounded-xl pl-8 pr-4 py-3 text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
                    required
                  />
                </div>
              </div>

              {depositMessage && (
                <div className="p-3 bg-teal-500/10 border border-teal-500/30 rounded-xl flex items-center gap-2 text-xs text-teal-300">
                  <CheckCircle2 className="w-4 h-4 text-teal-400 flex-shrink-0" />
                  <span>{depositMessage}</span>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsDepositOpen(false)}
                  className="flex-1 py-3 bg-white/5 hover:bg-white/10 text-gray-300 font-bold text-xs rounded-xl border border-white/10 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={depositLoading || !depositAmount || parseFloat(depositAmount) <= 0}
                  className="flex-1 py-3 bg-teal-500 hover:bg-teal-400 text-black font-bold text-xs rounded-xl transition-all shadow-[0_0_15px_rgba(45,212,191,0.4)] flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {depositLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  Confirm Deposit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
