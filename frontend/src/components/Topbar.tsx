import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../lib/AuthContext';
import { Bell, User, Trash2, CheckSquare, Calendar, ChevronDown } from 'lucide-react';
import { api } from '../lib/api';
import { useLocation } from 'react-router-dom';
import { useAcademicSession } from '../lib/AcademicSessionContext';

interface NotificationItem {
  id: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

const Topbar = () => {
  const { user, role } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const location = useLocation();
  const { currentSession, setSession } = useAcademicSession();
  const [isSessionOpen, setIsSessionOpen] = useState(false);
  const sessionDropdownRef = useRef<HTMLDivElement>(null);

  const isAcademicsPage = location.pathname.includes('academics');

  const SESSIONS = [
    '2025-2026 (July-Dec)',
    '2025-2026 (Jan-Jun)',
    '2026-2027 (July-Dec)',
    '2026-2027 (Jan-Jun)'
  ];

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications/');
      if (res.data?.success) {
        setNotifications(res.data.data || []);
      }
    } catch (e) {
      console.error("Failed to fetch notifications", e);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Poll for notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle click outside to close dropdowns
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
      if (sessionDropdownRef.current && !sessionDropdownRef.current.contains(event.target as Node)) {
        setIsSessionOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markAllAsRead = async () => {
    try {
      const res = await api.post('/notifications/read-all');
      if (res.data?.success) {
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const markAsRead = async (id: number) => {
    try {
      const res = await api.post(`/notifications/${id}/read`);
      if (res.data?.success) {
        setNotifications(prev =>
          prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
        );
      }
    } catch (e) {
      console.error(e);
    }
  };

  const deleteNotification = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      const res = await api.delete(`/notifications/${id}`);
      if (res.data?.success) {
        setNotifications(prev => prev.filter(n => n.id !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-10">
      <div className="flex items-center gap-4">
        {/* Search or breadcrumbs can go here */}
      </div>

      <div className="flex items-center gap-6">
        {/* Academic Session Selector */}
        <div className="relative font-sans" ref={sessionDropdownRef}>
          <button
            onClick={() => setIsSessionOpen(!isSessionOpen)}
            className="flex items-center gap-2 px-3.5 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 hover:border-slate-350 rounded-xl text-xs font-bold text-slate-700 transition-all active:scale-98 shadow-sm"
          >
            <Calendar size={14} className="text-slate-500" />
            <span>{currentSession}</span>
            <ChevronDown size={14} className="text-slate-400" />
          </button>

          {isSessionOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white border border-slate-200 rounded-xl shadow-lg z-50 py-1.5 overflow-hidden">
              {SESSIONS.map(session => (
                <button
                  key={session}
                  onClick={() => {
                    setSession(session);
                    setIsSessionOpen(false);
                  }}
                  className={`w-full text-left px-4 py-2 text-xs font-semibold hover:bg-slate-50 transition-colors ${
                    currentSession === session ? 'text-indigo-600 bg-indigo-50/20' : 'text-slate-700'
                  }`}
                >
                  {session}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Notification Bell Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="text-slate-400 hover:text-indigo-600 transition-colors relative p-2 rounded-full hover:bg-slate-50 flex items-center justify-center"
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 bg-red-500 rounded-full text-[9px] font-bold text-white flex items-center justify-center px-1">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Dropdown Panel */}
          {isOpen && (
            <div className="absolute right-0 mt-2.5 w-80 bg-white border border-slate-200 rounded-2xl shadow-xl z-50 overflow-hidden">
              <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                <span className="font-extrabold text-slate-800 text-xs uppercase tracking-wider">Notifications</span>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-[10px] text-indigo-600 hover:text-indigo-800 font-extrabold flex items-center gap-1 transition-colors"
                  >
                    <CheckSquare size={12} /> Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-400 font-medium">
                    No new notifications.
                  </div>
                ) : (
                  notifications.map(n => (
                    <div
                      key={n.id}
                      onClick={() => !n.is_read && markAsRead(n.id)}
                      className={`p-3.5 flex items-start justify-between gap-2.5 transition-colors cursor-pointer ${
                        n.is_read ? 'hover:bg-slate-50 bg-white' : 'bg-indigo-50/20 hover:bg-indigo-50/40'
                      }`}
                    >
                      <div className="flex-1 space-y-1">
                        <p className={`text-xs leading-relaxed ${n.is_read ? 'text-slate-500 font-medium' : 'text-slate-800 font-semibold'}`}>
                          {n.message}
                        </p>
                        <span className="text-[9px] text-slate-400 block font-semibold">
                          {new Date(n.created_at).toLocaleDateString('en-GB', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {!n.is_read && (
                          <span className="w-1.5 h-1.5 bg-indigo-600 rounded-full flex-shrink-0"></span>
                        )}
                        <button
                          onClick={(e) => deleteNotification(e, n.id)}
                          className="text-slate-300 hover:text-red-500 transition-colors p-1 rounded hover:bg-slate-100"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 border-l pl-6 border-slate-200">
          <div className="text-right hidden md:block">
            <p className="text-sm font-semibold text-slate-700">{user?.name || 'User'}</p>
            <p className="text-xs text-slate-500">{role || 'Role'}</p>
          </div>
          <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
            <User size={18} />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
