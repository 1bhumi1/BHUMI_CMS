import React from 'react';
import { useAuth } from '../lib/AuthContext';
import PermissionGuard from '../components/PermissionGuard';
import { Users, GraduationCap, ClipboardList, BookOpen, DollarSign } from 'lucide-react';

const StaffDashboard = () => {
  const { user, department } = useAuth();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Staff Dashboard</h1>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-800 mb-2">Welcome, {user?.name}</h2>
        <p className="text-slate-500">
          Department: <span className="font-medium text-slate-700">{department || 'Not assigned'}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        <PermissionGuard permission="student.read">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-blue-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
              <GraduationCap size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Students</p>
              <p className="text-xl font-bold text-slate-800">Manage</p>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard permission="faculty.read">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-emerald-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center">
              <Users size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Faculty</p>
              <p className="text-xl font-bold text-slate-800">Directory</p>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard permission="attendance.manage">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-amber-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-lg flex items-center justify-center">
              <ClipboardList size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Attendance</p>
              <p className="text-xl font-bold text-slate-800">Record</p>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard permission="exam.manage">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-purple-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center">
              <BookOpen size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Marks</p>
              <p className="text-xl font-bold text-slate-800">Entry</p>
            </div>
          </div>
        </PermissionGuard>

        <PermissionGuard permission="fees.manage">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex items-center gap-4 hover:border-green-300 transition-colors cursor-pointer">
            <div className="w-12 h-12 bg-green-100 text-green-600 rounded-lg flex items-center justify-center">
              <DollarSign size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Fees</p>
              <p className="text-xl font-bold text-slate-800">Collection</p>
            </div>
          </div>
        </PermissionGuard>

      </div>
    </div>
  );
};

export default StaffDashboard;
