import { api } from './api';

export interface FacultyAssignmentRequest {
  faculty_date: string;
  faculty_computer_code: number;
  assigned_class_dept: string;
  assigned_section: string;
  lecture_type: string;
  start_time: string;
  end_time: string;
  other_responsibility: string;
}

export interface LeaveCreate {
  session?: string;
  start_date: string;
  end_date: string;
  days: number;
  leave_type: string;
  reason: string;
  assignments?: FacultyAssignmentRequest[];
}

export const lmsApi = {
  applyLeave: async (data: LeaveCreate) => {
    const res = await api.post('/leave/apply', data);
    return res.data;
  },
  getMyLeaves: async () => {
    const res = await api.get('/leave/my-leaves');
    return res.data;
  },
  getPendingLeaves: async () => {
    const res = await api.get('/leave/pending');
    return res.data;
  },
  approveLeave: async (id: string, status: number, actionType: string = 'HOD') => {
    const res = await api.put(`/leave/${id}/approve?action_type=${actionType}`, { status });
    return res.data;
  },
  rejectLeave: async (id: string, status: number, actionType: string = 'HOD') => {
    const res = await api.put(`/leave/${id}/reject?action_type=${actionType}`, { status });
    return res.data;
  },
  getLeaveBalance: async (session: number) => {
    const res = await api.get(`/leave/balance?session=${session}`);
    return res.data;
  },
  getLeaveLimits: async () => {
    const res = await api.get('/leave/limits');
    return res.data;
  },
  getAssignableStaff: async () => {
    const res = await api.get('/leave/staff');
    return res.data;
  },
  getSessions: async () => {
    const res = await api.get('/academic/academic-sessions');
    return res.data;
  }
};
