import React, { useState, useEffect, useRef } from 'react';
import { lmsApi, FacultyAssignmentRequest } from '../../lib/lms';
import { api } from '../../lib/api';
import Toast from '../../components/Toast';
import { Plus, Trash2 } from 'lucide-react';

interface AssignmentState extends FacultyAssignmentRequest {
  faculty_name: string;
}

export default function MyLeaves() {
  const [leaves, setLeaves] = useState([]);
  const [staffList, setStaffList] = useState<any[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    session: '',
    start_date: '',
    end_date: '',
    days: 0,
    leave_type: 'CL',
    reason: ''
  });

  const [assignments, setAssignments] = useState<(FacultyAssignmentRequest & { faculty_name: string; showDropdown: boolean; assignmentType: 'substitute' | 'other' })[]>([]);

  const fetchLeaves = async () => {
    try {
      const data = await lmsApi.getMyLeaves();
      if (data.data) {
        setLeaves(data.data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchStaff = async () => {
    try {
      const res = await lmsApi.getAssignableStaff();
      if (res.data) {
        setStaffList(res.data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchLeaves();
    fetchStaff();
  }, []);

  useEffect(() => {
    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      if (!isNaN(start.getTime()) && !isNaN(end.getTime())) {
        const diffTime = end.getTime() - start.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        if (diffDays >= 0) {
          setFormData(prev => ({ ...prev, days: diffDays }));
        }
      }
    }
  }, [formData.start_date, formData.end_date]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'days' ? parseFloat(value) : value
    }));
  };

  const handleAddAssignment = (type: 'substitute' | 'other') => {
    setAssignments([...assignments, {
      faculty_date: formData.start_date || '',
      faculty_computer_code: 0,
      faculty_name: '',
      showDropdown: false,
      assignmentType: type,
      assigned_class_dept: type === 'other' ? 'N/A' : '',
      assigned_section: type === 'other' ? 'N/A' : '',
      lecture_type: type === 'other' ? 'N/A' : '',
      start_time: type === 'other' ? '00:00' : '',
      end_time: type === 'other' ? '00:00' : '',
      other_responsibility: ''
    }]);
  };

  const handleAssignmentChange = (index: number, field: string, value: any) => {
    const updated = [...assignments];
    updated[index] = { ...updated[index], [field]: value };
    setAssignments(updated);
  };

  const handleFacultySearchChange = (index: number, value: string) => {
    const updated = [...assignments];
    updated[index].faculty_name = value;
    updated[index].showDropdown = true;
    updated[index].faculty_computer_code = 0; // Reset selected ID when typing
    setAssignments(updated);
  };

  const selectFaculty = (index: number, staff: any) => {
    const updated = [...assignments];
    updated[index].faculty_name = `${staff.first_name} ${staff.last_name} (${staff.computer_code})`;
    updated[index].faculty_computer_code = staff.computer_code;
    updated[index].showDropdown = false;
    setAssignments(updated);
  };

  const handleRemoveAssignment = (index: number) => {
    const updated = [...assignments];
    updated.splice(index, 1);
    setAssignments(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (assignments.length === 0) {
      setToast({ message: 'You must add at least one substitute or other responsibility before applying for leave.', type: 'error' });
      return;
    }

    // Check if all assignments have a valid selected faculty
    const invalidAssignment = assignments.find(a => !a.faculty_computer_code);
    if (invalidAssignment) {
      setToast({ message: 'Please select a valid substitute faculty from the dropdown for all assignments.', type: 'error' });
      return;
    }

    try {
      const payload = {
        ...formData,
        assignments: assignments.map(a => {
          // Exclude UI-only properties
          const { faculty_name, showDropdown, assignmentType, ...rest } = a;
          return {
            ...rest,
            faculty_computer_code: Number(rest.faculty_computer_code)
          };
        })
      };
      await lmsApi.applyLeave(payload);
      setToast({ message: 'Leave applied successfully', type: 'success' });
      fetchLeaves();
      setFormData({
        session: '',
        start_date: '',
        end_date: '',
        days: 0,
        leave_type: 'CL',
        reason: ''
      });
      setAssignments([]);
    } catch (error: any) {
      setToast({ message: error.response?.data?.detail || 'Failed to apply leave', type: 'error' });
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">My Leaves</h1>
      
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 mb-8">
        <h2 className="text-xl font-semibold mb-4">Apply for Leave</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Leave Type</label>
              <select name="leave_type" value={formData.leave_type} onChange={handleChange} className="w-full border rounded p-2">
                <option value="CL">Casual Leave (CL)</option>
                <option value="ML">Medical Leave (ML)</option>
                <option value="EL">Earned Leave (EL)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Start Date</label>
              <input type="date" name="start_date" value={formData.start_date} onChange={handleChange} className="w-full border rounded p-2" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">End Date</label>
              <input type="date" name="end_date" value={formData.end_date} onChange={handleChange} className="w-full border rounded p-2" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Total Days</label>
              <input type="number" step="0.5" name="days" value={formData.days} onChange={handleChange} className="w-full border rounded p-2" required />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Reason</label>
            <textarea name="reason" value={formData.reason} onChange={handleChange} className="w-full border rounded p-2" rows={3} required></textarea>
          </div>

          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Assigned Responsibilities </h3>
              <div className="flex gap-2">
                <button type="button" onClick={() => handleAddAssignment('substitute')} className="flex items-center gap-1 text-sm bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-md transition-colors">
                  <Plus size={16} /> Add Substitute
                </button>
                <button type="button" onClick={() => handleAddAssignment('other')} className="flex items-center gap-1 text-sm bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-md transition-colors">
                  <Plus size={16} /> Add Other
                </button>
              </div>
            </div>
            
            {assignments.length > 0 ? (
              <div className="space-y-4">
                {assignments.map((assignment, index) => {
                  const filteredStaff = staffList.filter((s: any) => 
                    `${s.first_name} ${s.last_name} ${s.computer_code}`.toLowerCase().includes(assignment.faculty_name.toLowerCase())
                  );

                  return (
                    <div key={index} className="p-4 border rounded-md bg-slate-50 relative">
                      <button type="button" onClick={() => handleRemoveAssignment(index)} className="absolute top-2 right-2 text-red-500 hover:text-red-700">
                        <Trash2 size={18} />
                      </button>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="relative">
                          <label className="block text-sm font-medium mb-1">Substitute Faculty</label>
                          <input 
                            type="text"
                            placeholder="Type to search faculty..."
                            value={assignment.faculty_name}
                            onChange={(e) => handleFacultySearchChange(index, e.target.value)}
                            onFocus={() => {
                              const updated = [...assignments];
                              updated[index].showDropdown = true;
                              setAssignments(updated);
                            }}
                            className="w-full border rounded p-2"
                            required
                          />
                          {assignment.showDropdown && assignment.faculty_name.length > 0 && (
                            <ul className="absolute z-10 w-full bg-white border rounded shadow-lg max-h-40 overflow-y-auto mt-1">
                              {filteredStaff.length > 0 ? (
                                filteredStaff.map((staff: any) => (
                                  <li 
                                    key={staff.id} 
                                    onClick={() => selectFaculty(index, staff)}
                                    className="p-2 hover:bg-slate-100 cursor-pointer text-sm"
                                  >
                                    {staff.first_name} {staff.last_name} ({staff.computer_code})
                                  </li>
                                ))
                              ) : (
                                <li className="p-2 text-sm text-slate-500">No faculty found</li>
                              )}
                            </ul>
                          )}
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">Date</label>
                          <input type="date" value={assignment.faculty_date} onChange={(e) => handleAssignmentChange(index, 'faculty_date', e.target.value)} className="w-full border rounded p-2" required />
                        </div>
                        
                        {assignment.assignmentType === 'substitute' ? (
                          <>
                            <div>
                              <label className="block text-sm font-medium mb-1">Class/Dept</label>
                              <input type="text" placeholder="e.g. CSE-3" value={assignment.assigned_class_dept} onChange={(e) => handleAssignmentChange(index, 'assigned_class_dept', e.target.value)} className="w-full border rounded p-2" required />
                            </div>
                            <div>
                              <label className="block text-sm font-medium mb-1">Section</label>
                              <input type="text" placeholder="e.g. A" value={assignment.assigned_section} onChange={(e) => handleAssignmentChange(index, 'assigned_section', e.target.value)} className="w-full border rounded p-2" required />
                            </div>
                            <div>
                              <label className="block text-sm font-medium mb-1">Lecture Type</label>
                              <input type="text" placeholder="e.g. Theory" value={assignment.lecture_type} onChange={(e) => handleAssignmentChange(index, 'lecture_type', e.target.value)} className="w-full border rounded p-2" required />
                            </div>
                            <div className="flex gap-2">
                              <div className="w-1/2">
                                <label className="block text-sm font-medium mb-1">Start Time</label>
                                <input type="time" value={assignment.start_time} onChange={(e) => handleAssignmentChange(index, 'start_time', e.target.value)} className="w-full border rounded p-2" required />
                              </div>
                              <div className="w-1/2">
                                <label className="block text-sm font-medium mb-1">End Time</label>
                                <input type="time" value={assignment.end_time} onChange={(e) => handleAssignmentChange(index, 'end_time', e.target.value)} className="w-full border rounded p-2" required />
                              </div>
                            </div>
                          </>
                        ) : (
                          <div className="md:col-span-2">
                            <label className="block text-sm font-medium mb-1">Other Responsibility Description</label>
                            <input type="text" placeholder="Describe the responsibility..." value={assignment.other_responsibility} onChange={(e) => handleAssignmentChange(index, 'other_responsibility', e.target.value)} className="w-full border rounded p-2" required />
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-slate-500 italic">No substitute assigned. Click above to assign responsibilities.</p>
            )}
          </div>

          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full md:w-auto">Submit Application</button>
        </form>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
        <h2 className="text-xl font-semibold mb-4">Leave History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b">
                <th className="p-3">Type</th>
                <th className="p-3">Start</th>
                <th className="p-3">End</th>
                <th className="p-3">Days</th>
                <th className="p-3">HOD Approval</th>
                <th className="p-3">Principal Approval</th>
              </tr>
            </thead>
            <tbody>
              {leaves.map((l: any) => (
                <tr key={l.apply_id} className="border-b hover:bg-slate-50">
                  <td className="p-3">{l.leave_type}</td>
                  <td className="p-3">{l.start_date}</td>
                  <td className="p-3">{l.end_date}</td>
                  <td className="p-3">{l.days}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 text-xs rounded-full ${l.hod_approval === 1 ? 'bg-green-100 text-green-800' : l.hod_approval === 2 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {l.hod_approval === 0 ? 'Pending' : l.hod_approval === 1 ? 'Approved' : 'Rejected'}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-1 text-xs rounded-full ${l.principal_approval === 1 ? 'bg-green-100 text-green-800' : l.principal_approval === 2 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {l.principal_approval === 0 ? 'Pending' : l.principal_approval === 1 ? 'Approved' : 'Rejected'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
