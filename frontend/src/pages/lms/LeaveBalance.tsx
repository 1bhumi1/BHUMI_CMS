import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { lmsApi } from '../../lib/lms';
import { Loader2 } from 'lucide-react';

export default function LeaveBalance() {
  const [selectedSession, setSelectedSession] = React.useState(2023);

  // Fetch sessions from DB
  const { data: sessionsRes } = useQuery({
    queryKey: ['academicSessions'],
    queryFn: lmsApi.getSessions,
  });

  const { data: balanceRes, isLoading, isError } = useQuery({
    queryKey: ['leaveBalance', selectedSession],
    queryFn: () => lmsApi.getLeaveBalance(selectedSession),
  });

  const balance = balanceRes?.data;
  const sessions = sessionsRes?.data || [];

  // Automatically select the active session if not already set manually
  React.useEffect(() => {
    if (sessions.length > 0 && selectedSession === 2023) {
      const activeSession = sessions.find((s: any) => s.is_active);
      if (activeSession) {
        setSelectedSession(Number(activeSession.session_name.split('-')[0]));
      }
    }
  }, [sessions, selectedSession]);

  if (isLoading) return <div className="p-6 flex items-center justify-center"><Loader2 className="animate-spin w-6 h-6 text-indigo-600" /></div>;
  if (isError || !balance) return <div className="p-6 text-red-500">Failed to load leave balance. Please try again.</div>;

  const leaveTypes = [
    { key: 'cl', name: 'Casual Leave (CL)' },
    { key: 'dl', name: 'Duty Leave (DL)' },
    { key: 'el', name: 'Earned Leave (EL)' },
    { key: 'ol', name: 'Optional Leave (OL)' },
    { key: 'lwp', name: 'Leave Without Pay (LWP)' },
    { key: 'sl', name: 'Special Leave (SL)' },
    { key: 'ab', name: 'Absent (AB)' },
    { key: 'ml', name: 'Medical Leave (ML)' },
    { key: 'sdl', name: 'Special Duty Leave (SDL)' },
    { key: 'vl', name: 'Vacation Leave (VL)' },
    { key: 'od', name: 'On Duty (OD)' },
  ];

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Leave Balance</h1>
        <p className="text-slate-600 mt-1">Detailed breakdown of your leave allowances for the current academic session.</p>
      </div>
      
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-800">Session:</h2>
            <select 
              value={selectedSession} 
              onChange={(e) => setSelectedSession(Number(e.target.value))}
              className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {sessions.length > 0 ? (
                sessions.map((s: any) => (
                  <option key={s.id} value={Number(s.session_name.split('-')[0])}>
                    {s.session_name}
                  </option>
                ))
              ) : (
                <option value={2023}>2023-24</option>
              )}
            </select>
          </div>
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium whitespace-nowrap">Overtime (OT): {balance.ot} hrs</span>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-0 border-t border-slate-200">
          {leaveTypes.map((type, idx) => (
            <div 
              key={type.key} 
              className={`p-5 flex flex-col ${
                idx % 3 !== 2 ? 'md:border-r' : ''
              } ${
                idx < leaveTypes.length - 3 ? 'border-b' : ''
              } border-slate-100 hover:bg-slate-50/50 transition-colors`}
            >
              <span className="text-sm font-medium text-slate-500 mb-1">{type.name}</span>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-slate-800">{(balance as any)[type.key] || 0}</span>
                <span className="text-sm text-slate-400 mb-1">days left</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
