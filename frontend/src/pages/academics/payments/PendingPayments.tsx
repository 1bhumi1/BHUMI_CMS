import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../../../lib/api';
import { useAuth } from '../../../lib/AuthContext';
import { Calendar, DollarSign, AlertCircle, Loader2, CreditCard } from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';

export default function PendingPayments() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(() => {
    const status = searchParams.get('status');
    const txnid = searchParams.get('txnid');
    if (status === 'success') {
      return { message: `Payment successful! Transaction ID: ${txnid}`, type: 'success' };
    } else if (status === 'failure' || status === 'failed') {
      return { message: `Payment failed or cancelled. Transaction ID: ${txnid}`, type: 'error' };
    }
    return null;
  });

  // Fetch pending fees
  const { data: fees = [], isLoading, error } = useQuery({
    queryKey: ['pending-fees'],
    queryFn: async () => {
      const res = await api.get('/payments/student/pending');
      return res.data?.data || [];
    }
  });

  // Initiate payment mutation
  const payMutation = useMutation({
    mutationFn: async (feeId: number) => {
      const res = await api.post(`/payments/initiate/${feeId}`);
      return res.data?.data;
    },
    onSuccess: (data) => {
      // Check if we are in test mode or key is TEST_KEY, redirect to local simulated checkout
      if (data.key === 'TEST_KEY' || data.action_url.includes('sandbox')) {
        const queryParams = new URLSearchParams({
          key: data.key || '',
          txnid: data.txnid || '',
          amount: String(data.amount || ''),
          productinfo: data.productinfo || '',
          firstname: data.firstname || '',
          email: data.email || '',
          phone: String(data.phone || ''),
          surl: data.surl || '',
          furl: data.furl || '',
          hash: data.hash || '',
          udf1: data.udf1 || '',
          udf2: data.udf2 || ''
        }).toString();
        navigate(`/dashboard/student/fees/payment-simulation?${queryParams}`);
        return;
      }

      // Dynamic HTML form submit for PayU redirection (Production)
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = data.action_url;

      const fields = {
        key: data.key,
        txnid: data.txnid,
        amount: data.amount,
        productinfo: data.productinfo,
        firstname: data.firstname,
        email: data.email,
        phone: data.phone,
        surl: data.surl,
        furl: data.furl,
        hash: data.hash,
        udf1: data.udf1,
        udf2: data.udf2
      };

      Object.entries(fields).forEach(([k, v]) => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = k;
        input.value = String(v);
        form.appendChild(input);
      });

      document.body.appendChild(form);
      form.submit();
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || 'Failed to initiate payment.', type: 'error' });
    }
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-24">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <CreditCard className="text-blue-600" /> Pending Payments
        </h1>
        <p className="text-sm text-slate-500">View and pay your assigned college fees, exams fee, and workshop dues safely</p>
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

      {error ? (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg text-sm font-medium">
          Failed to load pending payments. Please try again later.
        </div>
      ) : fees.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center text-slate-500 space-y-2">
          <DollarSign className="w-12 h-12 mx-auto text-slate-300" />
          <p className="font-semibold text-lg">No pending payments</p>
          <p className="text-sm text-slate-400">All your assigned college fee items are paid. Thank you!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {fees.map((fee: any) => {
            const isPending = payMutation.isPending && payMutation.variables === fee.id;
            const dueDate = new Date(fee.fee_structure.due_date);
            const isOverdue = new Date() > dueDate;
            
            return (
              <div key={fee.id} className="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden flex flex-col justify-between hover:shadow-lg transition duration-200">
                <div className="p-6 space-y-4">
                  <div className="flex justify-between items-start">
                    <span className={`px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider ${
                      isOverdue ? 'bg-red-50 border border-red-100 text-red-700' : 'bg-amber-50 border border-amber-100 text-amber-700'
                    }`}>
                      {isOverdue ? 'Overdue' : 'Pending'}
                    </span>
                    <span className="font-extrabold text-2xl text-slate-900">₹{fee.fee_structure.amount}</span>
                  </div>

                  <div className="space-y-1">
                    <h3 className="font-bold text-lg text-slate-900 leading-snug">{fee.fee_structure.title}</h3>
                    <p className="text-xs text-slate-500 line-clamp-3">{fee.fee_structure.description}</p>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <Calendar size={14} className="text-slate-400" />
                    <span>Due Date: <b>{dueDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</b></span>
                  </div>
                </div>

                <div className="px-6 py-4 bg-slate-50/50 border-t border-slate-100 flex justify-end">
                  <button
                    disabled={payMutation.isPending}
                    onClick={() => payMutation.mutate(fee.id)}
                    className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-semibold rounded-lg text-xs shadow-sm transition duration-150 flex items-center gap-1.5"
                  >
                    {isPending ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Redirection...
                      </>
                    ) : (
                      <>
                        <CreditCard size={14} /> Pay Now
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
