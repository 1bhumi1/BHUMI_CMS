import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Check, X, Loader2 } from 'lucide-react';
import { lmsApi } from '../../lib/lms';

export default function PendingApproval() {
  const queryClient = useQueryClient();

  const { data: response, isLoading, isError } = useQuery({
    queryKey: ['pendingLeaves'],
    queryFn: lmsApi.getPendingLeaves
  });

  const leaves = response?.data || [];

  const approveMutation = useMutation({
    mutationFn: ({ id, actionType }: { id: string, actionType: string }) => lmsApi.approveLeave(id, 1, actionType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingLeaves'] });
    }
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, actionType }: { id: string, actionType: string }) => lmsApi.rejectLeave(id, 2, actionType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingLeaves'] });
    }
  });

  if (isLoading) return <div className="p-6 flex items-center justify-center"><Loader2 className="animate-spin w-6 h-6 text-indigo-600" /></div>;
  if (isError) return <div className="p-6 text-red-500">Failed to load pending leaves.</div>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-slate-800">Pending Leave Approvals</h1>
      
      {leaves.length === 0 ? (
        <div className="bg-white p-6 rounded-xl border border-slate-200 text-center text-slate-500">
          No pending leave approvals found.
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-sm font-semibold text-slate-600">
                <th className="p-4">Faculty</th>
                <th className="p-4">Leave Type</th>
                <th className="p-4">Duration</th>
                <th className="p-4">Days</th>
                <th className="p-4">Reason</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {leaves.map((l: any) => {
                const actionType = l.required_action;
                
                let statusBadge = null;
                if (actionType === 'SUBSTITUTE') {
                  statusBadge = <span className="px-2.5 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">Substitute Approval Needed</span>;
                } else if (actionType === 'WAITING_ON_SUBSTITUTE') {
                  statusBadge = <span className="px-2.5 py-1 bg-orange-100 text-orange-700 text-xs font-medium rounded-full">Awaiting Substitute</span>;
                } else if (actionType === 'HOD') {
                  statusBadge = <span className="px-2.5 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded-full">Awaiting HOD</span>;
                } else if (actionType === 'PRINCIPAL') {
                  statusBadge = <span className="px-2.5 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">Awaiting Principal</span>;
                } else {
                  statusBadge = <span className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-medium rounded-full">{actionType || 'Unknown'}</span>;
                }

                return (
                  <React.Fragment key={l.apply_id}>
                    <tr className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                      <td className="p-4 font-medium text-slate-700">
                        <div className="flex flex-col">
                          <span>{l.faculty_name || 'Unknown Faculty'}</span>
                          <span className="text-xs text-slate-500">{l.faculty_computer_code}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="px-2.5 py-1 bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-full uppercase tracking-wider">
                          {l.leave_type}
                        </span>
                      </td>
                      <td className="p-4 text-sm text-slate-600">
                        {new Date(l.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} - {new Date(l.end_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="p-4 text-sm font-medium text-slate-700">{l.days}</td>
                      <td className="p-4 text-sm text-slate-500 max-w-xs truncate" title={l.reason}>
                        {l.reason}
                      </td>
                      <td className="p-4">
                        {statusBadge}
                      </td>
                      <td className="p-4 flex items-center justify-end gap-2">
                        <button
                          onClick={() => approveMutation.mutate({ id: l.apply_id, actionType: actionType })}
                          disabled={approveMutation.isPending || actionType === 'WAITING_ON_SUBSTITUTE'}
                          className={`p-1.5 rounded-lg transition-colors ${actionType === 'WAITING_ON_SUBSTITUTE' ? 'bg-slate-50 text-slate-300 cursor-not-allowed' : 'bg-green-50 text-green-600 hover:bg-green-100'}`}
                          title={actionType === 'WAITING_ON_SUBSTITUTE' ? 'Cannot approve until substitute approves' : `${actionType} Approve`}
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => rejectMutation.mutate({ id: l.apply_id, actionType: actionType })}
                          disabled={rejectMutation.isPending || actionType === 'WAITING_ON_SUBSTITUTE'}
                          className={`p-1.5 rounded-lg transition-colors ${actionType === 'WAITING_ON_SUBSTITUTE' ? 'bg-slate-50 text-slate-300 cursor-not-allowed' : 'bg-red-50 text-red-600 hover:bg-red-100'}`}
                          title={actionType === 'WAITING_ON_SUBSTITUTE' ? 'Cannot reject until substitute approves' : `${actionType} Reject`}
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                    {l.assignments && l.assignments.length > 0 && (
                      <tr className="bg-slate-50/50 border-b border-slate-200">
                        <td colSpan={7} className="p-4">
                          <div className="bg-white rounded-lg border border-slate-200 p-4">
                            <h4 className="text-sm font-semibold text-slate-700 mb-3">Substitute Responsibilities</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {l.assignments.map((assignment: any, index: number) => (
                                <div key={index} className="bg-slate-50 rounded p-3 border border-slate-100 text-sm">
                                  <div className="grid grid-cols-2 gap-2">
                                    <div className="text-slate-500">Date:</div>
                                    <div className="font-medium text-slate-800">{new Date(assignment.faculty_date).toLocaleDateString()}</div>
                                    
                                    <div className="text-slate-500">Time:</div>
                                    <div className="font-medium text-slate-800">{assignment.start_time} - {assignment.end_time}</div>
                                    
                                    <div className="text-slate-500">Class/Dept:</div>
                                    <div className="font-medium text-slate-800">{assignment.assigned_class_dept} {assignment.assigned_section ? `(Sec: ${assignment.assigned_section})` : ''}</div>
                                    
                                    <div className="text-slate-500">Lecture Type:</div>
                                    <div className="font-medium text-slate-800">{assignment.lecture_type || 'N/A'}</div>
                                    
                                    {assignment.other_responsibility && (
                                      <>
                                        <div className="text-slate-500">Other:</div>
                                        <div className="font-medium text-slate-800">{assignment.other_responsibility}</div>
                                      </>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
