import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Plus, Edit2, Trash2, Calendar } from 'lucide-react';
import PermissionGuard from '../../components/PermissionGuard';
import Toast from '../../components/Toast';
import Modal from '../../components/Modal';

type AcademicTerm = { id: number; term_name: string; start_date?: string; end_date?: string; academic_session_id: number; };
type AcademicSession = { id: number; session_name: string; };

const AcademicTermsPage = () => {
  const [terms, setTerms] = useState<AcademicTerm[]>([]);
  const [sessions, setSessions] = useState<AcademicSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTermModal, setShowTermModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [termForm, setTermForm] = useState<Partial<AcademicTerm>>({});
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [termsRes, sessRes] = await Promise.all([
        api.get('/academic/academic-terms'),
        api.get('/academic/academic-sessions')
      ]);
      setTerms(termsRes.data?.data || []);
      setSessions(sessRes.data?.data || []);
    } catch (error) {
      setToast({ message: 'Failed to fetch entities', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openTermModal = (item?: AcademicTerm) => {
    setTermForm(item ? { ...item } : { academic_session_id: sessions[0]?.id });
    setIsEditing(!!item);
    setShowTermModal(true);
  };

  const saveTerm = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload: any = { ...termForm };
      if (!payload.start_date) payload.start_date = null;
      if (!payload.end_date) payload.end_date = null;

      if (isEditing && termForm.id) {
        await api.put(`/academic/academic-terms/${termForm.id}`, payload);
      } else {
        await api.post('/academic/academic-terms', payload);
      }
      setToast({ message: `Term ${isEditing ? 'updated' : 'created'} successfully`, type: 'success' });
      setShowTermModal(false);
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.message || 'Error saving term', type: 'error' });
    } finally { setSubmitting(false); }
  };

  const deleteTerm = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this term?')) return;
    try {
      await api.delete(`/academic/academic-terms/${id}`);
      setToast({ message: 'Term deleted', type: 'success' });
      fetchData();
    } catch (error: any) { setToast({ message: 'Error deleting term', type: 'error' }); }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <Calendar className="text-blue-600" /> Academic Terms
            </h1>
            <p className="text-sm text-slate-500 mt-1">Manage Academic Terms</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-800">Academic Terms</h2>
            <PermissionGuard permission="academic_term.create">
              <button onClick={() => openTermModal()} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                <Plus size={16} /> Add Term
              </button>
            </PermissionGuard>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-6 py-3 font-semibold text-slate-600">Term Name</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Session</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">Start Date</th>
                  <th className="px-6 py-3 font-semibold text-slate-600">End Date</th>
                  <th className="px-6 py-3 font-semibold text-slate-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {terms.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4 font-medium text-slate-800">{t.term_name}</td>
                    <td className="px-6 py-4 text-slate-600">{sessions.find(s => s.id === t.academic_session_id)?.session_name || 'Unknown'}</td>
                    <td className="px-6 py-4 text-slate-600">{t.start_date || 'N/A'}</td>
                    <td className="px-6 py-4 text-slate-600">{t.end_date || 'N/A'}</td>
                    <td className="px-6 py-4 text-right">
                      <PermissionGuard permission="academic_term.update">
                        <button onClick={() => openTermModal(t)} className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"><Edit2 size={16} /></button>
                      </PermissionGuard>
                      <PermissionGuard permission="academic_term.delete">
                        <button onClick={() => deleteTerm(t.id)} className="p-1.5 text-slate-400 hover:text-red-600 transition-colors"><Trash2 size={16} /></button>
                      </PermissionGuard>
                    </td>
                  </tr>
                ))}
                {terms.length === 0 && !loading && (
                  <tr><td colSpan={5} className="px-6 py-8 text-center text-slate-500">No terms found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showTermModal && (
        <Modal title={isEditing ? 'Edit Term' : 'Add Term'} onClose={() => setShowTermModal(false)}>
          <form onSubmit={saveTerm} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Term Name</label>
              <input required type="text" value={termForm.term_name || ''} onChange={e => setTermForm({ ...termForm, term_name: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Session</label>
              <select required value={termForm.academic_session_id || ''} onChange={e => setTermForm({ ...termForm, academic_session_id: Number(e.target.value) })} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
                <option value="">Select Session</option>
                {sessions.map(s => <option key={s.id} value={s.id}>{s.session_name}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Start Date</label>
                <input type="date" value={termForm.start_date || ''} onChange={e => setTermForm({ ...termForm, start_date: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">End Date</label>
                <input type="date" value={termForm.end_date || ''} onChange={e => setTermForm({ ...termForm, end_date: e.target.value })} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
              </div>
            </div>
            <div className="pt-4 flex justify-end gap-3 border-t">
              <button type="button" onClick={() => setShowTermModal(false)} className="px-4 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg">Cancel</button>
              <button type="submit" disabled={submitting} className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg">Save</button>
            </div>
          </form>
        </Modal>
      )}

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

export default AcademicTermsPage;
