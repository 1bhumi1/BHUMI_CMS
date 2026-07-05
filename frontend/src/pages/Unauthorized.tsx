import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { useAuth } from '../lib/AuthContext';

const Unauthorized = () => {
  const navigate = useNavigate();
  const { dashboard } = useAuth();

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-slate-50 p-6">
      <div className="w-24 h-24 bg-red-100 text-red-500 rounded-full flex items-center justify-center mb-6">
        <ShieldAlert size={48} />
      </div>
      <h1 className="text-3xl font-bold text-slate-800 mb-2">Access Denied</h1>
      <p className="text-slate-500 mb-8 max-w-md text-center">
        You do not have the necessary permissions to access this page. Please return to your designated dashboard.
      </p>
      <button 
        onClick={() => navigate(dashboard || '/dashboard', { replace: true })}
        className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
      >
        Return to Dashboard
      </button>
    </div>
  );
};

export default Unauthorized;
