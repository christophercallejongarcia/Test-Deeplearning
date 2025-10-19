'use client';

import { ExpenseStats } from '@/lib/types';
import { formatCurrency } from '@/lib/utils';
import { CATEGORY_ICONS } from '@/lib/constants';
import CategoryChart from './CategoryChart';
import CloudExportButton from './CloudExportButton';

interface DashboardProps {
  stats: ExpenseStats;
  expenseCount: number;
}

export default function Dashboard({ stats, expenseCount }: DashboardProps) {
  return (
    <div className="space-y-6">
      {/* Cloud Export Button */}
      <div className="flex justify-end">
        <CloudExportButton />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Spending */}
        <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium opacity-90">Total Spending</h3>
            <svg className="w-8 h-8 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-3xl font-bold">{formatCurrency(stats.total)}</p>
          <p className="text-sm opacity-80 mt-1">{expenseCount} expense{expenseCount !== 1 ? 's' : ''}</p>
        </div>

        {/* Monthly Spending */}
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium opacity-90">This Month</h3>
            <svg className="w-8 h-8 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-3xl font-bold">{formatCurrency(stats.monthlyTotal)}</p>
          <p className="text-sm opacity-80 mt-1">Current month</p>
        </div>

        {/* Weekly Spending */}
        <div className="bg-gradient-to-br from-pink-500 to-pink-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium opacity-90">This Week</h3>
            <svg className="w-8 h-8 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <p className="text-3xl font-bold">{formatCurrency(stats.weeklyTotal)}</p>
          <p className="text-sm opacity-80 mt-1">Last 7 days</p>
        </div>

        {/* Average per Day */}
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium opacity-90">Daily Average</h3>
            <svg className="w-8 h-8 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-3xl font-bold">{formatCurrency(stats.averagePerDay)}</p>
          <p className="text-sm opacity-80 mt-1">Last 30 days</p>
        </div>
      </div>

      {/* Top Category and Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Category */}
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Category</h3>
          {stats.topCategory ? (
            <div className="text-center">
              <div className="text-6xl mb-3">{CATEGORY_ICONS[stats.topCategory]}</div>
              <p className="text-2xl font-bold text-gray-900 mb-1">{stats.topCategory}</p>
              <p className="text-3xl font-bold text-indigo-600">
                {formatCurrency(stats.categoryBreakdown[stats.topCategory])}
              </p>
              <p className="text-sm text-gray-600 mt-2">
                {((stats.categoryBreakdown[stats.topCategory] / stats.total) * 100).toFixed(1)}% of total
              </p>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No data available</p>
            </div>
          )}
        </div>

        {/* Category Breakdown Chart */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Spending by Category</h3>
          <CategoryChart categoryBreakdown={stats.categoryBreakdown} total={stats.total} />
        </div>
      </div>

      {/* Insights */}
      {expenseCount > 0 && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Quick Insights
          </h3>
          <div className="space-y-2 text-sm text-gray-700">
            {stats.monthlyTotal > stats.total * 0.7 && (
              <p>• You&apos;ve spent {((stats.monthlyTotal / stats.total) * 100).toFixed(0)}% of your total this month.</p>
            )}
            {stats.weeklyTotal > stats.monthlyTotal * 0.5 && stats.monthlyTotal > 0 && (
              <p>• Your weekly spending is high - {((stats.weeklyTotal / stats.monthlyTotal) * 100).toFixed(0)}% of this month&apos;s total.</p>
            )}
            {stats.topCategory && (
              <p>• Your highest spending category is {stats.topCategory}.</p>
            )}
            {stats.averagePerDay > 0 && (
              <p>• You&apos;re averaging {formatCurrency(stats.averagePerDay)} per day over the last 30 days.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
