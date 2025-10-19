'use client';

import { useState, useMemo } from 'react';
import { useExpenses } from '@/hooks/useExpenses';
import { EXPORT_TEMPLATES, ExportTemplateId, exportWithTemplate } from '@/lib/exportTemplates';
import {
  getExportHistory,
  getScheduledExports,
  getCloudConnections,
  saveScheduledExport,
  deleteScheduledExport,
  updateCloudConnection,
  exportToCloudService,
  sendEmailExport,
  calculateNextExportDate,
  formatNextExportTime,
  CloudService,
  ScheduleFrequency
} from '@/lib/cloudExport';
import {
  generateShareableLink,
  generateQRCode,
  copyToClipboard,
  formatExpirationDate,
  getPermissionDescription,
  SharePermission,
  ShareExpiration
} from '@/lib/shareUtils';

interface CloudExportHubProps {
  isOpen: boolean;
  onClose: () => void;
}

type Tab = 'export' | 'history' | 'schedule' | 'share';

export default function CloudExportHub({ isOpen, onClose }: CloudExportHubProps) {
  const { expenses } = useExpenses();
  const [activeTab, setActiveTab] = useState<Tab>('export');
  const [selectedTemplate, setSelectedTemplate] = useState<ExportTemplateId>('monthly-summary');
  const [selectedService, setSelectedService] = useState<CloudService | 'email'>('email');
  const [emailRecipient, setEmailRecipient] = useState('');
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  // Sharing state
  const [shareLink, setShareLink] = useState<string | null>(null);
  const [sharePermission, setSharePermission] = useState<SharePermission>('view');
  const [shareExpiration, setShareExpiration] = useState<ShareExpiration>('7d');
  const [showQR, setShowQR] = useState(false);

  // Schedule state
  const [scheduleFreq, setScheduleFreq] = useState<ScheduleFrequency>('weekly');
  const [schedules, setSchedules] = useState(getScheduledExports());

  // History and connections
  const exportHistory = useMemo(() => getExportHistory(), [exportSuccess]);
  const cloudConnections = useMemo(() => getCloudConnections(), []);

  if (!isOpen) return null;

  const handleExport = async () => {
    setIsExporting(true);
    setExportSuccess(false);

    try {
      if (selectedService === 'email' && emailRecipient) {
        await sendEmailExport(expenses, selectedTemplate, emailRecipient);
      } else if (selectedService !== 'email') {
        await exportToCloudService(expenses, selectedService, selectedTemplate, { email: emailRecipient });
      }

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleGenerateShareLink = () => {
    const link = generateShareableLink(sharePermission, shareExpiration);
    setShareLink(link.url);
    setShowQR(false);
  };

  const handleCopyLink = async () => {
    if (shareLink) {
      const success = await copyToClipboard(shareLink);
      if (success) {
        alert('✓ Link copied to clipboard!');
      }
    }
  };

  const handleAddSchedule = () => {
    const newSchedule = saveScheduledExport({
      templateId: selectedTemplate,
      frequency: scheduleFreq,
      nextExport: calculateNextExportDate(scheduleFreq),
      destination: selectedService,
      emailRecipient: selectedService === 'email' ? emailRecipient : undefined,
      enabled: true,
    });
    setSchedules([...schedules, newSchedule]);
  };

  const handleToggleConnection = (service: CloudService) => {
    const current = cloudConnections.find(c => c.service === service);
    updateCloudConnection(service, !current?.connected, 'user@example.com');
    window.location.reload(); // Reload to show updated status
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 text-white p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-bold mb-2">☁️ Cloud Export Hub</h2>
              <p className="text-blue-100">Export, share, and automate your expense data</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mt-4">
            {([
              { id: 'export', label: '📤 Export', icon: '📤' },
              { id: 'history', label: '📜 History', icon: '📜' },
              { id: 'schedule', label: '⏰ Schedule', icon: '⏰' },
              { id: 'share', label: '🔗 Share', icon: '🔗' },
            ] as const).map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 shadow-lg'
                    : 'bg-white bg-opacity-20 text-white hover:bg-opacity-30'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'export' && (
            <div className="space-y-6">
              {/* Template Selection */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Select Export Template</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {EXPORT_TEMPLATES.map(template => (
                    <button
                      key={template.id}
                      onClick={() => setSelectedTemplate(template.id)}
                      className={`p-4 rounded-lg border-2 transition-all text-left ${
                        selectedTemplate === template.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300'
                      }`}
                    >
                      <div className="text-3xl mb-2">{template.icon}</div>
                      <div className="font-semibold">{template.name}</div>
                      <div className="text-sm text-gray-600 mt-1">{template.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Cloud Service Selection */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Select Destination</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    { id: 'email', name: 'Email', icon: '📧', color: 'bg-red-50 border-red-300' },
                    { id: 'google-sheets', name: 'Google Sheets', icon: '📊', color: 'bg-green-50 border-green-300' },
                    { id: 'dropbox', name: 'Dropbox', icon: '📦', color: 'bg-blue-50 border-blue-300' },
                    { id: 'onedrive', name: 'OneDrive', icon: '☁️', color: 'bg-indigo-50 border-indigo-300' },
                    { id: 'google-drive', name: 'Google Drive', icon: '💾', color: 'bg-yellow-50 border-yellow-300' },
                  ].map(service => {
                    const connection = cloudConnections.find(c => c.service === service.id);
                    return (
                      <button
                        key={service.id}
                        onClick={() => setSelectedService(service.id as CloudService | 'email')}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          selectedService === service.id ? service.color : 'border-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-2xl">{service.icon}</span>
                            <span className="font-medium">{service.name}</span>
                          </div>
                          {service.id !== 'email' && connection && (
                            <span className={`text-xs px-2 py-1 rounded ${connection.connected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                              {connection.connected ? '✓' : '○'}
                            </span>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Email Input */}
              {selectedService === 'email' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Email Recipient</label>
                  <input
                    type="email"
                    value={emailRecipient}
                    onChange={(e) => setEmailRecipient(e.target.value)}
                    placeholder="recipient@example.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              )}

              {/* Export Button */}
              <button
                onClick={handleExport}
                disabled={isExporting || (selectedService === 'email' && !emailRecipient)}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isExporting ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Exporting...
                  </span>
                ) : exportSuccess ? (
                  '✓ Export Successful!'
                ) : (
                  `Export ${expenses.length} Expenses`
                )}
              </button>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Export History</h3>
              {exportHistory.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-6xl mb-4">📭</div>
                  <p>No exports yet. Start by exporting your first report!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {exportHistory.slice(0, 10).map(record => {
                    const template = EXPORT_TEMPLATES.find(t => t.id === record.templateId);
                    return (
                      <div key={record.id} className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-semibold flex items-center gap-2">
                              <span>{template?.icon}</span>
                              <span>{template?.name}</span>
                            </div>
                            <div className="text-sm text-gray-600 mt-1">
                              {record.recordCount} records • {new Date(record.exportedAt).toLocaleString()}
                            </div>
                            {record.service && (
                              <div className="text-xs text-blue-600 mt-1">
                                via {record.service}
                              </div>
                            )}
                          </div>
                          {record.downloadUrl && (
                            <a
                              href={record.downloadUrl}
                              download={`export-${record.id}.csv`}
                              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                            >
                              Download
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {activeTab === 'schedule' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-3">Schedule Automatic Exports</h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">💡</span>
                    <div className="text-sm text-blue-900">
                      <strong>Pro Tip:</strong> Set up recurring exports to automatically send reports to your email or cloud storage.
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Frequency</label>
                    <select
                      value={scheduleFreq}
                      onChange={(e) => setScheduleFreq(e.target.value as ScheduleFrequency)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="daily">Daily (9 AM)</option>
                      <option value="weekly">Weekly (Monday 9 AM)</option>
                      <option value="monthly">Monthly (1st of month)</option>
                    </select>
                  </div>

                  <button
                    onClick={handleAddSchedule}
                    className="w-full py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    + Add Schedule
                  </button>
                </div>
              </div>

              {/* Existing Schedules */}
              {schedules.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3">Active Schedules</h4>
                  <div className="space-y-3">
                    {schedules.map(schedule => {
                      const template = EXPORT_TEMPLATES.find(t => t.id === schedule.templateId);
                      return (
                        <div key={schedule.id} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="font-medium">{template?.name}</div>
                              <div className="text-sm text-gray-600">
                                {schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1)} → {schedule.destination}
                              </div>
                              <div className="text-xs text-blue-600 mt-1">
                                Next export: {formatNextExportTime(new Date(schedule.nextExport))}
                              </div>
                            </div>
                            <button
                              onClick={() => {
                                deleteScheduledExport(schedule.id);
                                setSchedules(schedules.filter(s => s.id !== schedule.id));
                              }}
                              className="text-red-600 hover:text-red-700 text-sm"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'share' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">Share Export Data</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Permission Level</label>
                  <select
                    value={sharePermission}
                    onChange={(e) => setSharePermission(e.target.value as SharePermission)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="view">View Only</option>
                    <option value="download">View & Download</option>
                    <option value="full">Full Access</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">{getPermissionDescription(sharePermission)}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Link Expiration</label>
                  <div className="grid grid-cols-4 gap-2">
                    {(['24h', '7d', '30d', 'never'] as ShareExpiration[]).map(exp => (
                      <button
                        key={exp}
                        onClick={() => setShareExpiration(exp)}
                        className={`px-4 py-2 rounded-lg border-2 transition-all ${
                          shareExpiration === exp
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-blue-300'
                        }`}
                      >
                        {exp === 'never' ? 'Never' : exp}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleGenerateShareLink}
                  className="w-full py-3 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg font-semibold hover:from-green-700 hover:to-teal-700"
                >
                  🔗 Generate Share Link
                </button>

                {shareLink && (
                  <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center gap-2 mb-3">
                      <input
                        type="text"
                        value={shareLink}
                        readOnly
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-white"
                      />
                      <button
                        onClick={handleCopyLink}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 whitespace-nowrap"
                      >
                        Copy
                      </button>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setShowQR(!showQR)}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        {showQR ? 'Hide' : 'Show'} QR Code
                      </button>
                    </div>

                    {showQR && (
                      <div className="mt-4 text-center">
                        <img
                          src={generateQRCode(shareLink)}
                          alt="QR Code"
                          className="mx-auto border border-gray-300 rounded-lg"
                        />
                        <p className="text-xs text-gray-500 mt-2">Scan with mobile device</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          <div className="flex justify-between items-center text-sm text-gray-600">
            <div>{expenses.length} expenses ready to export</div>
            <button onClick={onClose} className="text-blue-600 hover:text-blue-700 font-medium">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
