import React from 'react';
import { useAuth } from '../lib/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Link } from 'react-router-dom';
import { BookOpen, Calendar, DollarSign, FileText, Loader2, MapPin, Clock, ArrowRight, ShieldCheck } from 'lucide-react';

export default function StudentDashboard() {
  const { user } = useAuth();

  // Load events visible to the current student
  const { data: events = [], isLoading: loadingEvents } = useQuery({
    queryKey: ['user-events-list-dashboard'],
    queryFn: async () => {
      const res = await api.get('/events/');
      return res.data?.data || [];
    }
  });

  // Load student's registrations
  const { data: myRegistrations = [], isLoading: loadingMy } = useQuery({
    queryKey: ['my-registrations-list-dashboard'],
    queryFn: async () => {
      const res = await api.get('/events/registrations/my');
      return res.data?.data || [];
    }
  });

  // Filter Upcoming (Not registered yet and Published status)
  const upcomingEvents = events.filter((e: any) => !e.is_registered);
  
  // Confirmed registrations
  const registeredEvents = myRegistrations.filter((r: any) => r.status === 'Confirmed');

  // Registrations that had fees (Success or Pending)
  const paidRegistrations = myRegistrations.filter((r: any) => r.payment_status !== 'Free');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Student Dashboard</h1>
      </div>

      {/* Welcome Card */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-800 mb-2">Welcome back, {user?.name}</h2>
        <p className="text-slate-500">
          Roll No: <span className="font-medium text-slate-700">{user?.computer_code}</span>
        </p>
      </div>

      {/* Stats Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-4">
          <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
            <Calendar size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Attendance</p>
            <p className="text-2xl font-bold text-slate-800">85%</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-4">
          <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center">
            <FileText size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Current SGPA</p>
            <p className="text-2xl font-bold text-slate-800">8.4</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-4">
          <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-lg flex items-center justify-center">
            <BookOpen size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Classes Today</p>
            <p className="text-2xl font-bold text-slate-800">4</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-4">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center">
            <DollarSign size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Fee Status</p>
            <p className="text-2xl font-bold text-emerald-600">Paid</p>
          </div>
        </div>
      </div>

      {/* Events Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Upcoming Events */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center border-b border-slate-100 pb-3 mb-4">
              <h3 className="font-bold text-lg text-slate-900 flex items-center gap-2">
                <Calendar className="text-blue-600 w-5 h-5" /> Upcoming Events
              </h3>
              <Link to="/dashboard/student/events" className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1">
                View All <ArrowRight size={12} />
              </Link>
            </div>

            {loadingEvents ? (
              <div className="flex justify-center items-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              </div>
            ) : upcomingEvents.length === 0 ? (
              <p className="text-slate-400 text-sm py-4 text-center">No upcoming events right now.</p>
            ) : (
              <div className="space-y-3">
                {upcomingEvents.slice(0, 3).map((e: any) => (
                  <Link
                    key={e.id}
                    to={`/dashboard/student/events/${e.id}`}
                    className="block p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition cursor-pointer"
                  >
                    <div className="flex justify-between items-start">
                      <h4 className="font-bold text-sm text-slate-800 hover:text-blue-600 transition">{e.title}</h4>
                      <span className="px-1.5 py-0.5 rounded bg-blue-50 text-[10px] text-blue-700 font-bold uppercase tracking-wider">{e.event_type}</span>
                    </div>
                    <div className="flex gap-4 text-[11px] text-slate-500 mt-2">
                      <span className="flex items-center gap-1"><MapPin size={12} /> {e.venue}</span>
                      <span className="flex items-center gap-1"><Clock size={12} /> {new Date(e.start_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Registered Events */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center border-b border-slate-100 pb-3 mb-4">
              <h3 className="font-bold text-lg text-slate-900 flex items-center gap-2">
                <ShieldCheck className="text-green-600 w-5 h-5" /> Registered Events
              </h3>
            </div>

            {loadingMy ? (
              <div className="flex justify-center items-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              </div>
            ) : registeredEvents.length === 0 ? (
              <p className="text-slate-400 text-sm py-4 text-center">You haven't registered for any events yet.</p>
            ) : (
              <div className="space-y-3">
                {registeredEvents.slice(0, 3).map((r: any) => (
                  <div key={r.id} className="p-3 rounded-lg border border-slate-100 bg-green-50/20">
                    <div className="flex justify-between items-start">
                      <h4 className="font-bold text-sm text-slate-800">{r.event_title}</h4>
                      <span className="px-1.5 py-0.5 rounded bg-green-100 text-[10px] text-green-800 font-bold uppercase tracking-wider">Confirmed</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1.5">Registered on: {new Date(r.registered_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Payment History */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="border-b border-slate-100 pb-3 mb-4">
          <h3 className="font-bold text-lg text-slate-900 flex items-center gap-2">
            <DollarSign className="text-emerald-600 w-5 h-5" /> Event Payment History
          </h3>
        </div>

        {loadingMy ? (
          <div className="flex justify-center items-center py-6">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          </div>
        ) : paidRegistrations.length === 0 ? (
          <p className="text-slate-400 text-sm py-4 text-center">No payment history found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs uppercase">
                  <th className="px-4 py-2.5">Event</th>
                  <th className="px-4 py-2.5">Amount</th>
                  <th className="px-4 py-2.5">Payment Date</th>
                  <th className="px-4 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paidRegistrations.map((p: any) => (
                  <tr key={p.id}>
                    <td className="px-4 py-3 font-medium text-slate-800">{p.event_title}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900">₹{p.payment_amount}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      {new Date(p.registered_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                        p.payment_status === 'Success' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {p.payment_status}
                      </span>
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
