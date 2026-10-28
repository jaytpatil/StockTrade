"use client";
import React from 'react';

export default function NewsPage() {
  return (
    <div className="max-w-5xl mx-auto py-12">
      <h1 className="text-3xl font-bold mb-8">News Sentiment Analysis</h1>
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
         <p className="text-gray-400 text-center py-10">NLP Pipeline scraping global financial news to assign positive/negative polarity scores.</p>
      </div>
    </div>
  );
}
