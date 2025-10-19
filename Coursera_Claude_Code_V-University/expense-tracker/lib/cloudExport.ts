import { Expense } from './types';
import { ExportTemplateId, exportWithTemplate } from './exportTemplates';

export type CloudService = 'email' | 'google-sheets' | 'dropbox' | 'onedrive' | 'google-drive';
export type ExportStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type ScheduleFrequency = 'daily' | 'weekly' | 'monthly' | 'custom';

export interface ExportHistory {
  id: string;
  templateId: ExportTemplateId;
  recordCount: number;
  exportedAt: Date;
  service?: CloudService;
  sharedWith?: string[];
  downloadUrl?: string;
  status: ExportStatus;
}

export interface ScheduledExport {
  id: string;
  templateId: ExportTemplateId;
  frequency: ScheduleFrequency;
  nextExport: Date;
  destination: CloudService | 'email';
  emailRecipient?: string;
  enabled: boolean;
}

// LocalStorage keys
const EXPORT_HISTORY_KEY = 'expense-export-history';
const SCHEDULED_EXPORTS_KEY = 'expense-scheduled-exports';
const CLOUD_CONNECTIONS_KEY = 'expense-cloud-connections';

/**
 * Mock cloud service connection status
 */
export interface CloudConnection {
  service: CloudService;
  connected: boolean;
  email?: string;
  lastSync?: Date;
}

/**
 * Get export history from localStorage
 */
export function getExportHistory(): ExportHistory[] {
  if (typeof window === 'undefined') return [];
  const stored = localStorage.getItem(EXPORT_HISTORY_KEY);
  if (!stored) return [];
  return JSON.parse(stored, (key, value) => {
    if (key === 'exportedAt') return new Date(value);
    return value;
  });
}

/**
 * Add export to history
 */
export function addToExportHistory(export_: Omit<ExportHistory, 'id' | 'exportedAt'>): ExportHistory {
  const newExport: ExportHistory = {
    ...export_,
    id: `exp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    exportedAt: new Date(),
  };

  const history = getExportHistory();
  history.unshift(newExport);

  // Keep only last 50 exports
  const trimmed = history.slice(0, 50);
  localStorage.setItem(EXPORT_HISTORY_KEY, JSON.stringify(trimmed));

  return newExport;
}

/**
 * Get scheduled exports
 */
export function getScheduledExports(): ScheduledExport[] {
  if (typeof window === 'undefined') return [];
  const stored = localStorage.getItem(SCHEDULED_EXPORTS_KEY);
  if (!stored) return [];
  return JSON.parse(stored, (key, value) => {
    if (key === 'nextExport') return new Date(value);
    return value;
  });
}

/**
 * Add or update scheduled export
 */
export function saveScheduledExport(schedule: Omit<ScheduledExport, 'id'> | ScheduledExport): ScheduledExport {
  const schedules = getScheduledExports();

  const newSchedule: ScheduledExport = 'id' in schedule
    ? schedule
    : {
        ...schedule,
        id: `sch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      };

  const index = schedules.findIndex(s => s.id === newSchedule.id);
  if (index >= 0) {
    schedules[index] = newSchedule;
  } else {
    schedules.push(newSchedule);
  }

  localStorage.setItem(SCHEDULED_EXPORTS_KEY, JSON.stringify(schedules));
  return newSchedule;
}

/**
 * Delete scheduled export
 */
export function deleteScheduledExport(id: string): void {
  const schedules = getScheduledExports().filter(s => s.id !== id);
  localStorage.setItem(SCHEDULED_EXPORTS_KEY, JSON.stringify(schedules));
}

/**
 * Get cloud connection status
 */
export function getCloudConnections(): CloudConnection[] {
  if (typeof window === 'undefined') return [];
  const stored = localStorage.getItem(CLOUD_CONNECTIONS_KEY);
  if (stored) {
    return JSON.parse(stored, (key, value) => {
      if (key === 'lastSync') return value ? new Date(value) : undefined;
      return value;
    });
  }

  // Default mock connections
  return [
    { service: 'email', connected: false },
    { service: 'google-sheets', connected: false },
    { service: 'dropbox', connected: false },
    { service: 'onedrive', connected: false },
    { service: 'google-drive', connected: false },
  ];
}

/**
 * Update cloud connection status
 */
export function updateCloudConnection(service: CloudService, connected: boolean, email?: string): void {
  const connections = getCloudConnections();
  const index = connections.findIndex(c => c.service === service);

  if (index >= 0) {
    connections[index] = {
      ...connections[index],
      connected,
      email,
      lastSync: connected ? new Date() : undefined,
    };
  } else {
    connections.push({ service, connected, email, lastSync: connected ? new Date() : undefined });
  }

  localStorage.setItem(CLOUD_CONNECTIONS_KEY, JSON.stringify(connections));
}

/**
 * Mock export to cloud service
 */
export async function exportToCloudService(
  expenses: Expense[],
  service: CloudService,
  templateId: ExportTemplateId,
  options?: { email?: string; folder?: string }
): Promise<ExportHistory> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1500));

  const data = exportWithTemplate(expenses, templateId);

  // Create download blob
  const blob = new Blob([data], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);

  // Add to history
  const exportRecord = addToExportHistory({
    templateId,
    recordCount: expenses.length,
    service,
    sharedWith: options?.email ? [options.email] : undefined,
    downloadUrl: url,
    status: 'completed',
  });

  return exportRecord;
}

/**
 * Mock email export
 */
export async function sendEmailExport(
  expenses: Expense[],
  templateId: ExportTemplateId,
  recipient: string,
  subject?: string
): Promise<ExportHistory> {
  await new Promise(resolve => setTimeout(resolve, 1000));

  const exportRecord = addToExportHistory({
    templateId,
    recordCount: expenses.length,
    service: 'email',
    sharedWith: [recipient],
    status: 'completed',
  });

  // Mock success notification
  console.log(`📧 Email sent to ${recipient} with subject: ${subject || 'Expense Export'}`);

  return exportRecord;
}

/**
 * Calculate next export date based on frequency
 */
export function calculateNextExportDate(frequency: ScheduleFrequency, from: Date = new Date()): Date {
  const next = new Date(from);

  switch (frequency) {
    case 'daily':
      next.setDate(next.getDate() + 1);
      next.setHours(9, 0, 0, 0); // 9 AM
      break;
    case 'weekly':
      next.setDate(next.getDate() + 7);
      next.setHours(9, 0, 0, 0);
      break;
    case 'monthly':
      next.setMonth(next.getMonth() + 1);
      next.setDate(1); // First of month
      next.setHours(9, 0, 0, 0);
      break;
  }

  return next;
}

/**
 * Format next export time for display
 */
export function formatNextExportTime(date: Date): string {
  const now = new Date();
  const diff = date.getTime() - now.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

  if (days > 1) return `in ${days} days`;
  if (days === 1) return 'tomorrow';
  if (hours > 0) return `in ${hours} hours`;
  return 'soon';
}
