import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navigate } from 'react-router-dom';
import { api } from '../../../lib/api';
import { useAuth } from '../../../lib/AuthContext';
import {
  Calendar, Search, Loader2, Award, CheckCircle, AlertCircle, FileText, Filter
} from 'lucide-react';

export default function Registrations() {
  const { role } = useAuth();
  const queryClient = useQueryClient();

  if (role !== 'HOD') {
    return <Navigate to="/unauthorized" replace />;
  }

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  // Load dropdown lists of events
  const { data: events = [] } = useQuery({
    queryKey: ['events-dropdown-list'],
    queryFn: async () => {
      const res = await api.get('/events/');
      return res.data?.data || [];
    }
  });

  // Load registrations
  const { data: registrations = [], isLoading } = useQuery({
    queryKey: ['registrations-all', selectedEventId, selectedStatus],
    queryFn: async () => {
      let url = '/events/registrations/all';
      const params = [];
      if (selectedEventId) params.push(`event_id=${selectedEventId}`);
      if (selectedStatus) params.push(`status=${selectedStatus}`);
      if (params.length > 0) url += `?${params.join('&')}`;
      
      const res = await api.get(url);
      return res.data?.data || [];
    }
  });

  const issueCertMutation = useMutation({
    mutationFn: async (regId: number) => {
      const res = await api.post(`/events/certificates/issue/${regId}`);
      return res.data;
    },
    onSuccess: (data) => {
      setToast({ message: `Certificate successfully issued! Code: ${data.data?.certificate_code}`, type: 'success' });
      queryClient.invalidateQueries({ queryKey: ['registrations-all'] });
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || 'Failed to issue certificate.', type: 'error' });
    }
  });

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Award className="text-blue-600" /> Event Registrations
        </h1>
        <p className="text-sm text-slate-500">Track user signups, check fee receipts, and award certificate codes to attendees</p>
      </div>

      {toast && (
        <div className={`p-4 rounded-lg flex items-center gap-3 border ${
          toast.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <CheckCircle size={20} />
          <p className="text-sm font-medium">{toast.message}</p>
          <button onClick={() => setToast(null)} className="ml-auto text-xs font-bold uppercase hover:underline">Dismiss</button>
        </div>
      )}

      {/* Filters Toolbar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 bg-white rounded-lg p-4 shadow-sm border border-slate-200 gap-4 items-center">
        <div>
          <label className="block text-xs font-bold text-slate-400 uppercase mb-1">Filter by Event</label>
          <select
            value={selectedEventId}
            onChange={(e) => setSelectedEventId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Events</option>
            {events.map((e: any) => (
              <option key={e.id} value={e.id}>{e.title}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-400 uppercase mb-1">Filter by Status</label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="Confirmed">Confirmed (Approved)</option>
            <option value="Pending">Pending Payment</option>
            <option value="Cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Registrations List */}
      <div className="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : registrations.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <Calendar className="w-12 h-12 mx-auto text-slate-300" />
            <p className="font-semibold text-lg">No registrations found</p>
            <p className="text-sm text-slate-400">Signups will display here as students and faculty register.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase">
                  <th className="px-6 py-4">Participant</th>
                  <th className="px-6 py-4">Event Details</th>
                  <th className="px-6 py-4">Registration Date</th>
                  <th className="px-6 py-4">Fee Details</th>
                  <th className="px-6 py-4">Status & Attendance</th>
                  <th className="px-6 py-4 text-center">Certificate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                {registrations.map((r: any) => (
                  <tr key={r.id} className="hover:bg-slate-50/50 transition">
                    <td className="px-6 py-4">
                      <p className="font-bold text-slate-900">{r.user_name}</p>
                      <p className="text-xs text-slate-500">{r.user_role} • {r.user_computer_code}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-slate-800">{r.event_title}</p>
                      <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 text-xxs font-bold uppercase tracking-wider">{r.event_type}</span>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      {new Date(r.registered_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="px-6 py-4 text-xs space-y-1">
                      {r.payment_status === 'Free' ? (
                        <span className="text-slate-400">Free Event</span>
                      ) : (
                        <>
                          <p className="font-bold text-slate-800">₹{r.payment_amount}</p>
                          <span className={`px-1.5 py-0.5 rounded text-xxs font-bold ${
                            r.payment_status === 'Success' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {r.payment_status}
                          </span>
                        </>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs space-y-2">
                      <div>
                        <span className={`px-2 py-0.5 rounded-full font-bold ${
                          r.status === 'Confirmed' ? 'bg-green-100 text-green-800 border border-green-200' :
                          r.status === 'Cancelled' ? 'bg-red-100 text-red-800 border border-red-200' :
                          'bg-yellow-100 text-yellow-800 border border-yellow-200'
                        }`}>
                          {r.status}
                        </span>
                      </div>
                      {r.status === 'Confirmed' && (
                        <div>
                          <span className={`px-2 py-0.5 rounded-full font-semibold ${
                            r.attended === 1 ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-500'
                          }`}>
                            {r.attended === 1 ? '✓ Attended' : 'Absent'}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-center items-center">
                        {r.has_certificate ? (
                          <div className="text-center">
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-bold rounded flex items-center gap-1 border border-green-200">
                              <Award size={14} /> Issued
                            </span>
                            <span className="text-slate-400 font-mono text-[10px] mt-0.5 block">{r.certificate_code}</span>
                          </div>
                        ) : (
                          <button
                            disabled={r.status !== 'Confirmed' || r.attended !== 1 || issueCertMutation.isPending}
                            onClick={() => issueCertMutation.mutate(r.id)}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 disabled:text-slate-400 text-white font-semibold rounded text-xs transition flex items-center gap-1 shadow-sm"
                          >
                            <Award size={14} /> Issue
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
