import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams, Navigate } from 'react-router-dom';
import { api } from '../../../lib/api';
import { useAuth } from '../../../lib/AuthContext';
import {
  FileSpreadsheet, Loader2, BarChart, Download, DollarSign, Users, CheckSquare, Calendar, Award
} from 'lucide-react';

export default function Reports() {
  const { role } = useAuth();
  const [searchParams] = useSearchParams();
  
  if (role !== 'HOD' && role !== 'Principal') {
    return <Navigate to="/unauthorized" replace />;
  }

  // Pre-select event if passed via query params (e.g. from manage list)
  const initialEventId = searchParams.get('event_id') || '';
  const [selectedEventId, setSelectedEventId] = useState<string>(initialEventId);

  // Load dropdown lists of events
  const { data: events = [] } = useQuery({
    queryKey: ['events-reports-dropdown'],
    queryFn: async () => {
      const res = await api.get('/events/');
      return res.data?.data || [];
    }
  });

  // Load summary metrics
  const { data: summary, isLoading } = useQuery({
    queryKey: ['events-reports-summary', selectedEventId],
    queryFn: async () => {
      let url = '/events/reports/summary';
      if (selectedEventId) url += `?event_id=${selectedEventId}`;
      const res = await api.get(url);
      return res.data?.data || null;
    }
  });

  const handleExport = async () => {
    try {
      let url = '/events/reports/export';
      if (selectedEventId) url += `?event_id=${selectedEventId}`;
      
      const res = await api.get(url, { responseType: 'blob' });
      const blob = new Blob([res.data], { type: 'text/csv' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `event_registrations_report_${selectedEventId || 'all'}.csv`;
      link.click();
    } catch (e) {
      alert('Failed to export report CSV');
    }
  };

  const handleExportPDF = () => {
    // Generate a simple print layout representation of the summary report
    window.print();
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <BarChart className="text-blue-600" /> Event & Seminar Reports
          </h1>
          <p className="text-sm text-slate-500">Analyze registrations, attendances, and financial revenues generated from events</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg text-sm shadow transition flex items-center gap-2"
          >
            <Download size={16} /> Export Excel (CSV)
          </button>
          
          <button
            onClick={handleExportPDF}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-lg text-sm shadow transition flex items-center gap-2"
          >
            <FileSpreadsheet size={16} /> Export PDF (Print)
          </button>
        </div>
      </div>

      {/* Filters Toolbar */}
      <div className="bg-white rounded-lg p-4 shadow-sm border border-slate-200 flex flex-col sm:flex-row gap-4 items-center">
        <div className="w-full sm:max-w-md">
          <label className="block text-xs font-bold text-slate-400 uppercase mb-1">Select Event to Filter</label>
          <select
            value={selectedEventId}
            onChange={(e) => setSelectedEventId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Events (Summary)</option>
            {events.map((e: any) => (
              <option key={e.id} value={e.id}>{e.title}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Metrics Dashboard */}
      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : !summary ? (
        <p className="text-center text-slate-500">No report data found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Total Registrations */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
              <Users className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Total Signups</p>
              <h3 className="text-2xl font-bold text-slate-900">{summary.total_registrations}</h3>
            </div>
          </div>

          {/* Paid Registrations */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-green-50 text-green-600 rounded-lg">
              <Award className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Paid & Confirmed</p>
              <h3 className="text-2xl font-bold text-slate-900">{summary.paid_registrations}</h3>
            </div>
          </div>

          {/* Revenue */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
              <DollarSign className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Total Revenue</p>
              <h3 className="text-2xl font-bold text-slate-900">₹{parseFloat(summary.total_revenue).toFixed(2)}</h3>
            </div>
          </div>

          {/* Pending Signups */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-yellow-50 text-yellow-600 rounded-lg">
              <Calendar className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Pending Payments</p>
              <h3 className="text-2xl font-bold text-slate-900">{summary.pending_registrations}</h3>
            </div>
          </div>

          {/* Cancelled signups */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-red-50 text-red-600 rounded-lg">
              <Calendar className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Cancelled / Failed</p>
              <h3 className="text-2xl font-bold text-slate-900">{summary.cancelled_registrations}</h3>
            </div>
          </div>

          {/* Attendance */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-teal-50 text-teal-600 rounded-lg">
              <CheckSquare className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Attended count</p>
              <h3 className="text-2xl font-bold text-slate-900">{summary.attendance_count}</h3>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
