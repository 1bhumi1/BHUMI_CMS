import React from 'react';
import { useAuth } from '../lib/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Link } from 'react-router-dom';
import PermissionGuard from '../components/PermissionGuard';
import { Users, GraduationCap, ClipboardList, BookOpen, DollarSign, Calendar, MapPin, Clock, ArrowRight, ShieldCheck, Loader2 } from 'lucide-react';

export default function StaffDashboard() {
  const { user, role, department } = useAuth();

  // Load events visible to the current staff member
  const { data: events = [], isLoading: loadingEvents } = useQuery({
    queryKey: ['user-events-list-staff-dashboard'],
    queryFn: async () => {
      // Check role - Principal doesn't participate in events listing
      if (role === 'Principal') return [];
      const res = await api.get('/events/');
      return res.data?.data || [];
    },
    enabled: role !== 'Principal'
  });

  // Load staff's registrations
  const { data: myRegistrations = [], isLoading: loadingMy } = useQuery({
    queryKey: ['my-registrations-list-staff-dashboard'],
    queryFn: async () => {
      if (role === 'Principal') return [];
      const res = await api.get('/events/registrations/my');
      return res.data?.data || [];
    },
    enabled: role !== 'Principal'
  });

  // Filter Upcoming (Not registered yet)
  const upcomingEvents = events.filter((e: any) => !e.is_registered);
  
  // Confirmed registrations
  const registeredEvents = myRegistrations.filter((r: any) => r.status === 'Confirmed');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Staff Dashboard</h1>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-800 mb-2">Welcome, {user?.name}</h2>
        <p className="text-slate-500">
          Department: <span className="font-medium text-slate-700">{department || 'Not assigned'}</span>
        </p>
      </div>

      {/* Stats Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        <PermissionGuard permission="student.read">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-blue-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
              <GraduationCap size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Students</p>
              <p className="text-xl font-bold text-slate-800">Manage</p>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard permission="faculty.read">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-emerald-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center">
              <Users size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Faculty</p>
              <p className="text-xl font-bold text-slate-800">Directory</p>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard permission="attendance.manage">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-amber-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-lg flex items-center justify-center">
              <ClipboardList size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Attendance</p>
              <p className="text-xl font-bold text-slate-800">Record</p>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard permission="exam.manage">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-purple-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center">
              <BookOpen size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Marks</p>
              <p className="text-xl font-bold text-slate-800">Entry</p>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard permission="fees.manage">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-green-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-green-100 text-green-600 rounded-lg flex items-center justify-center">
              <DollarSign size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Fees</p>
              <p className="text-xl font-bold text-slate-800">Collection</p>
            </div>
          </div>
        </PermissionGuard>

      </div>

      {/* Events Panels (Only for HOD / Faculty - Principal is excluded) */}
      {role !== 'Principal' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
          
          {/* Upcoming Events */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-3 mb-4">
                <h3 className="font-bold text-lg text-slate-900 flex items-center gap-2">
                  <Calendar className="text-blue-600 w-5 h-5" /> Upcoming Events
                </h3>
                <Link to="/dashboard/staff/academics/events" className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1">
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
                      to={`/dashboard/staff/academics/events/${e.id}`}
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
      )}
    </div>
  );
}
