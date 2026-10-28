"use client";
import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Search as SearchIcon, Filter, ArrowRight, Loader2, TrendingUp } from 'lucide-react';
import { MarketService } from '@/services/api';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searched, setSearched] = useState<boolean>(false);

  const performSearch = useCallback(async (searchQuery: string) => {
    setLoading(true);
    try {
      const data = await MarketService.searchStocks(searchQuery);
      setResults(data || []);
      setSearched(Boolean(searchQuery.trim()));
    } catch (err) {
      console.error("Search failed:", err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load with popular assets
  useEffect(() => {
    performSearch('');
  }, [performSearch]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold mb-4">Stock Intelligence Screener</h1>
        <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
          Search across any existing equities, crypto, and ETFs in real-time. Our models run live forecasts on demand.
        </p>
        
        <form onSubmit={handleSubmit} className="relative max-w-3xl mx-auto group">
          <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <SearchIcon className="h-6 w-6 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
          </div>
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search any ticker (e.g. AAPL, NVDA, AMZN, BTC-USD, RELIANCE.NS)..." 
            className="w-full bg-[#0a0a0f] border-2 border-white/10 rounded-2xl py-4 pl-14 pr-28 text-lg text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-all font-medium shadow-2xl"
          />
          <button 
            type="submit"
            disabled={loading}
            className="absolute right-2 top-2 bottom-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl px-6 font-bold transition-colors flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Scan"}
          </button>
        </form>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-md overflow-hidden">
        <div className="p-4 border-b border-white/10 flex justify-between items-center bg-black/20">
          <h2 className="font-semibold text-gray-300">
            {searched && query.trim() ? `Search Results for "${query}"` : "Trending & Popular Assets"}
          </h2>
          <span className="text-xs text-gray-400 font-medium px-3 py-1 bg-white/5 rounded-full border border-white/10">
            {results.length} found
          </span>
        </div>
        
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center text-gray-400 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
            <p className="text-sm">Scanning global stock exchanges & markets...</p>
          </div>
        ) : results.length === 0 ? (
          <div className="p-16 text-center text-gray-400">
            <p className="text-lg font-medium text-gray-300 mb-1">No matching assets found</p>
            <p className="text-sm">Try searching for standard ticker symbols like AAPL, MSFT, TSLA, or company names.</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {results.map((result, idx) => (
              <div key={`${result.symbol}-${idx}`} className="p-4 flex items-center justify-between hover:bg-white/5 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center font-bold text-white tracking-wider">
                    {result.symbol.slice(0, 2)}
                  </div>
                  <div>
                    <div className="font-bold text-lg text-white flex items-center gap-2">
                      {result.symbol}
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                        {result.type || 'EQUITY'}
                      </span>
                    </div>
                    <div className="text-sm text-gray-400">{result.name} &bull; <span className="text-gray-500">{result.sector}</span></div>
                  </div>
                </div>
                
                <div className="flex items-center gap-4">
                  <Link 
                    href={`/stock/${result.symbol}`}
                    className="flex items-center gap-2 text-sm font-semibold bg-white/10 hover:bg-indigo-600 hover:text-white text-gray-200 px-4 py-2 rounded-xl transition-all"
                  >
                    <span>Analyze</span>
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
