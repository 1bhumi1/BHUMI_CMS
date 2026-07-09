import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../lib/AuthContext';
import { 
  LogOut, LayoutDashboard, Users, BookOpen, Settings,
  Shield, FileText, ClipboardList, BookMarked,
  DollarSign, FileSpreadsheet, Key, GraduationCap, Library, UserCircle,
  ChevronDown, ChevronRight, Briefcase, School, Building2, Calendar, Plus
} from 'lucide-react';

const SidebarItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => {
  const location = useLocation();
  const toPath = to.split('?')[0];
  const toQuery = to.includes('?') ? to.split('?')[1] : '';
  const currentQuery = location.search.replace('?', '');
  const isActive = location.pathname === toPath && currentQuery === toQuery;

  return (
    <NavLink
      to={to}
      end
      className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
        isActive 
          ? 'bg-blue-600 text-white shadow-md' 
          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
      }`}
    >
      <Icon size={18} />
      <span className="font-medium text-sm">{label}</span>
    </NavLink>
  );
};

const SidebarGroup = ({ icon: Icon, label, children, activePrefixes = [] }: { icon: any, label: string, children: React.ReactNode, activePrefixes?: string[] }) => {
  const location = useLocation();
  const isActiveGroup = activePrefixes.some(prefix => location.pathname.includes(prefix));
  const [isOpen, setIsOpen] = useState(isActiveGroup);

  return (
    <div className="mb-1">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between px-4 py-2.5 rounded-lg transition-colors ${
          isOpen ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
        }`}
      >
        <div className="flex items-center gap-3">
          <Icon size={18} />
          <span className="font-medium text-sm">{label}</span>
        </div>
        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>
      {isOpen && (
        <div className="mt-1 ml-4 pl-2 border-l border-slate-700 space-y-1">
          {children}
        </div>
      )}
    </div>
  );
};

