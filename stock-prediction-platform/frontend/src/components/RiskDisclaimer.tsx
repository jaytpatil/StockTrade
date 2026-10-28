import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function RiskDisclaimer() {
  return (
    <div className="fixed bottom-0 left-0 w-full bg-black/80 backdrop-blur-md border-t border-red-500/20 text-xs sm:text-sm text-gray-400 p-3 sm:px-6 z-50 flex items-center justify-center gap-3 shadow-[0_-5px_20px_rgba(255,0,0,0.1)]">
      <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
      <p className="max-w-6xl text-center">
        <strong className="text-red-400">DISCLAIMER:</strong> The information, predictions, and signals (BUY/SELL/HOLD) provided on this platform are strictly for educational and informational purposes and do not constitute financial advice. Algorithmic predictions are inherently uncertain. You should consult a licensed financial advisor before investing. We hold no liability for financial losses.
      </p>
    </div>
  );
}
