"use client";
import React, { useState, useEffect } from 'react';
import { AIService } from '@/services/api';
import { Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecs = async () => {
      try {
        const data = await AIService.fetchRecommendations();
        setRecommendations(data || []);
      } catch (err) {
        console.error("Failed to load recommendations", err);
      } finally {
        setLoading(false);
      }
    };
    fetchRecs();
  }, []);

  return (
    <div className="max-w-5xl mx-auto py-12">
      <h1 className="text-3xl font-bold mb-8 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
        AI Recommendations Matrix
      </h1>
      
      <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-md">
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
          </div>
        ) : recommendations.length === 0 ? (
          <p className="text-gray-400 text-center py-10">No machine learning signals currently active.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-xs uppercase tracking-wider text-gray-500 bg-white/5">
                  <th className="p-4 font-medium">Asset</th>
                  <th className="p-4 font-medium">Signal</th>
                  <th className="p-4 font-medium">Confidence</th>
                  <th className="p-4 font-medium">AI Reasoning</th>
                  <th className="p-4 font-medium">Generated At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {recommendations.map((rec, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="p-4 font-bold text-white">{rec.ticker}</td>
                    <td className="p-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-black tracking-wider flex items-center w-max gap-1 ${
                        rec.action === 'BUY' ? 'bg-teal-500/20 text-teal-400' : 
                        rec.action === 'SELL' ? 'bg-red-500/20 text-red-400' : 
                        'bg-yellow-500/20 text-yellow-500'
                      }`}>
                        {rec.action === 'BUY' && <TrendingUp className="w-3 h-3" />}
                        {rec.action === 'SELL' && <TrendingDown className="w-3 h-3" />}
                        {rec.action === 'HOLD' && <Minus className="w-3 h-3" />}
                        {rec.action}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-gray-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${rec.confidence_score > 70 ? 'bg-teal-500' : rec.confidence_score > 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                            style={{ width: `${rec.confidence_score}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{Number(rec.confidence_score).toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="p-4 text-sm text-gray-300 max-w-md truncate" title={rec.reasoning_text}>
                      {rec.reasoning_text}
                    </td>
                    <td className="p-4 text-xs text-gray-500">
                      {rec.created_at}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
