import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { lmsApi } from '../../lib/lms';
import { FileText, ClipboardList, CheckCircle, Clock, Calendar, PlusCircle } from 'lucide-react';
import { useAuth } from '../../lib/AuthContext';

export default function LeaveDashboard() {
  const { hasPermission } = useAuth();
  const [selectedSession, setSelectedSession] = React.useState(2023);
  
  // Fetch sessions from DB
  const { data: sessionsRes } = useQuery({
    queryKey: ['academicSessions'],
    queryFn: lmsApi.getSessions,
  });

  // Try fetching current leave balance
  const { data: balanceRes } = useQuery({
    queryKey: ['leaveBalance', selectedSession],
    queryFn: () => lmsApi.getLeaveBalance(selectedSession),
    retry: false
  });

  const { data: myLeavesRes } = useQuery({
    queryKey: ['myLeaves'],
    queryFn: lmsApi.getMyLeaves,
  });

  const { data: pendingRes } = useQuery({
    queryKey: ['pendingLeaves'],
    queryFn: lmsApi.getPendingLeaves,
    enabled: hasPermission('leave.create') || hasPermission('leave.approve') // Any faculty can be a substitute
  });

  const balance = balanceRes?.data;
  const myLeaves = myLeavesRes?.data || [];
  const pendingLeaves = pendingRes?.data || [];

  const pendingCount = pendingLeaves.length;
  const approvedLeavesCount = myLeaves.filter((l: any) => l.principal_approval === 1).length;
  const pendingMyLeavesCount = myLeaves.filter((l: any) => l.principal_approval === 0 && l.hod_approval !== 2).length;

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

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-800">Leave Dashboard</h1>
            <select 
              value={selectedSession} 
              onChange={(e) => setSelectedSession(Number(e.target.value))}
              className="border border-slate-300 rounded-lg px-2 py-1 text-sm font-medium text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
          <p className="text-slate-600 mt-1">Overview of your leaves, balances, and pending actions.</p>
        </div>
        <Link to="/dashboard/staff/leave/my-leaves" className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm">
          <PlusCircle size={20} />
          Apply for Leave
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <CheckCircle size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Approved Leaves</p>
            <h3 className="text-2xl font-bold text-slate-800">{approvedLeavesCount}</h3>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
            <Clock size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Pending My Leaves</p>
            <h3 className="text-2xl font-bold text-slate-800">{pendingMyLeavesCount}</h3>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4 relative overflow-hidden transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
            <ClipboardList size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Action Required</p>
            <h3 className="text-2xl font-bold text-slate-800">{pendingCount}</h3>
          </div>
          {pendingCount > 0 && (
            <div className="absolute top-0 right-0 w-1.5 h-full bg-purple-500" />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Leave Requests */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <FileText size={20} className="text-blue-500" />
              My Recent Leaves
            </h2>
            <Link to="/dashboard/staff/leave/my-leaves" className="text-sm font-medium text-blue-600 hover:text-blue-700">View All</Link>
          </div>
          <div className="p-0 overflow-y-auto max-h-[400px]">
            {myLeaves.length === 0 ? (
              <div className="p-10 text-center text-slate-500">
                <div className="mx-auto w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-3">
                  <FileText className="text-slate-300" size={32} />
                </div>
                You haven't applied for any leaves recently.
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {myLeaves.slice(0, 5).map((leave: any) => (
                  <li key={leave.apply_id} className="p-5 hover:bg-slate-50/80 transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-semibold text-slate-700">{leave.leave_type} Leave</span>
                      <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                        {leave.days} Days
                      </span>
                    </div>
                    <div className="text-sm text-slate-500 mb-3 flex items-center gap-1.5">
                      <Calendar size={14} className="text-slate-400" />
                      {new Date(leave.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} - {new Date(leave.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </div>
                    <div className="flex gap-2 text-xs">
                      <span className={`px-2.5 py-1 rounded-md font-medium ${leave.hod_approval === 1 ? 'bg-green-50 text-green-700 border border-green-100' : leave.hod_approval === 2 ? 'bg-red-50 text-red-700 border border-red-100' : 'bg-amber-50 text-amber-700 border border-amber-100'}`}>
                        HOD: {leave.hod_approval === 0 ? 'Pending' : leave.hod_approval === 1 ? 'Approved' : 'Rejected'}
                      </span>
                      <span className={`px-2.5 py-1 rounded-md font-medium ${leave.principal_approval === 1 ? 'bg-green-50 text-green-700 border border-green-100' : leave.principal_approval === 2 ? 'bg-red-50 text-red-700 border border-red-100' : 'bg-amber-50 text-amber-700 border border-amber-100'}`}>
                        Principal: {leave.principal_approval === 0 ? 'Pending' : leave.principal_approval === 1 ? 'Approved' : 'Rejected'}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Pending Actions */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
            <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <ClipboardList size={20} className="text-purple-500" />
              Approvals Needing Attention
            </h2>
            <Link to="/dashboard/staff/leave/pending" className="text-sm font-medium text-blue-600 hover:text-blue-700">View All</Link>
          </div>
          <div className="p-0 overflow-y-auto max-h-[400px]">
            {pendingLeaves.length === 0 ? (
              <div className="p-10 text-center text-slate-500">
                <div className="mx-auto w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-3">
                  <CheckCircle className="text-slate-300" size={32} />
                </div>
                You have no pending leave approvals. You're all caught up!
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {pendingLeaves.slice(0, 5).map((leave: any) => (
                  <li key={leave.apply_id} className="p-5 hover:bg-slate-50/80 transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex flex-col">
                        <span className="font-semibold text-slate-700">{leave.faculty_name || 'Unknown Faculty'}</span>
                        <span className="text-xs text-slate-500">{leave.faculty_computer_code}</span>
                      </div>
                      <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${leave.required_action === 'WAITING_ON_SUBSTITUTE' ? 'bg-orange-100 text-orange-700' : leave.required_action === 'SUBSTITUTE' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>
                        {leave.required_action === 'SUBSTITUTE' ? 'Substitute Approval Needed' : leave.required_action === 'WAITING_ON_SUBSTITUTE' ? 'Awaiting Substitute' : 'Awaiting Your Approval'}
                      </span>
                    </div>
                    <div className="text-sm text-slate-600 mb-1">
                      <span className="font-medium text-slate-700">{leave.leave_type} Leave</span> • {leave.days} Days
                    </div>
                    <div className="text-xs text-slate-500 flex items-center gap-1.5">
                      <Calendar size={13} className="text-slate-400" />
                      {new Date(leave.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} to {new Date(leave.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
