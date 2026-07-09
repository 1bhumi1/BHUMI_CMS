import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { api } from '../../../lib/api';
import { useAuth } from '../../../lib/AuthContext';
import {
  Calendar, Loader2, CreditCard, Award, CheckCircle2, AlertCircle, Clock, MapPin, Sparkles
} from 'lucide-react';

export default function UserEvents() {
  const { role } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'all' | 'my'>('all');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Get current prefix path to correctly configure return URL of payment redirects
  const isStudent = location.pathname.includes('/student');
  const dashboardPrefix = isStudent ? '/dashboard/student' : '/dashboard/staff/academics';

  // Load events visible to the current user
  const { data: events = [], isLoading: loadingEvents } = useQuery({
    queryKey: ['user-events-list'],
    queryFn: async () => {
      const res = await api.get('/events/');
      return res.data?.data || [];
    }
  });

  // Load current user's registrations
  const { data: myRegistrations = [], isLoading: loadingMy } = useQuery({
    queryKey: ['my-registrations-list'],
    queryFn: async () => {
      const res = await api.get('/events/registrations/my');
      return res.data?.data || [];
    }
  });

  const registerMutation = useMutation({
    mutationFn: async (eventId: number) => {
      const res = await api.post(`/events/${eventId}/register`);
      return res.data;
    },
    onSuccess: (resData) => {
      const data = resData.data;
      if (data.payment_required) {
        setToast({ message: 'Redirecting to payment gateway...', type: 'success' });
        setTimeout(() => {
          navigate(`${dashboardPrefix}/events/payment-simulation?txnId=${data.transaction_id}&amount=${data.amount}&returnUrl=${location.pathname}`);
        }, 1200);
      } else {
        setToast({ message: 'Successfully registered for event!', type: 'success' });
        queryClient.invalidateQueries({ queryKey: ['user-events-list'] });
        queryClient.invalidateQueries({ queryKey: ['my-registrations-list'] });
      }
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || 'Failed to register.', type: 'error' });
    }
  });

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="text-blue-600 animate-pulse" /> Campus Events & Workshops
          </h1>
          <p className="text-sm text-slate-500">Discover coding hackathons, guest seminars, training bootcamps, and view your certificates</p>
        </div>

        {/* Tab Buttons */}
        <div className="bg-slate-100 p-1 rounded-lg flex border border-slate-200">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-2 text-sm font-semibold rounded-md transition ${
              activeTab === 'all' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            All Events
          </button>
          <button
            onClick={() => setActiveTab('my')}
            className={`px-4 py-2 text-sm font-semibold rounded-md transition ${
              activeTab === 'my' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            My Signups & Certs
          </button>
        </div>
      </div>

      {toast && (
        <div className={`p-4 rounded-lg flex items-center gap-3 border ${
          toast.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <CheckCircle2 size={20} />
          <p className="text-sm font-medium">{toast.message}</p>
          <button onClick={() => setToast(null)} className="ml-auto text-xs font-bold uppercase hover:underline">Dismiss</button>
        </div>
      )}

      {activeTab === 'all' ? (
        loadingEvents ? (
          <div className="flex justify-center items-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-16 text-slate-500 bg-white rounded-xl border border-slate-200 p-6 space-y-2">
            <Calendar className="w-12 h-12 mx-auto text-slate-300" />
            <p className="font-semibold text-lg">No events available</p>
            <p className="text-sm text-slate-400">There are no published events matching your department or role right now.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {events.map((e: any) => {
              const spotsLeft = Math.max(0, e.max_seats - e.registered_count);
              const deadlinePassed = new Date() > new Date(e.registration_deadline);
              
              return (
                <div key={e.id} className="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden flex flex-col justify-between hover:shadow-lg transition duration-200">
                  <Link to={`${isStudent ? '/dashboard/student' : '/dashboard/staff/academics'}/events/${e.id}`} className="p-6 space-y-4 cursor-pointer hover:bg-slate-50/50 block">
                    <div className="flex justify-between items-start">
                      <span className="px-2.5 py-1 rounded bg-blue-50 border border-blue-100 text-blue-700 text-xs font-bold uppercase tracking-wider">
                        {e.event_type}
                      </span>
                      {e.fee_required == 1 ? (
                        <span className="font-bold text-green-600 text-sm">₹{e.fee_amount}</span>
                      ) : (
                        <span className="font-bold text-slate-400 text-sm">Free</span>
                      )}
                    </div>

                    <div className="space-y-1">
                      <h3 className="font-bold text-lg text-slate-900 leading-snug hover:text-blue-600 transition">{e.title}</h3>
                      <p className="text-xs text-slate-500 line-clamp-3">{e.description}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
                      <div className="flex items-center gap-1.5">
                        <MapPin size={14} className="text-slate-400" />
                        <span className="truncate">{e.venue}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock size={14} className="text-slate-400" />
                        <span>{new Date(e.start_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>
                      </div>
                    </div>
                  </Link>

                  <div className="px-6 py-4 bg-slate-50/50 border-t border-slate-100 flex justify-between items-center gap-4">
                    <span className="text-xs text-slate-500">
                      {spotsLeft > 0 ? `${spotsLeft} seats remaining` : 'Fully booked'}
                    </span>

                    {e.is_registered ? (
                      <span className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 ${
                        e.registration_status === 'Confirmed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        <CheckCircle2 size={14} /> {e.registration_status === 'Confirmed' ? 'Registered' : 'Pending Pay'}
                      </span>
                    ) : (
                      <button
                        disabled={spotsLeft === 0 || deadlinePassed || registerMutation.isPending}
                        onClick={() => registerMutation.mutate(e.id)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 disabled:text-slate-400 text-white font-semibold rounded-lg text-xs transition shadow-sm"
                      >
                        {spotsLeft === 0 ? 'Sold Out' : deadlinePassed ? 'Deadline Passed' : 'Register Now'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : (
        loadingMy ? (
          <div className="flex justify-center items-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : myRegistrations.length === 0 ? (
          <div className="text-center py-16 text-slate-500 bg-white rounded-xl border border-slate-200 p-6 space-y-2">
            <Calendar className="w-12 h-12 mx-auto text-slate-300" />
            <p className="font-semibold text-lg">No active signups</p>
            <p className="text-sm text-slate-400">Events you sign up for will be managed and tracked here.</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 shadow-md overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase">
                    <th className="px-6 py-4">Event Details</th>
                    <th className="px-6 py-4">Signup Date</th>
                    <th className="px-6 py-4">Fee status</th>
                    <th className="px-6 py-4">Attended?</th>
                    <th className="px-6 py-4 text-center">Certificate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                  {myRegistrations.map((r: any) => (
                    <tr key={r.id} className="hover:bg-slate-50/50 transition">
                      <td className="px-6 py-4 font-bold text-slate-900">
                        <p>{r.event_title}</p>
                        <p className="text-xs text-blue-600 font-semibold uppercase">{r.event_type}</p>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-500">
                        {new Date(r.registered_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </td>
                      <td className="px-6 py-4 text-xs">
                        {r.payment_status === 'Free' ? (
                          <span className="text-slate-400">Free</span>
                        ) : r.payment_status === 'Success' ? (
                          <span className="text-green-600 font-bold">Paid</span>
                        ) : (
                          <button
                            onClick={() => navigate(`${dashboardPrefix}/events/payment-simulation?txnId=${r.certificate_code || 'MOCK'}&amount=${r.payment_amount}&returnUrl=${location.pathname}`)}
                            className="px-2 py-1 bg-yellow-600 hover:bg-yellow-700 text-white font-semibold rounded text-[11px] flex items-center gap-1 shadow-sm transition"
                          >
                            <CreditCard size={12} /> Pay ₹{r.payment_amount}
                          </button>
                        )}
                      </td>
                      <td className="px-6 py-4 text-xs font-semibold text-slate-600">
                        {r.status === 'Confirmed' ? (r.attended === 1 ? '✓ Yes' : 'No') : 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {r.has_certificate ? (
                          <a
                            href="#"
                            onClick={(e) => {
                              e.preventDefault();
                              alert(`Certificate Issued!\nCode: ${r.certificate_code}\nLink: ${r.certificate_code}`);
                            }}
                            className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-600 hover:bg-green-700 text-white font-semibold rounded text-xs transition shadow-sm"
                          >
                            <Award size={14} /> Download Certificate
                          </a>
                        ) : (
                          <span className="text-slate-400 text-xs">Not Issued</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}
    </div>
  );
}
