import React from 'react';
import Navbar from '@/components/layout/Navbar';
import Sidebar from '@/components/layout/Sidebar';
import RiskDisclaimer from '@/components/RiskDisclaimer';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex overflow-hidden selection:bg-indigo-500/30">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen overflow-hidden relative">
        {/* Ambient Blur */}
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-900/10 blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-teal-900/10 blur-[120px] pointer-events-none" />
        
        <Navbar />
        
        <main className="flex-1 overflow-y-auto p-4 md:p-8 pb-24 z-10">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
        
        <RiskDisclaimer />
      </div>
    </div>
  );
}
