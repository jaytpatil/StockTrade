"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  TrendingUp, 
  ShieldCheck, 
  Zap, 
  Wallet, 
  ArrowRight, 
  UserCheck, 
  Sparkles, 
  BarChart3, 
  DollarSign, 
  Loader2 
} from 'lucide-react';
import { AuthService } from '@/services/api';

export default function WelcomePage() {
  const router = useRouter();
  const [guestLoading, setGuestLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGuestLogin = async () => {
    setGuestLoading(true);
    setError(null);
    try {
      await AuthService.loginAsGuest();
      router.push('/dashboard');
    } catch (err: any) {
      console.error("Guest login failed:", err);
      setError("Could not initialize guest session. Please try again or create an account.");
    } finally {
      setGuestLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#07070b] text-white flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      
      {/* Top Navigation */}
      <header className="border-b border-white/10 backdrop-blur-md bg-[#0a0a0f]/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-teal-400 p-[2px]">
              <div className="w-full h-full bg-[#0a0a0f] rounded-xl flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-teal-400" />
              </div>
            </div>
            <span className="font-extrabold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-teal-400">
              StockTrade
            </span>
          </div>

          <div className="flex items-center gap-4">
            <Link 
              href="/login" 
              className="text-sm font-semibold text-gray-300 hover:text-white px-4 py-2 rounded-xl hover:bg-white/5 transition-all"
            >
              Sign In
            </Link>
            <Link 
              href="/signup" 
              className="text-sm font-semibold bg-white/10 hover:bg-white/20 text-white px-5 py-2.5 rounded-xl border border-white/10 transition-all shadow-lg"
            >
              Register
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Welcoming Section */}
      <main className="max-w-7xl mx-auto px-6 py-16 flex-1 flex flex-col justify-center items-center text-center relative overflow-hidden">
        {/* Glow ambient background effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-indigo-600/20 to-teal-500/20 blur-[130px] rounded-full pointer-events-none" />

        {/* Hero Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-bold uppercase tracking-widest mb-6">
          <Sparkles className="w-4 h-4 text-teal-400" />
          <span>Real-Time Intelligence & Paper Trading Sandbox</span>
        </div>

        {/* Main Welcoming Headline */}
        <h1 className="text-5xl md:text-7xl font-black tracking-tight max-w-4xl mx-auto mb-6 leading-tight">
          Master the Market with <br className="hidden md:block" />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-teal-300 to-white">
            AI Predictions & Virtual Trading
          </span>
        </h1>

        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
          Every account receives <span className="text-teal-400 font-semibold">$100,000 in virtual funds</span> to test real-world stock trading risk-free. Run XGBoost machine learning forecasts, buy or sell any stock, and deposit funds anytime.
        </p>

        {error && (
          <div className="mb-6 p-3 px-6 bg-red-500/20 border border-red-500/40 text-red-300 rounded-xl text-sm font-medium">
            {error}
          </div>
        )}

        {/* Primary Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center w-full max-w-md mx-auto mb-16">
          <button
            onClick={handleGuestLogin}
            disabled={guestLoading}
            className="w-full sm:w-auto flex-1 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 text-black font-extrabold px-8 py-4 rounded-2xl shadow-[0_0_30px_rgba(45,212,191,0.3)] hover:shadow-[0_0_40px_rgba(45,212,191,0.5)] transition-all flex items-center justify-center gap-2 text-base"
          >
            {guestLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin text-black" />
                <span>Launching Guest Session...</span>
              </>
            ) : (
              <>
                <UserCheck className="w-5 h-5" />
                <span>Try as Guest ($100k Cash)</span>
              </>
            )}
          </button>

          <Link
            href="/signup"
            className="w-full sm:w-auto flex-1 bg-white/5 hover:bg-white/10 text-white font-bold px-8 py-4 rounded-2xl border border-white/10 hover:border-white/20 transition-all flex items-center justify-center gap-2 text-base"
          >
            <span>Create Account</span>
            <ArrowRight className="w-4 h-4 text-gray-400" />
          </Link>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl w-full text-left">
          
          <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md hover:border-indigo-500/50 transition-all group">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Wallet className="w-6 h-6 text-indigo-400" />
            </div>
            <h3 className="text-xl font-bold mb-2 text-white">$100,000 Virtual Starting Cash</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              Start trading immediately with zero risk. You can add or top up your demo balance at any time with a single click to test any strategy.
            </p>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md hover:border-teal-500/50 transition-all group">
            <div className="w-12 h-12 rounded-2xl bg-teal-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Zap className="w-6 h-6 text-teal-400" />
            </div>
            <h3 className="text-xl font-bold mb-2 text-white">Live Stock Buy & Sell Execution</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              Buy and sell any existing equity, ETF, or cryptocurrency at live market prices. Track your holdings, real-time P&L, and portfolio net worth.
            </p>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md hover:border-purple-500/50 transition-all group">
            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <BarChart3 className="w-6 h-6 text-purple-400" />
            </div>
            <h3 className="text-xl font-bold mb-2 text-white">7-Day AI Machine Learning Forecasts</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              Leverage an XGBoost regressor trained on technical momentum, RSI, MACD, and Bollinger Bands to project dynamic 7-day price trajectories.
            </p>
          </div>

        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-xs text-gray-500">
        <p>&copy; {new Date().getFullYear()} StockTrade Platform. Strictly for educational & simulation purposes.</p>
      </footer>

    </div>
  );
}
