import React from 'react';
import { TrendingUp } from 'lucide-react';
import RiskDisclaimer from '@/components/RiskDisclaimer';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex selection:bg-indigo-500/30 relative">
      
      {/* Left abstract split (visible on lg screens) */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-indigo-900/20 overflow-hidden flex-col justify-center p-12 lg:p-24 border-r border-white/5">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/30 via-[#0a0a0f] to-teal-500/20 z-0"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-[500px] bg-indigo-500/20 blur-[150px] rounded-full"></div>
        
        <div className="relative z-10 max-w-lg">
          <div className="h-16 w-16 rounded-2xl bg-indigo-600 flex items-center justify-center shadow-[0_0_40px_rgba(79,70,229,0.5)] mb-8">
            <TrendingUp className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-5xl font-extrabold tracking-tight mb-6">
            Predict the Future.<br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-teal-400">Trade with AI.</span>
          </h1>
          <p className="text-xl text-gray-400 leading-relaxed">
            Harness the power of LSTM and XGBoost models to run deeply structured technical analysis on global equties in real-time.
          </p>
        </div>
      </div>

      {/* Right side form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 z-10 relative">
        <div className="w-full max-w-md">
            {children}
        </div>
      </div>

      <RiskDisclaimer />
    </div>
  );
}
