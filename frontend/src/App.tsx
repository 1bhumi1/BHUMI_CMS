import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './lib/AuthContext';
import { Loader2 } from 'lucide-react';
import { AcademicSessionProvider } from './lib/AcademicSessionContext';

// Eager load core components
import Login from './pages/Login';
import Unauthorized from './pages/Unauthorized';
import ProtectedRoute from './components/ProtectedRoute';
import RoleRouter from './components/RoleRouter';
import Layout from './components/Layout';

// Lazy load Dashboard Pages
const AdminDashboard = React.lazy(() => import('./pages/AdminDashboard'));
const StaffDashboard = React.lazy(() => import('./pages/StaffDashboard'));
const StudentDashboard = React.lazy(() => import('./pages/StudentDashboard'));

// Lazy load Management Pages
const StaffManagement = React.lazy(() => import('./pages/StaffManagement'));
const StudentManagement = React.lazy(() => import('./pages/StudentManagement'));

// Lazy load Academics Pages
const InstitutesPage = React.lazy(() => import('./pages/academics/InstitutesPage'));
const DepartmentsPage = React.lazy(() => import('./pages/academics/DepartmentsPage'));
const ProgramsPage = React.lazy(() => import('./pages/academics/ProgramsPage'));
const SpecializationsPage = React.lazy(() => import('./pages/academics/SpecializationsPage'));
const AcademicProgramsPage = React.lazy(() => import('./pages/academics/AcademicProgramsPage'));
const AcademicSessionsPage = React.lazy(() => import('./pages/academics/AcademicSessionsPage'));
const AcademicTermsPage = React.lazy(() => import('./pages/academics/AcademicTermsPage'));

// Lazy load LMS Pages
const LeaveDashboard = React.lazy(() => import('./pages/lms/LeaveDashboard'));
const MyLeaves = React.lazy(() => import('./pages/lms/MyLeaves'));
const PendingApproval = React.lazy(() => import('./pages/lms/PendingApproval'));
const LeaveBalance = React.lazy(() => import('./pages/lms/LeaveBalance'));
const LeaveLimits = React.lazy(() => import('./pages/lms/LeaveLimits'));
const FacultyAssignment = React.lazy(() => import('./pages/lms/FacultyAssignment'));
const LeaveReports = React.lazy(() => import('./pages/lms/Reports'));
const Feedback360 = React.lazy(() => import('./pages/Feedback360'));
const AddSubject = React.lazy(() => import('./pages/academics/AddSubject'));
const AddSubjectCredit = React.lazy(() => import('./pages/academics/AddSubjectCredit'));

const PageLoader = () => (
  <div className="flex-1 flex items-center justify-center min-h-[50vh]">
    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AcademicSessionProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/unauthorized" element={<Unauthorized />} />
            
            <Route element={<ProtectedRoute />}>
              {/* 
                RoleRouter automatically redirects /dashboard to the correct sub-dashboard
                based on the user's role
              */}
              <Route path="/dashboard" element={<RoleRouter />}>
                <Route element={<Layout />}>
                  <Route path="admin" element={<Suspense fallback={<PageLoader />}><AdminDashboard /></Suspense>} />
                  <Route path="admin/staff" element={<Suspense fallback={<PageLoader />}><StaffManagement /></Suspense>} />
                  <Route path="admin/students" element={<Suspense fallback={<PageLoader />}><StudentManagement /></Suspense>} />
                  
                  {/* Academics nested routes */}
                  <Route path="admin/academics/institutes" element={<Suspense fallback={<PageLoader />}><InstitutesPage /></Suspense>} />
                  <Route path="admin/academics/departments" element={<Suspense fallback={<PageLoader />}><DepartmentsPage /></Suspense>} />
                  <Route path="admin/academics/programs" element={<Suspense fallback={<PageLoader />}><ProgramsPage /></Suspense>} />
                  <Route path="admin/academics/specializations" element={<Suspense fallback={<PageLoader />}><SpecializationsPage /></Suspense>} />
                  <Route path="admin/academics/academic-programs" element={<Suspense fallback={<PageLoader />}><AcademicProgramsPage /></Suspense>} />
                  <Route path="admin/academics/academic-sessions" element={<Suspense fallback={<PageLoader />}><AcademicSessionsPage /></Suspense>} />
                  <Route path="admin/academics/academic-terms" element={<Suspense fallback={<PageLoader />}><AcademicTermsPage /></Suspense>} />

                  {/* Admin LMS Routes */}
                  <Route path="admin/leave/limits" element={<Suspense fallback={<PageLoader />}><LeaveLimits /></Suspense>} />
                  <Route path="admin/leave/reports" element={<Suspense fallback={<PageLoader />}><LeaveReports /></Suspense>} />
                  <Route path="admin/feedback" element={<Suspense fallback={<PageLoader />}><Feedback360 /></Suspense>} />

                  <Route path="staff" element={<Suspense fallback={<PageLoader />}><StaffDashboard /></Suspense>} />
                  
                  {/* Staff LMS Routes */}
                  <Route path="staff/leave" element={<Suspense fallback={<PageLoader />}><LeaveDashboard /></Suspense>} />
                  <Route path="staff/leave/my-leaves" element={<Suspense fallback={<PageLoader />}><MyLeaves /></Suspense>} />
                  <Route path="staff/leave/pending" element={<Suspense fallback={<PageLoader />}><PendingApproval /></Suspense>} />
                  <Route path="staff/leave/balance" element={<Suspense fallback={<PageLoader />}><LeaveBalance /></Suspense>} />
                  <Route path="staff/leave/faculty-assignment" element={<Suspense fallback={<PageLoader />}><FacultyAssignment /></Suspense>} />
                  <Route path="staff/reports" element={<Suspense fallback={<PageLoader />}><LeaveReports /></Suspense>} />
                  <Route path="staff/feedback" element={<Suspense fallback={<PageLoader />}><Feedback360 /></Suspense>} />
                  <Route path="staff/academics/schema/add-subject" element={<Suspense fallback={<PageLoader />}><AddSubject /></Suspense>} />
                  <Route path="staff/academics/schema/add-subject-credit" element={<Suspense fallback={<PageLoader />}><AddSubjectCredit /></Suspense>} />

                  <Route path="student" element={<Suspense fallback={<PageLoader />}><StudentDashboard /></Suspense>} />
                </Route>
              </Route>
            </Route>
            
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </AcademicSessionProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
