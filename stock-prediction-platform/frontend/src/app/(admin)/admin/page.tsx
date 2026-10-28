"use client";
import React from 'react';

export default function AdminPage() {
  return (
    <div className="max-w-7xl mx-auto py-12 text-white">
      <h1 className="text-3xl font-bold mb-8">Admin Control Center</h1>
      <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6">
         <h2 className="text-red-400 font-bold mb-2">Restricted Area</h2>
         <p className="text-gray-400">View celery task queues, force re-train XGBoost endpoints, and manage active users.</p>
      </div>
    </div>
  );
}
