import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Plus, Edit2, Trash2, BookOpen } from 'lucide-react';
import PermissionGuard from '../../components/PermissionGuard';
import Toast from '../../components/Toast';
import Modal from '../../components/Modal';

type Program = { id: number; name: string; program_code: string; active: number };

const ProgramsPage = () => {
  const [toast, setToast] = useState<{message: string, type: 'success'|'error'} | null>(null);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [showProgModal, setShowProgModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [progForm, setProgForm] = useState<Partial<Program>>({ active: 1 });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const progRes = await api.get('/academic/programs');
      setPrograms(progRes.data?.data || []);
    } catch (error) {
      setToast({ message: 'Failed to fetch programs', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openProgModal = (prog?: Program) => {
    if (prog) {
      setProgForm(prog);
      setIsEditing(true);
    } else {
      setProgForm({ active: 1 });
      setIsEditing(false);
    }
    setShowProgModal(true);
  };

  const saveProgram = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (isEditing && progForm.id) {
        await api.put(`/academic/programs/${progForm.id}`, progForm);
        setToast({ message: 'Program updated successfully', type: 'success' });
      } else {
        await api.post('/academic/programs', progForm);
        setToast({ message: 'Program created successfully', type: 'success' });
      }
      setShowProgModal(false);
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.message || 'Error saving program', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const deleteProgram = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this program?')) return;
    try {
      await api.delete(`/academic/programs/${id}`);
      setToast({ message: 'Program deleted successfully', type: 'success' });
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.message || 'Error deleting program', type: 'error' });
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <BookOpen className="text-blue-600" /> Programs
            </h1>
            <p className="text-sm text-slate-500 mt-1">Manage overarching academic programs</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-800">All Programs</h2>
            <PermissionGuard permission="program.create">
              <button onClick={() => openProgModal()} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                <Plus size={16} /> Add Program
              </button>
            </PermissionGuard>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-6 py-3 font-semibold text-slate-600">Code</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Name</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Status</th>
                  <th className="px-6 py-3 font-semibold text-slate-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {programs.map((prog) => (
                  <tr key={prog.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-medium text-slate-800">{prog.program_code}</td>
                    <td className="px-6 py-4 text-slate-600">{prog.name}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${prog.active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-800'}`}>
                        {prog.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <PermissionGuard permission="program.update">
                        <button onClick={() => openProgModal(prog)} className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"><Edit2 size={16} /></button>
                      </PermissionGuard>
                      <PermissionGuard permission="program.delete">
                        <button onClick={() => deleteProgram(prog.id)} className="p-1.5 text-slate-400 hover:text-red-600 transition-colors"><Trash2 size={16} /></button>
                      </PermissionGuard>
                    </td>
                  </tr>
                ))}
                {programs.length === 0 && !loading && (
                  <tr><td colSpan={4} className="px-6 py-8 text-center text-slate-500">No programs found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showProgModal && (
        <Modal title={isEditing ? 'Edit Program' : 'Add Program'} onClose={() => setShowProgModal(false)}>
          <form onSubmit={saveProgram} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Program Code</label>
              <input
                required
                type="text"
                value={progForm.program_code || ''}
                onChange={e => setProgForm({ ...progForm, program_code: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
              <input
                required
                type="text"
                value={progForm.name || ''}
                onChange={e => setProgForm({ ...progForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={progForm.active === 1} onChange={e => setProgForm({ ...progForm, active: e.target.checked ? 1 : 0 })} />
                Active
              </label>
            </div>
            <div className="pt-4 flex justify-end gap-3 border-t">
              <button type="button" onClick={() => setShowProgModal(false)} className="px-4 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg">Cancel</button>
              <button type="submit" disabled={submitting} className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg">{submitting ? 'Saving...' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

export default ProgramsPage;