const Sidebar = () => {
  const { role, isAdmin, isStaff, isStudent, hasPermission, logout } = useAuth();

  return (
    <aside className="w-64 bg-slate-900 min-h-screen text-slate-300 flex flex-col shadow-xl flex-shrink-0 z-20 overflow-hidden">
      <div className="h-16 flex items-center px-6 border-b border-slate-800 shrink-0">
        <h1 className="text-xl font-bold text-white tracking-wider flex items-center gap-2">
          <BookOpen className="text-blue-500" /> CMS
        </h1>
      </div>
      
      <div className="flex-1 overflow-y-auto py-6 px-3 space-y-2">
        
        {/* ===================== ADMIN DASHBOARD ===================== */}
        {isAdmin() && (
          <>
            <SidebarItem to="/dashboard/admin" icon={LayoutDashboard} label="Dashboard" />
            <SidebarItem to="/dashboard/admin/feedback" icon={ClipboardList} label="360 Degree Feedback" />
            
            <SidebarGroup icon={Briefcase} label="Management" activePrefixes={['/admin/users', '/admin/staff', '/admin/students']}>
              <SidebarItem to="/dashboard/admin/users" icon={Users} label="Users" />
              <SidebarItem to="/dashboard/admin/staff" icon={Shield} label="Staff" />
              <SidebarItem to="/dashboard/admin/students" icon={GraduationCap} label="Students" />
            </SidebarGroup>
            
            <SidebarGroup icon={BookMarked} label="Academics" activePrefixes={['/admin/academics']}>
              <SidebarItem to="/dashboard/admin/academics/institutes" icon={School} label="Institutes" />
              <SidebarItem to="/dashboard/admin/academics/departments" icon={Building2} label="Departments" />
              <SidebarItem to="/dashboard/admin/academics/programs" icon={BookOpen} label="Programs" />
              <SidebarItem to="/dashboard/admin/academics/specializations" icon={GraduationCap} label="Specializations" />
              <SidebarItem to="/dashboard/admin/academics/academic-programs" icon={Library} label="Academic Programs" />
              <SidebarItem to="/dashboard/admin/academics/academic-sessions" icon={ClipboardList} label="Sessions" />
              <SidebarItem to="/dashboard/admin/academics/academic-terms" icon={Calendar} label="Terms" />
            </SidebarGroup>
            
            <SidebarGroup icon={Calendar} label="Leave Management" activePrefixes={['/admin/leave']}>
              <SidebarItem to="/dashboard/admin/leave/limits" icon={Settings} label="Leave Limits" />
              <SidebarItem to="/dashboard/admin/leave/reports" icon={FileSpreadsheet} label="Leave Reports" />
            </SidebarGroup>
            
            <SidebarGroup icon={Settings} label="System" activePrefixes={['/admin/roles', '/admin/permissions', '/admin/reports', '/admin/audit', '/admin/settings']}>
              <SidebarItem to="/dashboard/admin/roles" icon={Key} label="Roles" />
              <SidebarItem to="/dashboard/admin/permissions" icon={Shield} label="Permissions" />
              <SidebarItem to="/dashboard/admin/reports" icon={FileSpreadsheet} label="Reports" />
              <SidebarItem to="/dashboard/admin/audit" icon={FileText} label="Audit Logs" />
              <SidebarItem to="/dashboard/admin/settings" icon={Settings} label="Settings" />
            </SidebarGroup>
          </>
        )}

        {/* ===================== STAFF DASHBOARD ===================== */}
        {isStaff() && (
          <>
            <SidebarItem to="/dashboard/staff" icon={LayoutDashboard} label="Dashboard" />
            {role !== 'Principal' && (
              <SidebarItem to="/dashboard/staff/academics/events" icon={Calendar} label="Events & Workshops" />
            )}
            {role !== 'Principal' && (
              <SidebarItem to="/dashboard/staff/feedback" icon={ClipboardList} label="360 Degree Feedback" />
            )}
            {role === 'HOD' && (
              <SidebarGroup icon={Shield} label="HOD Feedback Review" activePrefixes={['/staff/feedback']}>
                <SidebarItem to="/dashboard/staff/feedback?view=review" icon={ClipboardList} label="Staff Review" />
                <SidebarItem to="/dashboard/staff/feedback?view=staff-review" icon={Users} label="Full Details" />
              </SidebarGroup>
            )}
            {role === 'HOD' && (
              <SidebarGroup icon={BookOpen} label="Academics" activePrefixes={['/staff/academics/schema', '/staff/academics/event-management']}>
                <SidebarGroup icon={Settings} label="Schema" activePrefixes={['/staff/academics/schema']}>
                  <SidebarItem to="/dashboard/staff/academics/schema/add-subject" icon={BookMarked} label="Add Subject" />
                  <SidebarItem to="/dashboard/staff/academics/schema/add-subject-credit" icon={DollarSign} label="Add Subject Credit" />
                </SidebarGroup>
                <SidebarGroup icon={Calendar} label="Event Management" activePrefixes={['/staff/academics/event-management']}>
                  <SidebarItem to="/dashboard/staff/academics/event-management/create" icon={Plus} label="Create Event" />
                  <SidebarItem to="/dashboard/staff/academics/event-management/manage" icon={Settings} label="Manage Events" />
                  <SidebarItem to="/dashboard/staff/academics/event-management/registrations" icon={ClipboardList} label="Registrations" />
                </SidebarGroup>
              </SidebarGroup>
            )}
            {role === 'Principal' && (
              <>
                <SidebarGroup icon={Shield} label="Principal Feedback Review" activePrefixes={['/staff/feedback']}>
                  <SidebarItem to="/dashboard/staff/feedback?view=principal" icon={ClipboardList} label="HOD Review" />
                  <SidebarItem to="/dashboard/staff/feedback?view=staff-review" icon={Users} label="Full Details" />
                </SidebarGroup>
                <SidebarItem to="/dashboard/staff/academics/event-management/reports" icon={FileSpreadsheet} label="Event Reports" />
              </>
            )}
            
            <SidebarGroup icon={Briefcase} label="Management" activePrefixes={['/staff/students', '/staff/faculty']}>
              {hasPermission('student.read') && (
                <SidebarItem to="/dashboard/staff/students" icon={GraduationCap} label="Students" />
              )}
              {hasPermission('faculty.read') && (
                <SidebarItem to="/dashboard/staff/faculty" icon={Users} label="Faculty" />
              )}
            </SidebarGroup>

            <SidebarGroup icon={BookMarked} label="Academics & Operations" activePrefixes={['/staff/attendance', '/staff/marks', '/staff/fees', '/staff/library', '/staff/departments']}>
              {hasPermission('attendance.manage') && (
                <SidebarItem to="/dashboard/staff/attendance" icon={ClipboardList} label="Attendance" />
              )}
              {hasPermission('exam.manage') && (
                <SidebarItem to="/dashboard/staff/marks" icon={FileText} label="Marks / Results" />
              )}
              {hasPermission('fees.manage') && (
                <SidebarItem to="/dashboard/staff/fees" icon={DollarSign} label="Fees" />
              )}
              {hasPermission('library.manage') && (
                <SidebarItem to="/dashboard/staff/library" icon={Library} label="Library" />
              )}
              <SidebarItem to="/dashboard/staff/departments" icon={Building2} label="Departments" />
            </SidebarGroup>

            <SidebarGroup icon={Calendar} label="Leave Management" activePrefixes={['/staff/leave']}>
              <SidebarItem to="/dashboard/staff/leave" icon={LayoutDashboard} label="Leave Dashboard" />
              <SidebarItem to="/dashboard/staff/leave/my-leaves" icon={FileText} label="My Leaves" />
              <SidebarItem to="/dashboard/staff/leave/pending" icon={ClipboardList} label="Pending Approval" />
              {hasPermission('leave.balance.read') && (
                <SidebarItem to="/dashboard/staff/leave/balance" icon={ClipboardList} label="Leave Balance" />
              )}
              {hasPermission('leave.assignment.manage') && (
                <SidebarItem to="/dashboard/staff/leave/faculty-assignment" icon={Users} label="Faculty Assignment" />
              )}
            </SidebarGroup>

            <SidebarItem to="/dashboard/staff/reports" icon={FileSpreadsheet} label="Reports" />
          </>
        )}

        {/* ===================== STUDENT DASHBOARD ===================== */}
        {isStudent() && (
          <>
            <SidebarItem to="/dashboard/student" icon={LayoutDashboard} label="Dashboard" />
            <SidebarItem to="/dashboard/student/profile" icon={UserCircle} label="Profile" />
            <SidebarGroup icon={BookMarked} label="Academics" activePrefixes={['/student/attendance', '/student/timetable', '/student/results', '/student/events']}>
              <SidebarItem to="/dashboard/student/attendance" icon={ClipboardList} label="Attendance" />
              <SidebarItem to="/dashboard/student/timetable" icon={BookOpen} label="Timetable" />
              <SidebarItem to="/dashboard/student/results" icon={FileText} label="Results" />
              <SidebarItem to="/dashboard/student/events" icon={Calendar} label="Events & Workshops" />
            </SidebarGroup>
            
            <SidebarGroup icon={DollarSign} label="Fees" activePrefixes={['/student/fees']}>
              <SidebarItem to="/dashboard/student/fees/pending" icon={ClipboardList} label="Pending Payments" />
              <SidebarItem to="/dashboard/student/fees/history" icon={FileText} label="Payment History" />
              <SidebarItem to="/dashboard/student/fees/history" icon={FileSpreadsheet} label="Receipts" />
            </SidebarGroup>
            
            <SidebarItem to="/dashboard/student/documents" icon={FileSpreadsheet} label="Documents" />
          </>
        )}

      </div>
      
      <div className="p-4 border-t border-slate-800 shrink-0">
        <button 
          onClick={logout}
          className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-slate-300 hover:bg-red-500/10 hover:text-red-500 transition-colors"
        >
          <LogOut size={18} />
          <span className="font-medium text-sm">Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
