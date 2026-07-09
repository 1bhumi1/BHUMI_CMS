import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../lib/api';
import { useAuth } from '../../../lib/AuthContext';
import {
  Calendar, MapPin, Clock, Users, ArrowLeft, Loader2, CreditCard, ShieldCheck, AlertCircle
} from 'lucide-react';

export default function EventDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { role } = useAuth();
  const queryClient = useQueryClient();

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Determine prefix path to correctly configure return URL of payment redirects
  const isStudent = window.location.pathname.includes('/student');
  const dashboardPrefix = isStudent ? '/dashboard/student' : '/dashboard/staff/academics';
  const listUrl = isStudent ? '/dashboard/student/events' : '/dashboard/staff/academics/events';

  // Load event details
  const { data: eventRes, isLoading, error } = useQuery({
    queryKey: ['event-details', id],
    queryFn: async () => {
      const res = await api.get(`/events/${id}`);
      return res.data?.data || null;
    },
    enabled: !!id
  });

  const registerMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/events/${id}/register`);
      return res.data;
    },
    onSuccess: (resData) => {
      const data = resData.data;
      if (data.payment_required) {
        setToast({ message: 'Redirecting to payment gateway...', type: 'success' });
        setTimeout(() => {
          navigate(`${dashboardPrefix}/events/payment-simulation?txnId=${data.transaction_id}&amount=${data.amount}&returnUrl=${window.location.pathname}`);
        }, 1200);
      } else {
        setToast({ message: 'Successfully registered for event!', type: 'success' });
        queryClient.invalidateQueries({ queryKey: ['event-details', id] });
        queryClient.invalidateQueries({ queryKey: ['user-events-list'] });
        queryClient.invalidateQueries({ queryKey: ['my-registrations-list'] });
      }
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || 'Failed to register.', type: 'error' });
    }
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-24">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !eventRes) {
    return (
      <div className="max-w-md mx-auto my-12 bg-white rounded-xl shadow border border-slate-200 p-8 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
        <h3 className="text-xl font-bold text-slate-800">Event Not Found</h3>
        <p className="text-slate-500 text-sm">The event you are looking for does not exist or has been deleted.</p>
        <button
          onClick={() => navigate(listUrl)}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition"
        >
          Back to Events List
        </button>
      </div>
    );
  }

  const spotsLeft = Math.max(0, eventRes.max_seats - eventRes.registered_count);
  const deadlinePassed = new Date() > new Date(eventRes.registration_deadline);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(listUrl)}
          className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition border border-slate-200 bg-white shadow-sm"
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Event Details</h2>
          <h1 className="text-xl font-bold text-slate-900 truncate max-w-xl">{eventRes.title}</h1>
        </div>
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Details Panel */}
        <div className="lg:col-span-2 space-y-6 bg-white rounded-xl shadow-md border border-slate-200 p-6">
          {/* Poster or Default Header */}
          {eventRes.poster_url ? (
            <div className="w-full h-64 rounded-lg overflow-hidden border border-slate-100 shadow-inner">
              <img src={eventRes.poster_url} alt={eventRes.title} className="w-full h-full object-cover" />
            </div>
          ) : (
            <div className="w-full h-44 bg-gradient-to-br from-slate-900 via-slate-800 to-blue-900 rounded-lg flex flex-col justify-center items-center text-white p-6 text-center border border-slate-700 relative">
              <Calendar className="w-12 h-12 text-blue-500 mb-2 opacity-80" />
              <h3 className="font-bold text-xl leading-tight">{eventRes.title}</h3>
              <p className="text-xs text-blue-300 font-semibold uppercase mt-1 tracking-wider">{eventRes.event_type}</p>
            </div>
          )}

          {/* Description Section */}
          <div className="space-y-3">
            <h3 className="font-bold text-lg text-slate-900 border-b border-slate-100 pb-2">Description</h3>
            <p className="text-sm text-slate-600 whitespace-pre-line leading-relaxed">{eventRes.description}</p>
          </div>
        </div>

        {/* Sidebar Info Panel */}
        <div className="space-y-6">
          {/* Status & Action Card */}
          <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 space-y-6">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-slate-500">Registration Fee</span>
              {eventRes.fee_required == 1 ? (
                <span className="font-extrabold text-2xl text-green-600">₹{eventRes.fee_amount}</span>
              ) : (
                <span className="font-extrabold text-2xl text-slate-500">Free</span>
              )}
            </div>

            <div className="border-t border-slate-100 pt-4 space-y-4">
              {eventRes.is_registered ? (
                <div className={`p-4 rounded-lg flex flex-col items-center justify-center gap-2 border text-center ${
                  eventRes.registration_status === 'Confirmed' ? 'bg-green-50 border-green-100 text-green-800' : 'bg-yellow-50 border-yellow-100 text-yellow-800'
                }`}>
                  <ShieldCheck className="w-10 h-10 text-green-600" />
                  <div>
                    <p className="font-bold text-sm">
                      {eventRes.registration_status === 'Confirmed' ? 'Registration Confirmed!' : 'Registration Pending Payment'}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      {eventRes.registration_status === 'Confirmed' ? 'We look forward to seeing you at the event.' : 'Complete your payment redirection to confirm seats.'}
                    </p>
                  </div>
                  {eventRes.registration_status === 'Pending' && (
                    <button
                      onClick={() => registerMutation.mutate()}
                      className="mt-3 w-full py-2 bg-yellow-600 hover:bg-yellow-700 text-white font-semibold rounded-lg text-xs shadow-sm flex items-center justify-center gap-1.5 transition"
                    >
                      <CreditCard size={13} /> Complete Payment
                    </button>
                  )}
                </div>
              ) : (
                <button
                  disabled={spotsLeft === 0 || deadlinePassed || registerMutation.isPending}
                  onClick={() => registerMutation.mutate()}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 disabled:text-slate-400 text-white font-semibold rounded-lg text-sm shadow transition duration-150 flex items-center justify-center gap-2"
                >
                  {registerMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : spotsLeft === 0 ? (
                    'Sold Out'
                  ) : deadlinePassed ? (
                    'Registration Closed'
                  ) : eventRes.fee_required == 1 ? (
                    'Pay & Register'
                  ) : (
                    'Register Now'
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Quick Details Card */}
          <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 space-y-4">
            <h3 className="font-bold text-slate-900 border-b border-slate-100 pb-2">Quick Information</h3>
            
            <div className="space-y-4 text-sm text-slate-700">
              {/* Date */}
              <div className="flex gap-3 items-start">
                <Clock className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-slate-900">Date & Time</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Starts: {new Date(eventRes.start_date).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Ends: {new Date(eventRes.end_date).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>

              {/* Venue */}
              <div className="flex gap-3 items-start">
                <MapPin className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-slate-900">Venue</p>
                  <p className="text-xs text-slate-500 mt-0.5">{eventRes.venue}</p>
                </div>
              </div>

              {/* Seats */}
              <div className="flex gap-3 items-start">
                <Users className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-slate-900">Seats Capacity</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {eventRes.registered_count} / {eventRes.max_seats} booked ({spotsLeft} remaining)
                  </p>
                </div>
              </div>

              {/* Registration Deadline */}
              <div className="flex gap-3 items-start border-t border-slate-100 pt-3">
                <Clock className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-red-600">Registration Closes</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {new Date(eventRes.registration_deadline).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
