import { Expense } from './types';

export type ExportTemplateId = 'tax-report' | 'monthly-summary' | 'category-analysis' | 'business-report' | 'budget-review';

export interface ExportTemplate {
  id: ExportTemplateId;
  name: string;
  description: string;
  icon: string;
  category: 'tax' | 'personal' | 'business';
  format: (expenses: Expense[]) => string;
}

export const EXPORT_TEMPLATES: ExportTemplate[] = [
  {
    id: 'tax-report',
    name: 'Tax Report',
    description: 'IRS-compatible format with category totals and tax year metadata',
    icon: '📋',
    category: 'tax',
    format: (expenses: Expense[]) => {
      const year = new Date().getFullYear();
      const categoryTotals = expenses.reduce((acc, exp) => {
        acc[exp.category] = (acc[exp.category] || 0) + exp.amount;
        return acc;
      }, {} as Record<string, number>);

      let csv = `TAX REPORT - ${year}\n`;
      csv += `Generated: ${new Date().toISOString()}\n\n`;
      csv += 'Date,Category,Amount,Description,Tax Deductible\n';

      expenses.forEach(exp => {
        csv += `${exp.date},${exp.category},${exp.amount.toFixed(2)},"${exp.description.replace(/"/g, '""')}",Yes\n`;
      });

      csv += '\n\nCATEGORY TOTALS\n';
      Object.entries(categoryTotals).forEach(([cat, total]) => {
        csv += `${cat},${total.toFixed(2)}\n`;
      });

      return csv;
    }
  },
  {
    id: 'monthly-summary',
    name: 'Monthly Summary',
    description: 'Clean overview with daily averages and budget insights',
    icon: '📊',
    category: 'personal',
    format: (expenses: Expense[]) => {
      const total = expenses.reduce((sum, exp) => sum + exp.amount, 0);
      const avgPerDay = total / 30;

      let csv = `MONTHLY EXPENSE SUMMARY\n`;
      csv += `Period: ${new Date().toLocaleDateString()}\n`;
      csv += `Total Expenses: $${total.toFixed(2)}\n`;
      csv += `Daily Average: $${avgPerDay.toFixed(2)}\n\n`;
      csv += 'Date,Category,Amount,Description,% of Total\n';

      expenses.forEach(exp => {
        const pct = ((exp.amount / total) * 100).toFixed(1);
        csv += `${exp.date},${exp.category},${exp.amount.toFixed(2)},"${exp.description.replace(/"/g, '""')}",${pct}%\n`;
      });

      return csv;
    }
  },
  {
    id: 'category-analysis',
    name: 'Category Analysis',
    description: 'Pivot table showing spending patterns by category',
    icon: '📈',
    category: 'personal',
    format: (expenses: Expense[]) => {
      const byCategory = expenses.reduce((acc, exp) => {
        if (!acc[exp.category]) {
          acc[exp.category] = { count: 0, total: 0, items: [] };
        }
        acc[exp.category].count++;
        acc[exp.category].total += exp.amount;
        acc[exp.category].items.push(exp);
        return acc;
      }, {} as Record<string, { count: number; total: number; items: Expense[] }>);

      const total = expenses.reduce((sum, exp) => sum + exp.amount, 0);

      let csv = `CATEGORY ANALYSIS\n\n`;
      csv += 'Category,Count,Total,Average,% of Total,Trend\n';

      Object.entries(byCategory)
        .sort(([, a], [, b]) => b.total - a.total)
        .forEach(([cat, data]) => {
          const avg = data.total / data.count;
          const pct = ((data.total / total) * 100).toFixed(1);
          const trend = data.total > total / Object.keys(byCategory).length ? '↑' : '↓';
          csv += `${cat},${data.count},${data.total.toFixed(2)},${avg.toFixed(2)},${pct}%,${trend}\n`;
        });

      return csv;
    }
  },
  {
    id: 'business-report',
    name: 'Business Expense Report',
    description: 'Professional format for business accounting',
    icon: '💼',
    category: 'business',
    format: (expenses: Expense[]) => {
      let csv = `BUSINESS EXPENSE REPORT\n`;
      csv += `Report Date: ${new Date().toISOString().split('T')[0]}\n`;
      csv += `Company: Your Business Name\n\n`;
      csv += 'Date,Category,Amount,Description,Receipt,Reimbursable\n';

      expenses.forEach((exp, idx) => {
        csv += `${exp.date},${exp.category},${exp.amount.toFixed(2)},"${exp.description.replace(/"/g, '""')}",Receipt-${idx + 1},Yes\n`;
      });

      const total = expenses.reduce((sum, exp) => sum + exp.amount, 0);
      csv += `\nTOTAL REIMBURSABLE,$${total.toFixed(2)}\n`;

      return csv;
    }
  },
  {
    id: 'budget-review',
    name: 'Personal Budget Review',
    description: 'Compare actual spending vs budget goals',
    icon: '💰',
    category: 'personal',
    format: (expenses: Expense[]) => {
      const categoryBudgets = {
        Food: 500,
        Transportation: 200,
        Entertainment: 150,
        Shopping: 300,
        Housing: 1500,
        Healthcare: 200,
        Other: 150
      };

      const actual = expenses.reduce((acc, exp) => {
        acc[exp.category] = (acc[exp.category] || 0) + exp.amount;
        return acc;
      }, {} as Record<string, number>);

      let csv = `BUDGET REVIEW\n\n`;
      csv += 'Category,Budget,Actual,Difference,Status\n';

      Object.entries(categoryBudgets).forEach(([cat, budget]) => {
        const spent = actual[cat] || 0;
        const diff = budget - spent;
        const status = diff >= 0 ? 'Under Budget ✓' : 'Over Budget ⚠';
        csv += `${cat},$${budget.toFixed(2)},$${spent.toFixed(2)},$${Math.abs(diff).toFixed(2)},${status}\n`;
      });

      return csv;
    }
  }
];

export function getTemplate(id: ExportTemplateId): ExportTemplate | undefined {
  return EXPORT_TEMPLATES.find(t => t.id === id);
}

export function exportWithTemplate(expenses: Expense[], templateId: ExportTemplateId): string {
  const template = getTemplate(templateId);
  if (!template) {
    throw new Error(`Template ${templateId} not found`);
  }
  return template.format(expenses);
}
