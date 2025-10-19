'use client';

import { useState } from 'react';
import { useExpenses } from '@/hooks/useExpenses';
import CloudExportHub from './CloudExportHub';
import { getScheduledExports } from '@/lib/cloudExport';

export default function CloudExportButton() {
  const { expenses } = useExpenses();
  const [isHubOpen, setIsHubOpen] = useState(false);
  const scheduledCount = getScheduledExports().filter(s => s.enabled).length;

  return (
    <>
      <button
        onClick={() => setIsHubOpen(true)}
        className="relative inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:via-purple-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl font-medium group"
        title="Open Cloud Export Hub"
      >
        <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <span>Cloud Export</span>

        {/* Badge for scheduled exports or expense count */}
        {scheduledCount > 0 ? (
          <span className="absolute -top-1 -right-1 bg-green-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
            {scheduledCount}
          </span>
        ) : expenses.length > 0 ? (
          <span className="absolute -top-1 -right-1 bg-white text-blue-600 text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center shadow-md">
            {expenses.length}
          </span>
        ) : null}

        {/* Animated cloud icon overlay */}
        <div className="absolute -right-1 -bottom-1 opacity-20 group-hover:opacity-40 transition-opacity">
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19 18H6a4 4 0 01-4-4 4 4 0 014-4h.29a5.5 5.5 0 0110.84-1.37A4.5 4.5 0 0119 18z" />
          </svg>
        </div>
      </button>

      <CloudExportHub isOpen={isHubOpen} onClose={() => setIsHubOpen(false)} />
    </>
  );
}
