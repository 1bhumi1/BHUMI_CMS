import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../../../lib/api';
import { Loader2, ShieldCheck, ShieldAlert, CreditCard } from 'lucide-react';

export default function PaymentSimulation() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const txnId = searchParams.get('txnId') || '';
  const amount = searchParams.get('amount') || '0.00';
  const returnUrl = searchParams.get('returnUrl') || '/dashboard/student/events';
  
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'success' | 'failed' | null>(null);

  const handlePayment = async (statusStr: 'Success' | 'Failed') => {
    setLoading(true);
    try {
      await api.post('/events/payments/payu-callback', {
        transaction_id: txnId,
        status: statusStr,
        payment_gateway_ref: `PAYU-MOCK-${Math.floor(Math.random() * 1000000)}`
      });
      setStatus(statusStr.toLowerCase() as 'success' | 'failed');
      setTimeout(() => {
        navigate(returnUrl, { replace: true });
      }, 2000);
    } catch (e) {
      alert('Error communicating with payment gateway');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-12 bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden">
      <div className="bg-slate-900 px-6 py-8 text-center text-white relative">
        <div className="absolute top-0 right-0 p-3 text-xs bg-red-600 font-bold uppercase tracking-wider rounded-bl">
          Simulation Mode
        </div>
        <CreditCard className="w-12 h-12 mx-auto text-blue-500 mb-2" />
        <h2 className="text-2xl font-bold tracking-tight">PayU Gateway</h2>
        <p className="text-slate-400 text-sm mt-1">Merchant Payment Simulation Interface</p>
      </div>

      <div className="p-6 space-y-6">
        {status ? (
          <div className="text-center py-6 space-y-4">
            {status === 'success' ? (
              <div className="text-green-600 flex flex-col items-center">
                <ShieldCheck className="w-16 h-16 animate-bounce" />
                <h3 className="text-xl font-bold mt-2">Payment Successful!</h3>
                <p className="text-slate-500 text-sm mt-1">Redirecting you back to the app...</p>
              </div>
            ) : (
              <div className="text-red-600 flex flex-col items-center">
                <ShieldAlert className="w-16 h-16 animate-pulse" />
                <h3 className="text-xl font-bold mt-2">Payment Failed!</h3>
                <p className="text-slate-500 text-sm mt-1">Redirecting you back to the app...</p>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="bg-slate-50 rounded-lg p-4 border border-slate-100 space-y-3">
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500">Transaction ID:</span>
                <span className="font-semibold text-slate-800">{txnId || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500">Amount to Pay:</span>
                <span className="font-bold text-lg text-slate-900">₹{amount}</span>
              </div>
            </div>

            <div className="space-y-3">
              <button
                disabled={loading || !txnId}
                onClick={() => handlePayment('Success')}
                className="w-full py-3 bg-green-600 hover:bg-green-700 disabled:bg-slate-300 text-white font-semibold rounded-lg shadow transition duration-150 flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Confirm Payment (Success)'}
              </button>
              
              <button
                disabled={loading || !txnId}
                onClick={() => handlePayment('Failed')}
                className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:bg-slate-300 text-white font-semibold rounded-lg shadow transition duration-150 flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Cancel Payment (Failure)'}
              </button>
            </div>
            
            <p className="text-xs text-center text-slate-400">
              Disclaimer: This is a safe, virtual sandbox simulating the PayU redirect flow. No real funds are transferred.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
