'use client';

import { useState } from 'react';
import { useExpenses } from '@/hooks/useExpenses';
import ExpenseForm from '@/components/ExpenseForm';
import ExpenseList from '@/components/ExpenseList';
import CloudExportButton from '@/components/CloudExportButton';
import { Category } from '@/lib/types';

export default function ExpensesPage() {
  const { expenses, isLoading, addExpense, updateExpense, deleteExpense } = useExpenses();
  const [showForm, setShowForm] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const handleAddExpense = (
    amount: number,
    category: Category,
    description: string,
    date: string
  ) => {
    addExpense(amount, category, description, date);
    setShowForm(false);
    showSuccessToast('Expense added successfully!');
  };

  const handleUpdateExpense = (
    id: string,
    updates: { amount?: number; category?: Category; description?: string; date?: string }
  ) => {
    updateExpense(id, updates);
    showSuccessToast('Expense updated successfully!');
  };

  const handleDeleteExpense = (id: string) => {
    deleteExpense(id);
    showSuccessToast('Expense deleted successfully!');
  };

  const showSuccessToast = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading your expenses...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Expenses</h1>
          <p className="text-gray-600">
            {expenses.length === 0
              ? 'Start tracking your expenses'
              : `Manage your ${expenses.length} expense${expenses.length !== 1 ? 's' : ''}`}
          </p>
        </div>
        <div className="flex gap-3">
          <CloudExportButton />
          <button
            onClick={() => setShowForm(!showForm)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
          >
            {showForm ? (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Cancel
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Expense
              </>
            )}
          </button>
        </div>
      </div>

      {/* Add Expense Form */}
      {showForm && (
        <div className="mb-8 bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Add New Expense</h2>
          <ExpenseForm
            onSubmit={handleAddExpense}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {/* Expense List */}
      <ExpenseList
        expenses={expenses}
        onUpdate={handleUpdateExpense}
        onDelete={handleDeleteExpense}
      />

      {/* Success Toast */}
      {showToast && (
        <div className="fixed bottom-4 right-4 z-50 animate-slide-up">
          <div className="bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {toastMessage}
          </div>
        </div>
      )}
    </div>
  );
}
