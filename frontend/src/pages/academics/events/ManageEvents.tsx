import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { api } from '../../../lib/api';
import { useAuth } from '../../../lib/AuthContext';
import {
  Calendar, Search, Loader2, Play, Trash2, Edit, CheckSquare, BarChart, Plus,
  AlertCircle, X, Check, Users
} from 'lucide-react';

export default function ManageEvents() {
  const { role } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  if (role !== 'HOD') {
    return <Navigate to="/unauthorized" replace />;
  }

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Attendance marking modal states
  const [attendanceEventId, setAttendanceEventId] = useState<number | null>(null);
  const [attendanceEventTitle, setAttendanceEventTitle] = useState('');
  const [attendanceList, setAttendanceList] = useState<{ registration_id: number; user_name: string; computer_code: number; role: string; attended: number }[]>([]);
  const [loadingAttendance, setLoadingAttendance] = useState(false);

  // Fetch events
  const { data: eventsRes = [], isLoading } = useQuery({
    queryKey: ['events-list-admin'],
    queryFn: async () => {
      const res = await api.get('/events/');
      return res.data?.data || [];
    }
  });

  const publishMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await api.patch(`/events/${id}/publish`);
      return res.data;
    },
    onSuccess: () => {
      setToast({ message: 'Event successfully published! Eligible users notified.', type: 'success' });
      queryClient.invalidateQueries({ queryKey: ['events-list-admin'] });
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || 'Failed to publish event.', type: 'error' });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await api.delete(`/events/${id}`);
      return res.data;
    },
    onSuccess: () => {
      setToast({ message: 'Event deleted successfully.', type: 'success' });
      queryClient.invalidateQueries({ queryKey: ['events-list-admin'] });
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || 'Failed to delete event.', type: 'error' });
    }
  });

  const loadAttendance = async (eventId: number, title: string) => {
    setAttendanceEventId(eventId);
    setAttendanceEventTitle(title);
    setLoadingAttendance(true);
    try {
      const res = await api.get(`/events/registrations/all?event_id=${eventId}&status=Confirmed`);
      const list = (res.data?.data || []).map((r: any) => ({
        registration_id: r.id,
        user_name: r.user_name,
        computer_code: r.user_computer_code,
        role: r.user_role,
        attended: r.attended
      }));
      setAttendanceList(list);
    } catch (e) {
      setToast({ message: 'Failed to load registrations', type: 'error' });
    } finally {
      setLoadingAttendance(false);
    }
  };

  const saveAttendanceMutation = useMutation({
    mutationFn: async (payload: { registration_id: number; attended: number }[]) => {
      const res = await api.post('/events/attendance/mark', payload);
      return res.data;
    },
    onSuccess: () => {
      setToast({ message: 'Attendance updated successfully!', type: 'success' });
      setAttendanceEventId(null);
    },
    onError: () => {
      setToast({ message: 'Failed to save attendance.', type: 'error' });
    }
  });

  const filteredEvents = eventsRes.filter((e: any) =>
    e.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.venue.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.event_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Calendar className="text-blue-600" /> Manage Events & Workshops
          </h1>
          <p className="text-sm text-slate-500">Create, publish, track registrations, and mark attendance for campus events</p>
        </div>
        <Link
          to="/dashboard/staff/academics/event-management/create"
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-sm shadow transition flex items-center gap-2"
        >
          <Plus size={16} /> Create Event
        </Link>
      </div>

      {toast && (
        <div className={`p-4 rounded-lg flex items-center gap-3 border ${
          toast.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <AlertCircle size={20} />
          <p className="text-sm font-medium">{toast.message}</p>
          <button onClick={() => setToast(null)} className="ml-auto text-xs font-bold uppercase hover:underline">Dismiss</button>
        </div>
      )}

      {/* Toolbar */}
      <div className="flex bg-white rounded-lg p-4 shadow-sm border border-slate-200 gap-4 items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 text-slate-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search events by title, venue, or type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Main List */}
      <div className="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <Calendar className="w-12 h-12 mx-auto text-slate-300" />
            <p className="font-semibold text-lg">No events found</p>
            <p className="text-sm text-slate-400">Try adjusting search term or click "Create Event" to get started.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase">
                  <th className="px-6 py-4">Title & Type</th>
                  <th className="px-6 py-4">Session & Audience</th>
                  <th className="px-6 py-4">Schedule</th>
                  <th className="px-6 py-4">Venue & Seats</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                {filteredEvents.map((e: any) => (
                  <tr key={e.id} className="hover:bg-slate-50/50 transition">
                    <td className="px-6 py-4">
                      <p className="font-bold text-slate-900">{e.title}</p>
                      <p className="text-xs text-blue-600 font-semibold uppercase">{e.event_type}</p>
                    </td>
                    <td className="px-6 py-4 text-xs space-y-1">
                      <p><span className="text-slate-400">Session:</span> {e.academic_session?.session_name || 'N/A'}</p>
                      <p><span className="text-slate-400">Audience:</span> <span className="font-semibold text-slate-700">{e.audience}</span></p>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      <p className="font-semibold text-slate-800">{new Date(e.start_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</p>
                      <p className="text-slate-400">to {new Date(e.end_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</p>
                    </td>
                    <td className="px-6 py-4 text-xs space-y-0.5">
                      <p className="font-medium text-slate-800">{e.venue}</p>
                      <p className="text-slate-500">{e.registered_count} / {e.max_seats} seats booked</p>
                      {e.fee_required == 1 && <p className="text-green-600 font-semibold">₹{e.fee_amount}</p>}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                        e.status === 'Published' ? 'bg-green-100 text-green-800 border border-green-200' :
                        e.status === 'Closed' ? 'bg-slate-100 text-slate-800 border border-slate-200' :
                        'bg-yellow-100 text-yellow-800 border border-yellow-200'
                      }`}>
                        {e.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-center items-center gap-2">
                        {e.status === 'Draft' && (
                          <button
                            onClick={() => {
                              if (confirm('Are you sure you want to publish this event? Eligible users will be notified.')) {
                                publishMutation.mutate(e.id);
                              }
                            }}
                            title="Publish Event"
                            className="p-1.5 bg-green-50 hover:bg-green-100 text-green-700 rounded transition border border-green-200"
                          >
                            <Play size={15} />
                          </button>
                        )}
                        
                        {e.status === 'Published' && (
                          <button
                            onClick={() => loadAttendance(e.id, e.title)}
                            title="Mark Attendance"
                            className="p-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded transition border border-blue-200 flex items-center gap-1 text-xs font-semibold"
                          >
                            <CheckSquare size={14} /> Attendance
                          </button>
                        )}
                        
                        <Link
                          to={`/dashboard/staff/academics/event-management/reports?event_id=${e.id}`}
                          title="View Reports"
                          className="p-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 rounded transition border border-slate-200"
                        >
                          <BarChart size={15} />
                        </Link>
                        
                        <button
                          onClick={() => {
                            if (confirm('Are you sure you want to delete this event? This will remove all associated registrations and payments.')) {
                              deleteMutation.mutate(e.id);
                            }
                          }}
                          title="Delete Event"
                          className="p-1.5 bg-red-50 hover:bg-red-100 text-red-700 rounded transition border border-red-200"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Attendance marking Modal */}
      {attendanceEventId !== null && (
        <div className="fixed inset-0 bg-slate-900/60 flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="bg-slate-900 text-white p-4 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-lg">Mark Attendance</h3>
                <p className="text-xs text-slate-400">{attendanceEventTitle}</p>
              </div>
              <button
                onClick={() => setAttendanceEventId(null)}
                className="p-1.5 hover:bg-slate-800 rounded transition text-slate-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {loadingAttendance ? (
                <div className="flex justify-center items-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                </div>
              ) : attendanceList.length === 0 ? (
                <p className="text-center text-slate-500 py-8">No confirmed registrations found for this event.</p>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Confirmed Attendees</p>
                  <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden bg-white">
                    {attendanceList.map((att, idx) => (
                      <div key={att.registration_id} className="flex justify-between items-center p-4 hover:bg-slate-50 transition">
                        <div>
                          <p className="font-bold text-slate-800">{att.user_name}</p>
                          <p className="text-xs text-slate-500">{att.role} • Code: {att.computer_code}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => {
                              const updated = [...attendanceList];
                              updated[idx].attended = att.attended === 1 ? 0 : 1;
                              setAttendanceList(updated);
                            }}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition ${
                              att.attended === 1
                                ? 'bg-green-600 hover:bg-green-700 text-white shadow-sm'
                                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                            }`}
                          >
                            <Check size={14} /> {att.attended === 1 ? 'Attended' : 'Absent'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="bg-slate-50 p-4 border-t border-slate-200 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setAttendanceEventId(null)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  const payload = attendanceList.map(a => ({
                    registration_id: a.registration_id,
                    attended: a.attended
                  }));
                  saveAttendanceMutation.mutate(payload);
                }}
                disabled={saveAttendanceMutation.isPending}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition flex items-center gap-2 shadow"
              >
                {saveAttendanceMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />} Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
