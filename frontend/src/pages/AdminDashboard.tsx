import React, { useState, useEffect } from 'react';
import { useAuth } from '../lib/AuthContext';
import { Users, BookOpen, Shield, ShieldCheck, LogIn, Loader2 } from 'lucide-react';
import { api } from '../lib/api';
import { useNavigate } from 'react-router-dom';

const AdminDashboard = () => {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  
  const [students, setStudents] = useState<any[]>([]);
  const [staff, setStaff] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [impersonatingId, setImpersonatingId] = useState<number | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [studentRes, staffRes] = await Promise.all([
          api.get('/students?limit=10&sort_by=id&sort_order=desc'),
          api.get('/staff?limit=10&sort_by=id&sort_order=desc')
        ]);
        setStudents(studentRes.data?.data || []);
        setStaff(staffRes.data?.data?.items || []);
      } catch (err) {
        console.error("Failed to fetch users for impersonation", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleImpersonate = async (userId: number, role: string) => {
    try {
      setImpersonatingId(userId);
      const res = await api.post('/rbac/impersonate/start', {
        target_user_id: userId,
        target_role: role,
        reason: 'Admin support session'
      });
      
      if (res.data?.data) {
        login(res.data.data);
        if (role === 'student') navigate('/dashboard/student');
        else if (role === 'staff') navigate('/dashboard/staff');
      }
    } catch (err) {
      console.error("Impersonation failed", err);
      alert("Failed to start impersonation session. Check console for details.");
    } finally {
      setImpersonatingId(null);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Admin Dashboard</h1>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-800 mb-2">Welcome back, {user?.name}</h2>
        <p className="text-slate-500">System administration and overview.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Statistics Widgets */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4">
          <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
            <Users size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Total Users</p>
            <p className="text-2xl font-bold text-slate-800">1,248</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center">
            <BookOpen size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Departments</p>
            <p className="text-2xl font-bold text-slate-800">6</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center">
            <Shield size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Roles</p>
            <p className="text-2xl font-bold text-slate-800">9</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4">
          <div className="w-12 h-12 bg-orange-100 text-orange-600 rounded-lg flex items-center justify-center">
            <ShieldCheck size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">System Health</p>
            <p className="text-2xl font-bold text-slate-800">100%</p>
          </div>
        </div>
      </div>

      {/* Impersonation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        
        {/* Students Table */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
            <h3 className="font-semibold text-slate-800">Recent Students</h3>
          </div>
          <div className="p-0">
            {loading ? (
              <div className="p-8 flex justify-center text-slate-400">
                <Loader2 className="animate-spin" />
              </div>
            ) : students.length > 0 ? (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 bg-white">
                    <th className="px-6 py-3 font-medium">Name</th>
                    <th className="px-6 py-3 font-medium">Code</th>
                    <th className="px-6 py-3 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((student) => (
                    <tr key={student.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                      <td className="px-6 py-3 font-medium text-slate-800">{student.first_name} {student.last_name}</td>
                      <td className="px-6 py-3 text-slate-500">{student.computer_code}</td>
                      <td className="px-6 py-3 text-right">
                        <button
                          onClick={() => handleImpersonate(student.id, 'student')}
                          disabled={impersonatingId === student.id}
                          className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-md transition-colors disabled:opacity-50"
                        >
                          {impersonatingId === student.id ? <Loader2 size={14} className="animate-spin" /> : <LogIn size={14} />}
                          Login As
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-slate-500">No students found</div>
            )}
          </div>
        </div>

        {/* Staff Table */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
            <h3 className="font-semibold text-slate-800">Recent Staff</h3>
          </div>
          <div className="p-0">
            {loading ? (
              <div className="p-8 flex justify-center text-slate-400">
                <Loader2 className="animate-spin" />
              </div>
            ) : staff.length > 0 ? (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 bg-white">
                    <th className="px-6 py-3 font-medium">Name</th>
                    <th className="px-6 py-3 font-medium">Department</th>
                    <th className="px-6 py-3 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {staff.map((s) => (
                    <tr key={s.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                      <td className="px-6 py-3 font-medium text-slate-800">{s.first_name} {s.last_name}</td>
                      <td className="px-6 py-3 text-slate-500">{s.department?.department_name || 'N/A'}</td>
                      <td className="px-6 py-3 text-right">
                        <button
                          onClick={() => handleImpersonate(s.id, 'staff')}
                          disabled={impersonatingId === s.id}
                          className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-600 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 rounded-md transition-colors disabled:opacity-50"
                        >
                          {impersonatingId === s.id ? <Loader2 size={14} className="animate-spin" /> : <LogIn size={14} />}
                          Login As
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-slate-500">No staff found</div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default AdminDashboard;
