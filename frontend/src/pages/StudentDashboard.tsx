import React from 'react';
import { useAuth } from '../lib/AuthContext';
import { BookOpen, Calendar, DollarSign, FileText } from 'lucide-react';

const StudentDashboard = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Student Dashboard</h1>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-800 mb-2">Welcome back, {user?.name}</h2>
        <p className="text-slate-500">
          Roll No: <span className="font-medium text-slate-700">{user?.computer_code}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-4">
          <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
            <Calendar size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Attendance</p>
            <p className="text-2xl font-bold text-slate-800">85%</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-4">
          <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center">
            <FileText size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Current SGPA</p>
            <p className="text-2xl font-bold text-slate-800">8.4</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-4">
          <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-lg flex items-center justify-center">
            <BookOpen size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Classes Today</p>
            <p className="text-2xl font-bold text-slate-800">4</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col gap-4">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center">
            <DollarSign size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Fee Status</p>
            <p className="text-2xl font-bold text-emerald-600">Paid</p>
          </div>
        </div>

      </div>
    </div>
  );
};

export default StudentDashboard;
