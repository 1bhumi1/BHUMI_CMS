import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Plus, Edit2, Trash2, School } from 'lucide-react';
import PermissionGuard from '../../components/PermissionGuard';
import Toast from '../../components/Toast';
import Modal from '../../components/Modal';

type Institute = { id: number; name: string };

const InstitutesPage = () => {
  const [toast, setToast] = useState<{message: string, type: 'success'|'error'} | null>(null);
  const [institutes, setInstitutes] = useState<Institute[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInstModal, setShowInstModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [instForm, setInstForm] = useState<Partial<Institute>>({});
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const instRes = await api.get('/academic/institutes');
      setInstitutes(instRes.data?.data || []);
    } catch (error) {
      setToast({ message: 'Failed to fetch institutes', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openInstModal = (inst?: Institute) => {
    if (inst) {
      setInstForm(inst);
      setIsEditing(true);
    } else {
      setInstForm({});
      setIsEditing(false);
    }
    setShowInstModal(true);
  };

  const saveInstitute = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (isEditing && instForm.id) {
        await api.put(`/academic/institutes/${instForm.id}`, instForm);
        setToast({ message: 'Institute updated successfully', type: 'success' });
      } else {
        await api.post('/academic/institutes', instForm);
        setToast({ message: 'Institute created successfully', type: 'success' });
      }
      setShowInstModal(false);
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.message || 'Error saving institute', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const deleteInstitute = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this institute?')) return;
    try {
      await api.delete(`/academic/institutes/${id}`);
      setToast({ message: 'Institute deleted successfully', type: 'success' });
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.message || 'Error deleting institute', type: 'error' });
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <School className="text-blue-600" /> Institutes
            </h1>
            <p className="text-sm text-slate-500 mt-1">Manage Institutes in the system</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-800">All Institutes</h2>
            <PermissionGuard permission="institute.create">
              <button onClick={() => openInstModal()} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                <Plus size={16} /> Add Institute
              </button>
            </PermissionGuard>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-6 py-3 font-semibold text-slate-600">ID</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Name</th>
                  <th className="px-6 py-3 font-semibold text-slate-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {institutes.map((inst) => (
                  <tr key={inst.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-medium text-slate-800">{inst.id}</td>
                    <td className="px-6 py-4 text-slate-600">{inst.name}</td>
                    <td className="px-6 py-4 text-right">
                      <PermissionGuard permission="institute.update">
                        <button onClick={() => openInstModal(inst)} className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"><Edit2 size={16} /></button>
                      </PermissionGuard>
                      <PermissionGuard permission="institute.delete">
                        <button onClick={() => deleteInstitute(inst.id)} className="p-1.5 text-slate-400 hover:text-red-600 transition-colors"><Trash2 size={16} /></button>
                      </PermissionGuard>
                    </td>
                  </tr>
                ))}
                {institutes.length === 0 && !loading && (
                  <tr><td colSpan={3} className="px-6 py-8 text-center text-slate-500">No institutes found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showInstModal && (
        <Modal title={isEditing ? 'Edit Institute' : 'Add Institute'} onClose={() => setShowInstModal(false)}>
          <form onSubmit={saveInstitute} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
              <input
                required
                type="text"
                value={instForm.name || ''}
                onChange={e => setInstForm({ ...instForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <div className="pt-4 flex justify-end gap-3 border-t">
              <button type="button" onClick={() => setShowInstModal(false)} className="px-4 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg">Cancel</button>
              <button type="submit" disabled={submitting} className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg">{submitting ? 'Saving...' : 'Save'}</button>
            </div>
          </form>
        </Modal>
      )}

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

export default InstitutesPage;
