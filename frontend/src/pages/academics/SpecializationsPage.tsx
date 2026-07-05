import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Plus, Edit2, Trash2, GraduationCap } from 'lucide-react';
import PermissionGuard from '../../components/PermissionGuard';
import Toast from '../../components/Toast';
import Modal from '../../components/Modal';

type Program = { id: number; name: string; program_code: string; active: number };
type Department = { id: number; institue_id: number; name: string; dept_code: string; have_student: number; have_staff: number; active: number };
type Specialization = { id: number; program_id: number; department_id: number; name: string; specialization_code: string; active: number };

const SpecializationsPage = () => {
  const [toast, setToast] = useState<{message: string, type: 'success'|'error'} | null>(null);
  const [specializations, setSpecializations] = useState<Specialization[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSpecModal, setShowSpecModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [specForm, setSpecForm] = useState<Partial<Specialization>>({ active: 1 });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [specRes, progRes, deptRes] = await Promise.all([
        api.get('/academic/specializations'),
        api.get('/academic/programs'),
        api.get('/academic/departments')
      ]);
      setSpecializations(specRes.data?.data || []);
      setPrograms(progRes.data?.data || []);
      setDepartments(deptRes.data?.data || []);
    } catch (error) {
      setToast({ message: 'Failed to fetch specializations', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openSpecModal = (spec?: Specialization) => {
    if (spec) {
      setSpecForm(spec);
      setIsEditing(true);
    } else {
      setSpecForm({ active: 1, department_id: departments[0]?.id, program_id: programs[0]?.id });
      setIsEditing(false);
    }
    setShowSpecModal(true);
  };

  const saveSpecialization = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (isEditing && specForm.id) {
        await api.put(`/academic/specializations/${specForm.id}`, specForm);
        setToast({ message: 'Specialization updated successfully', type: 'success' });
      } else {
        await api.post('/academic/specializations', specForm);
        setToast({ message: 'Specialization created successfully', type: 'success' });
      }
      setShowSpecModal(false);
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.message || 'Error saving specialization', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const deleteSpecialization = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this specialization?')) return;
    try {
      await api.delete(`/academic/specializations/${id}`);
      setToast({ message: 'Specialization deleted successfully', type: 'success' });
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.message || 'Error deleting specialization', type: 'error' });
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <GraduationCap className="text-blue-600" /> Specializations
            </h1>
            <p className="text-sm text-slate-500 mt-1">Manage specialized fields of study</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-800">All Specializations</h2>
            <PermissionGuard permission="specialization.create">
              <button onClick={() => openSpecModal()} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                <Plus size={16} /> Add Specialization
              </button>
            </PermissionGuard>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-6 py-3 font-semibold text-slate-600">Code</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Name</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Program</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Department</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Status</th>
                  <th className="px-6 py-3 font-semibold text-slate-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {specializations.map((spec) => (
                  <tr key={spec.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-medium text-slate-800">{spec.specialization_code}</td>
                    <td className="px-6 py-4 text-slate-600">{spec.name}</td>
                    <td className="px-6 py-4 text-slate-600">{programs.find(p => p.id === spec.program_id)?.name || 'Unknown'}</td>
                    <td className="px-6 py-4 text-slate-600">{departments.find(d => d.id === spec.department_id)?.name || 'Unknown'}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${spec.active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-800'}`}>
                        {spec.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <PermissionGuard permission="specialization.update">
                        <button onClick={() => openSpecModal(spec)} className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"><Edit2 size={16} /></button>
                      </PermissionGuard>
                      <PermissionGuard permission="specialization.delete">
                        <button onClick={() => deleteSpecialization(spec.id)} className="p-1.5 text-slate-400 hover:text-red-600 transition-colors"><Trash2 size={16} /></button>
                      </PermissionGuard>
                    </td>
                  </tr>
                ))}
                {specializations.length === 0 && !loading && (
                  <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-500">No specializations found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showSpecModal && (
        <Modal title={isEditing ? 'Edit Specialization' : 'Add Specialization'} onClose={() => setShowSpecModal(false)}>
          <form onSubmit={saveSpecialization} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Program</label>
              <select
                required
                value={specForm.program_id || ''}
                onChange={e => setSpecForm({ ...specForm, program_id: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              >
                <option value="">Select Program</option>
                {programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Department</label>
              <select
                required
                value={specForm.department_id || ''}
                onChange={e => setSpecForm({ ...specForm, department_id: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              >
                <option value="">Select Department</option>
                {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Specialization Code</label>
              <input
                required
                type="text"
                value={specForm.specialization_code || ''}
                onChange={e => setSpecForm({ ...specForm, specialization_code: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
              <input
                required
                type="text"
                value={specForm.name || ''}
                onChange={e => setSpecForm({ ...specForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={specForm.active === 1} onChange={e => setSpecForm({ ...specForm, active: e.target.checked ? 1 : 0 })} />
                Active
              </label>
            </div>
            <div className="pt-4 flex justify-end gap-3 border-t">
              <button type="button" onClick={() => setShowSpecModal(false)} className="px-4 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg">Cancel</button>
              <button type="submit" disabled={submitting} className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg">{submitting ? 'Saving...' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

export default SpecializationsPage;
