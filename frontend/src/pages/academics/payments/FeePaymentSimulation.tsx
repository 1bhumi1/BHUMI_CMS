import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Loader2, ShieldCheck, ShieldAlert, CreditCard, Lock, ArrowLeft } from 'lucide-react';

export default function FeePaymentSimulation() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // PayU form variables from search parameters
  const key = searchParams.get('key') || '';
  const txnid = searchParams.get('txnid') || '';
  const amount = searchParams.get('amount') || '0.00';
  const productinfo = searchParams.get('productinfo') || 'College Fee';
  const firstname = searchParams.get('firstname') || 'Student';
  const email = searchParams.get('email') || '';
  const phone = searchParams.get('phone') || '';
  const surl = searchParams.get('surl') || 'http://127.0.0.1:8000/api/v1/payments/payu-callback';
  const furl = searchParams.get('furl') || 'http://127.0.0.1:8000/api/v1/payments/payu-callback';
  const hash = searchParams.get('hash') || '';
  const udf1 = searchParams.get('udf1') || '';
  const udf2 = searchParams.get('udf2') || '';

  // Form states
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvv, setCvv] = useState('');
  const [cardName, setCardName] = useState(firstname);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'success' | 'failed' | null>(null);

  // Auto-fill preset helper
  const handleAutoFill = () => {
    setCardNumber('4111 1111 1111 1111');
    setExpiry('12/29');
    setCvv('123');
    setCardName(firstname.toUpperCase());
  };

  const submitGatewayCallback = (paymentStatus: 'success' | 'failure') => {
    setLoading(true);
    setStatus(paymentStatus === 'success' ? 'success' : 'failed');

    setTimeout(() => {
      // Create HTML form and submit directly to the backend callback URL
      const form = document.createElement('form');
      form.method = 'POST';
      // If success, post to surl. If failure, post to furl.
      form.action = paymentStatus === 'success' ? surl : furl;

      const fields: Record<string, string> = {
        key,
        txnid,
        amount,
        productinfo,
        firstname,
        email,
        phone,
        status: paymentStatus,
        unmappedstatus: paymentStatus === 'success' ? 'captured' : 'failed',
        field9: paymentStatus === 'success' ? 'Successful' : 'Failed',
        error_Message: paymentStatus === 'success' ? 'No Error' : 'Transaction cancelled by user.',
        hash, // bypassed in test mode
        udf1,
        udf2
      };

      Object.entries(fields).forEach(([k, v]) => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = k;
        input.value = v;
        form.appendChild(input);
      });

      document.body.appendChild(form);
      form.submit();
    }, 2000);
  };

  // Card formatting handlers
  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '');
    const formattedValue = value.replace(/(\d{4})(?=\d)/g, '$1 ').substring(0, 19);
    setCardNumber(formattedValue);
  };

  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '');
    let formattedValue = value;
    if (value.length > 2) {
      formattedValue = `${value.substring(0, 2)}/${value.substring(2, 4)}`;
    }
    setExpiry(formattedValue.substring(0, 5));
  };

  const handleCvvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').substring(0, 4);
    setCvv(value);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="max-w-xl w-full bg-slate-950 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden flex flex-col md:flex-row">
        
        {/* Payment Summary Panel */}
        <div className="w-full md:w-5/12 bg-slate-900 p-6 border-b md:border-b-0 md:border-r border-slate-800 flex flex-col justify-between">
          <div className="space-y-6">
            <button 
              onClick={() => navigate('/dashboard/student/fees/pending')}
              className="text-slate-400 hover:text-white flex items-center gap-1 text-xs font-semibold tracking-wide transition duration-150"
            >
              <ArrowLeft size={14} /> Back to Fees
            </button>

            <div>
              <span className="bg-blue-900/40 text-blue-400 text-[10px] font-bold uppercase px-2 py-0.5 rounded border border-blue-800">
                Test Sandbox
              </span>
              <h2 className="text-xl font-bold text-white mt-3">PayU Gateway</h2>
              <p className="text-slate-400 text-xs mt-1">College Fee Checkout</p>
            </div>

            <div className="space-y-3 pt-2">
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-bold block">Fee Description</span>
                <span className="text-sm font-semibold text-slate-200">{productinfo}</span>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-bold block">Transaction ID</span>
                <span className="text-xs font-mono text-slate-300 break-all">{txnid}</span>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] uppercase font-bold block">Student</span>
                <span className="text-xs text-slate-300">{firstname} ({udf1})</span>
              </div>
            </div>
          </div>

          <div className="pt-6 mt-6 border-t border-slate-800/80">
            <span className="text-slate-500 text-[10px] uppercase font-bold block">Total Amount</span>
            <span className="text-3xl font-extrabold text-white">₹{amount}</span>
          </div>
        </div>

        {/* Checkout Card Entry Panel */}
        <div className="w-full md:w-7/12 p-6 flex flex-col justify-center relative">
          
          {status ? (
            <div className="text-center py-12 space-y-4">
              {status === 'success' ? (
                <div className="text-emerald-500 flex flex-col items-center space-y-3">
                  <ShieldCheck className="w-16 h-16 animate-bounce" />
                  <div>
                    <h3 className="text-lg font-bold text-white">Payment Authorized</h3>
                    <p className="text-slate-400 text-xs mt-1">Completing callback & redirecting...</p>
                  </div>
                </div>
              ) : (
                <div className="text-red-500 flex flex-col items-center space-y-3">
                  <ShieldAlert className="w-16 h-16 animate-pulse" />
                  <div>
                    <h3 className="text-lg font-bold text-white">Payment Cancelled</h3>
                    <p className="text-slate-400 text-xs mt-1">Processing failure callback...</p>
                  </div>
                </div>
              )}
              <Loader2 className="w-6 h-6 animate-spin text-slate-500 mx-auto" />
            </div>
          ) : (
            <div className="space-y-5">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <CreditCard size={16} className="text-blue-500" /> Enter Card Details
                </h3>
                <button
                  onClick={handleAutoFill}
                  className="text-xs text-blue-400 hover:text-blue-300 font-semibold underline decoration-dashed transition duration-150"
                >
                  Auto-Fill Demo
                </button>
              </div>

              <div className="space-y-3.5">
                <div>
                  <label className="text-slate-400 text-xs block mb-1">Card Number</label>
                  <input
                    type="text"
                    value={cardNumber}
                    onChange={handleCardNumberChange}
                    placeholder="4111 1111 1111 1111"
                    className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 text-white rounded-lg p-2.5 text-sm font-mono placeholder-slate-600 outline-none transition duration-150"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-slate-400 text-xs block mb-1">Expiry Date</label>
                    <input
                      type="text"
                      value={expiry}
                      onChange={handleExpiryChange}
                      placeholder="MM/YY"
                      className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 text-white rounded-lg p-2.5 text-sm font-mono placeholder-slate-600 outline-none transition duration-150"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 text-xs block mb-1">CVV / CID</label>
                    <input
                      type="password"
                      value={cvv}
                      onChange={handleCvvChange}
                      placeholder="•••"
                      className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 text-white rounded-lg p-2.5 text-sm font-mono placeholder-slate-600 outline-none transition duration-150"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-slate-400 text-xs block mb-1">Cardholder Name</label>
                  <input
                    type="text"
                    value={cardName}
                    onChange={(e) => setCardName(e.target.value.toUpperCase())}
                    placeholder="STUDENT ONE"
                    className="w-full bg-slate-900 border border-slate-800 focus:border-blue-500 text-white rounded-lg p-2.5 text-sm placeholder-slate-600 outline-none transition duration-150"
                  />
                </div>
              </div>

              <div className="pt-2 space-y-3">
                <button
                  onClick={() => submitGatewayCallback('success')}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-sm font-semibold rounded-lg shadow-lg shadow-blue-900/30 transition duration-150 flex items-center justify-center gap-1.5"
                >
                  <Lock size={14} /> Pay ₹{amount}
                </button>
                <button
                  onClick={() => submitGatewayCallback('failure')}
                  className="w-full py-2.5 bg-transparent border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-slate-200 text-xs font-semibold rounded-lg transition duration-150"
                >
                  Cancel Transaction
                </button>
              </div>

              <p className="text-[10px] text-slate-500 text-center flex items-center justify-center gap-1">
                <Lock size={10} /> Secured 256-bit encryption • Sandbox Mode
              </p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
