import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../../lib/api';
import { useAuth } from '../../../lib/AuthContext';
import { 
  DollarSign, TrendingUp, Search, Loader2, ArrowRightLeft, 
  Download, FileSpreadsheet, FileText, AlertCircle, Calendar
} from 'lucide-react';

export default function AccountantDashboard() {
  const { role } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);
  const limit = 10;

  // Load metrics stats
  const { data: statsRes, isLoading: loadingStats } = useQuery({
    queryKey: ['accountant-stats'],
    queryFn: async () => {
      const res = await api.get('/payments/accountant/stats');
      return res.data?.data;
    }
  });

  // Load transaction list
  const { data: listRes, isLoading: loadingList, error, refetch } = useQuery({
    queryKey: ['accountant-transactions', searchTerm, statusFilter, page],
    queryFn: async () => {
      const res = await api.get(`/payments/accountant/transactions?search=${searchTerm}&status=${statusFilter}&skip=${page * limit}&limit=${limit}`);
      return res.data?.data || [];
    }
  });

  const handleExport = async (format: 'csv' | 'pdf') => {
    try {
      const response = await api.get(`/payments/accountant/export/${format}?search=${searchTerm}&status=${statusFilter}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Transactions_Report_${new Date().toISOString().slice(0,10)}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (e) {
      alert('Failed to export transactions log.');
    }
  };

  if (loadingStats) {
    return (
      <div className="flex justify-center items-center py-24">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <DollarSign className="text-blue-600" /> Fees & Payments Dashboard
        </h1>
        <p className="text-sm text-slate-500">Track and monitor college revenue collection, search transactions, and export reports</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
        {/* Total Revenue */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-3">
          <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
            <TrendingUp size={20} />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Revenue</p>
            <p className="text-xl font-bold text-slate-800">₹{statsRes?.total_revenue?.toLocaleString('en-IN')}</p>
          </div>
        </div>

        {/* Success Payments */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-3">
          <div className="w-10 h-10 bg-green-100 text-green-600 rounded-lg flex items-center justify-center">
            <DollarSign size={20} />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Success Transactions</p>
            <p className="text-xl font-bold text-slate-800">{statsRes?.success_count}</p>
          </div>
        </div>

        {/* Pending Payments */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-3">
          <div className="w-10 h-10 bg-yellow-100 text-yellow-600 rounded-lg flex items-center justify-center">
            <ArrowRightLeft size={20} />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pending Dues</p>
            <p className="text-xl font-bold text-slate-800">{statsRes?.pending_count}</p>
          </div>
        </div>

        {/* Failed Payments */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-3">
          <div className="w-10 h-10 bg-red-100 text-red-600 rounded-lg flex items-center justify-center">
            <AlertCircle size={20} />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Failed Payment attempts</p>
            <p className="text-xl font-bold text-slate-800">{statsRes?.failed_count}</p>
          </div>
        </div>

        {/* Refunded */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-3">
          <div className="w-10 h-10 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center">
            <ArrowRightLeft size={20} />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Refunded</p>
            <p className="text-xl font-bold text-slate-800">{statsRes?.refunded_count}</p>
          </div>
        </div>
      </div>

      {/* Toolbar / Search Filters */}
      <div className="flex flex-col sm:flex-row bg-white rounded-lg p-4 shadow-sm border border-slate-200 gap-4 items-center justify-between">
        <div className="flex flex-1 gap-3 w-full max-w-xl">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 text-slate-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search by Txn ID, name, roll no, item..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(0);
              }}
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(0);
            }}
            className="border border-slate-300 rounded-lg text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="">All Statuses</option>
            <option value="Success">Success</option>
            <option value="Pending">Pending</option>
            <option value="Failed">Failed</option>
          </select>
        </div>

        <div className="flex gap-2 w-full sm:w-auto">
          <button
            onClick={() => handleExport('csv')}
            className="flex-1 sm:flex-none px-3.5 py-2 border border-slate-300 rounded-lg text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 transition flex items-center justify-center gap-1.5"
          >
            <FileSpreadsheet size={14} className="text-green-600" /> Export CSV
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="flex-1 sm:flex-none px-3.5 py-2 border border-slate-300 rounded-lg text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 transition flex items-center justify-center gap-1.5"
          >
            <FileText size={14} className="text-red-500" /> Export PDF
          </button>
        </div>
      </div>

      {/* Transaction Table */}
      <div className="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden">
        {loadingList ? (
          <div className="flex justify-center items-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : listRes.length === 0 ? (
          <div className="p-16 text-center text-slate-500 space-y-2">
            <Calendar className="w-12 h-12 mx-auto text-slate-300" />
            <p className="font-semibold text-lg">No transactions found</p>
            <p className="text-sm text-slate-400">There are no transaction records matching the current filters.</p>
          </div>
        ) : (
          <div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase">
                    <th className="px-6 py-4">Transaction ID</th>
                    <th className="px-6 py-4">Student</th>
                    <th className="px-6 py-4">Particulars</th>
                    <th className="px-6 py-4">Amount</th>
                    <th className="px-6 py-4">Date</th>
                    <th className="px-6 py-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                  {listRes.map((txn: any) => {
                    const isSuccess = txn.status_to_show.toLowerCase() === 'success';
                    const isPending = txn.status_to_show.toLowerCase() === 'pending';
                    
                    return (
                      <tr key={txn.id} className="hover:bg-slate-50/50 transition">
                        <td className="px-6 py-4 font-semibold text-slate-900">{txn.txnid}</td>
                        <td className="px-6 py-4">
                          <p className="font-medium text-slate-800">{txn.firstname}</p>
                          <p className="text-xs text-slate-500">Roll No: {txn.computer_code}</p>
                        </td>
                        <td className="px-6 py-4 text-slate-600 font-medium">{txn.productinfo}</td>
                        <td className="px-6 py-4 font-bold text-slate-900">₹{txn.amount}</td>
                        <td className="px-6 py-4 text-xs text-slate-500">
                          {new Date(txn.timestamp).toLocaleDateString('en-IN', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric'
                          })}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                            isSuccess ? 'bg-green-100 text-green-800' :
                            isPending ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {txn.status_to_show}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Simple Pagination */}
            <div className="bg-slate-50/50 border-t border-slate-150 p-4 flex justify-between items-center text-xs">
              <button
                disabled={page === 0}
                onClick={() => setPage(p => Math.max(0, p - 1))}
                className="px-3 py-1.5 border border-slate-300 rounded-md font-semibold bg-white hover:bg-slate-50 disabled:opacity-50 transition"
              >
                Previous
              </button>
              <span className="text-slate-500 font-medium">Page {page + 1}</span>
              <button
                disabled={listRes.length < limit}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1.5 border border-slate-300 rounded-md font-semibold bg-white hover:bg-slate-50 disabled:opacity-50 transition"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
