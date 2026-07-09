import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../../lib/api';
import { CreditCard, DollarSign, Download, Loader2, AlertCircle, Calendar } from 'lucide-react';

export default function PaymentHistory() {
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  // Fetch payment history
  const { data: history = [], isLoading, error } = useQuery({
    queryKey: ['payment-history'],
    queryFn: async () => {
      const res = await api.get('/payments/student/history');
      return res.data?.data || [];
    }
  });

  const downloadReceipt = async (txnId: number, txnidStr: string) => {
    setDownloadingId(txnId);
    try {
      const response = await api.get(`/payments/receipt/${txnId}/download`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Receipt_${txnidStr}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (e) {
      alert('Receipt document not generated or found for this transaction.');
    } finally {
      setDownloadingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-24">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Calendar className="text-blue-600" /> Payment History
        </h1>
        <p className="text-sm text-slate-500">Track all your past transactions, fees status, and download invoice receipts</p>
      </div>

      {error ? (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg text-sm font-medium">
          Failed to load payment history logs. Please try again.
        </div>
      ) : history.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center text-slate-500 space-y-2">
          <DollarSign className="w-12 h-12 mx-auto text-slate-300" />
          <p className="font-semibold text-lg">No transactions found</p>
          <p className="text-sm text-slate-400">You haven't initiated any payment transactions yet.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase">
                  <th className="px-6 py-4">Transaction ID</th>
                  <th className="px-6 py-4">Particulars</th>
                  <th className="px-6 py-4">Amount</th>
                  <th className="px-6 py-4">Payment Date</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-center">Receipt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                {history.map((txn: any) => {
                  const isSuccess = txn.status_to_show.toLowerCase() === 'success';
                  const isPending = txn.status_to_show.toLowerCase() === 'pending';
                  const isFailed = !isSuccess && !isPending;
                  
                  return (
                    <tr key={txn.id} className="hover:bg-slate-50/50 transition">
                      <td className="px-6 py-4 font-semibold text-slate-900">{txn.txnid}</td>
                      <td className="px-6 py-4 text-slate-600 font-medium">{txn.productinfo}</td>
                      <td className="px-6 py-4 font-bold text-slate-900">₹{txn.amount}</td>
                      <td className="px-6 py-4 text-xs text-slate-500">
                        {new Date(txn.timestamp).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                          isSuccess ? 'bg-green-100 text-green-800' :
                          isPending ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {txn.status_to_show}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        {isSuccess ? (
                          <button
                            disabled={downloadingId === txn.id}
                            onClick={() => downloadReceipt(txn.id, txn.txnid)}
                            className="p-2 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg transition inline-flex items-center gap-1.5 text-xs font-semibold"
                          >
                            {downloadingId === txn.id ? (
                              <Loader2 size={14} className="animate-spin" />
                            ) : (
                              <Download size={14} />
                            )}{' '}
                            Receipt
                          </button>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
