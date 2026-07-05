import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { useAuth } from '../lib/AuthContext';
import { AlertTriangle, LogOut } from 'lucide-react';
import { api } from '../lib/api';

const Layout = () => {
  const { isImpersonating, originalUser, user, login } = useAuth();
  const navigate = useNavigate();
  const [isExiting, setIsExiting] = useState(false);

  const handleExitImpersonation = async () => {
    try {
      setIsExiting(true);
      const res = await api.post('/rbac/impersonate/stop');
      if (res.data?.data) {
        login(res.data.data);
        navigate('/dashboard/admin');
      }
    } catch (err) {
      console.error("Failed to exit impersonation", err);
    } finally {
      setIsExiting(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-slate-50 overflow-hidden">
      {isImpersonating && (
        <div className="bg-amber-500 text-white px-4 py-2 flex items-center justify-between shrink-0 z-50 shadow-md">
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} className="text-white" />
            <span className="font-bold tracking-wider text-sm">IMPERSONATION MODE</span>
            <span className="px-2 border-l border-amber-400 text-sm">
              You are currently logged in as <strong>{user?.name}</strong>
            </span>
            <span className="px-2 border-l border-amber-400 text-sm">
              Original User: <strong>{originalUser}</strong>
            </span>
          </div>
          <button 
            onClick={handleExitImpersonation}
            disabled={isExiting}
            className="flex items-center gap-2 bg-amber-700 hover:bg-amber-800 transition-colors px-3 py-1.5 rounded text-sm font-medium disabled:opacity-70"
          >
            <LogOut size={16} />
            {isExiting ? 'Exiting...' : 'Exit Impersonation'}
          </button>
        </div>
      )}
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden relative">
          <Topbar />
          <main className="flex-1 overflow-y-auto p-6 relative">
            <div className="max-w-7xl mx-auto">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default Layout;
