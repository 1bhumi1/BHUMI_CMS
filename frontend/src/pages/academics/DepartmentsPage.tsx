import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Plus, Edit2, Trash2, Building2 } from 'lucide-react';
import PermissionGuard from '../../components/PermissionGuard';
import Toast from '../../components/Toast';
import Modal from '../../components/Modal';

type Institute = { id: number; name: string };
type Department = { id: number; institue_id: number; name: string; dept_code: string; have_student: number; have_staff: number; active: number };

const DepartmentsPage = () => {
  const [toast, setToast] = useState<{message: string, type: 'success'|'error'} | null>(null);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [institutes, setInstitutes] = useState<Institute[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [deptForm, setDeptForm] = useState<Partial<Department>>({ active: 1, have_student: 1, have_staff: 1 });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [deptRes, instRes] = await Promise.all([
        api.get('/academic/departments'),
        api.get('/academic/institutes')
      ]);
      setDepartments(deptRes.data?.data || []);
      setInstitutes(instRes.data?.data || []);
    } catch (error) {
      setToast({ message: 'Failed to fetch departments', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openDeptModal = (dept?: Department) => {
    if (dept) {
      setDeptForm(dept);
      setIsEditing(true);
    } else {
      setDeptForm({ active: 1, have_student: 1, have_staff: 1, institue_id: institutes[0]?.id });
      setIsEditing(false);
    }
    setShowDeptModal(true);
  };

  const saveDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (isEditing && deptForm.id) {
        await api.put(`/academic/departments/${deptForm.id}`, deptForm);
        setToast({ message: 'Department updated successfully', type: 'success' });
      } else {
        await api.post('/academic/departments', deptForm);
        setToast({ message: 'Department created successfully', type: 'success' });
      }
      setShowDeptModal(false);
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.message || 'Error saving department', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const deleteDepartment = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this department?')) return;
    try {
      await api.delete(`/academic/departments/${id}`);
      setToast({ message: 'Department deleted successfully', type: 'success' });
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.message || 'Error deleting department', type: 'error' });
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <Building2 className="text-blue-600" /> Departments
            </h1>
            <p className="text-sm text-slate-500 mt-1">Manage Departments across all institutes</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-800">All Departments</h2>
            <PermissionGuard permission="department.create">
              <button onClick={() => openDeptModal()} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                <Plus size={16} /> Add Department
              </button>
            </PermissionGuard>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-6 py-3 font-semibold text-slate-600">Code</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Name</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Institute</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Status</th>
                  <th className="px-6 py-3 font-semibold text-slate-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {departments.map((dept) => (
                  <tr key={dept.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-medium text-slate-800">{dept.dept_code}</td>
                    <td className="px-6 py-4 text-slate-600">{dept.name}</td>
                    <td className="px-6 py-4 text-slate-600">{institutes.find(i => i.id === dept.institue_id)?.name || 'Unknown'}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${dept.active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-800'}`}>
                        {dept.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <PermissionGuard permission="department.update">
                        <button onClick={() => openDeptModal(dept)} className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"><Edit2 size={16} /></button>
                      </PermissionGuard>
                      <PermissionGuard permission="department.delete">
                        <button onClick={() => deleteDepartment(dept.id)} className="p-1.5 text-slate-400 hover:text-red-600 transition-colors"><Trash2 size={16} /></button>
                      </PermissionGuard>
                    </td>
                  </tr>
                ))}
                {departments.length === 0 && !loading && (
                  <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-500">No departments found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showDeptModal && (
        <Modal title={isEditing ? 'Edit Department' : 'Add Department'} onClose={() => setShowDeptModal(false)}>
          <form onSubmit={saveDepartment} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Institute</label>
              <select
                required
                value={deptForm.institue_id || ''}
                onChange={e => setDeptForm({ ...deptForm, institue_id: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              >
                <option value="">Select Institute</option>
                {institutes.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Department Code</label>
              <input
                required
                type="text"
                value={deptForm.dept_code || ''}
                onChange={e => setDeptForm({ ...deptForm, dept_code: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
              <input
                required
                type="text"
                value={deptForm.name || ''}
                onChange={e => setDeptForm({ ...deptForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={deptForm.active === 1} onChange={e => setDeptForm({ ...deptForm, active: e.target.checked ? 1 : 0 })} />
                Active
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={deptForm.have_student === 1} onChange={e => setDeptForm({ ...deptForm, have_student: e.target.checked ? 1 : 0 })} />
                Has Students
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={deptForm.have_staff === 1} onChange={e => setDeptForm({ ...deptForm, have_staff: e.target.checked ? 1 : 0 })} />
                Has Staff
              </label>
            </div>
            <div className="pt-4 flex justify-end gap-3 border-t">
              <button type="button" onClick={() => setShowDeptModal(false)} className="px-4 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg">Cancel</button>
              <button type="submit" disabled={submitting} className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg">{submitting ? 'Saving...' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

export default DepartmentsPage;
