import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { useAuth } from '../../lib/AuthContext';
import { Navigate } from 'react-router-dom';
import { Plus, Edit2, Trash2, DollarSign } from 'lucide-react';
import Toast from '../../components/Toast';
import Modal from '../../components/Modal';

type Subject = { id: number; subject_code: string; subject_name: string };
type SubjectCredit = {
  id: number;
  subject_id: number;
  scheme_name: string;
  lecture_credits: number;
  tutorial_credits: number;
  practical_credits: number;
  total_credits: number;
  subject?: Subject;
};

const AddSubjectCredit = () => {
  const { role } = useAuth();

  // Route Guard: Only HOD can access
  if (role !== 'HOD') {
    return <Navigate to="/unauthorized" replace />;
  }

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [credits, setCredits] = useState<SubjectCredit[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [creditForm, setCreditForm] = useState<Partial<SubjectCredit>>({
    lecture_credits: 0,
    tutorial_credits: 0,
    practical_credits: 0,
    total_credits: 0
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [creditRes, subjectRes] = await Promise.all([
        api.get('/academic/subject-credits'),
        api.get('/academic/subjects')
      ]);
      setCredits(creditRes.data?.data || []);
      // Filter only active subjects for dropdown select
      const activeSubs = (subjectRes.data?.data || []).filter((s: any) => s.active === 1);
      setSubjects(activeSubs);
    } catch (error) {
      setToast({ message: 'Failed to fetch academic data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openModal = (credit?: SubjectCredit) => {
    if (credit) {
      setCreditForm(credit);
      setIsEditing(true);
    } else {
      setCreditForm({
        subject_id: subjects[0]?.id || undefined,
        scheme_name: '',
        lecture_credits: 3,
        tutorial_credits: 1,
        practical_credits: 0,
        total_credits: 4
      });
      setIsEditing(false);
    }
    setShowModal(true);
  };

  // Automatically calculate total credits when L, T, P changes
  const handleLTPChange = (field: 'lecture_credits' | 'tutorial_credits' | 'practical_credits', val: number) => {
    const nextForm = { ...creditForm, [field]: val };
    const l = nextForm.lecture_credits || 0;
    const t = nextForm.tutorial_credits || 0;
    const p = nextForm.practical_credits || 0;
    nextForm.total_credits = l + t + p;
    setCreditForm(nextForm);
  };

  const saveCredit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!creditForm.subject_id) {
      setToast({ message: 'Please select a subject', type: 'error' });
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        subject_id: Number(creditForm.subject_id),
        scheme_name: creditForm.scheme_name,
        lecture_credits: Number(creditForm.lecture_credits),
        tutorial_credits: Number(creditForm.tutorial_credits),
        practical_credits: Number(creditForm.practical_credits),
        total_credits: Number(creditForm.total_credits)
      };

      if (isEditing && creditForm.id) {
        await api.put(`/academic/subject-credits/${creditForm.id}`, payload);
        setToast({ message: 'Subject credit updated successfully', type: 'success' });
      } else {
        await api.post('/academic/subject-credits', payload);
        setToast({ message: 'Subject credit created successfully', type: 'success' });
      }
      setShowModal(false);
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.detail || 'Error saving subject credit', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const deleteCredit = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this subject credit rule?')) return;
    try {
      await api.delete(`/academic/subject-credits/${id}`);
      setToast({ message: 'Subject credit deleted successfully', type: 'success' });
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.detail || 'Error deleting subject credit', type: 'error' });
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <DollarSign className="text-blue-600" /> Subject Credits
            </h1>
            <p className="text-sm text-slate-500 mt-1">Configure credit structure (L-T-P) for subjects</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-800">All Subject Credits</h2>
            <button
              onClick={() => openModal()}
              disabled={subjects.length === 0}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <Plus size={16} /> Add Subject Credit
            </button>
          </div>

          <div className="overflow-x-auto">
            {loading ? (
              <div className="p-8 text-center text-slate-500">Loading credits config...</div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="px-6 py-3 font-semibold text-slate-600">Subject</th>
                    <th className="px-6 py-3 font-semibold text-slate-600">Scheme Name</th>
                    <th className="px-6 py-3 font-semibold text-slate-600 text-center">Lecture (L)</th>
                    <th className="px-6 py-3 font-semibold text-slate-600 text-center">Tutorial (T)</th>
                    <th className="px-6 py-3 font-semibold text-slate-600 text-center">Practical (P)</th>
                    <th className="px-6 py-3 font-semibold text-slate-600 text-center">Total Credits</th>
                    <th className="px-6 py-3 font-semibold text-slate-600 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {credits.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/50">
                      <td className="px-6 py-4 font-medium text-slate-800">
                        {c.subject ? `${c.subject.subject_name} (${c.subject.subject_code})` : `Subject ID: ${c.subject_id}`}
                      </td>
                      <td className="px-6 py-4 text-slate-600">{c.scheme_name}</td>
                      <td className="px-6 py-4 text-center text-slate-600">{c.lecture_credits}</td>
                      <td className="px-6 py-4 text-center text-slate-600">{c.tutorial_credits}</td>
                      <td className="px-6 py-4 text-center text-slate-600">{c.practical_credits}</td>
                      <td className="px-6 py-4 text-center font-bold text-blue-600">{c.total_credits}</td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => openModal(c)}
                          className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors mr-2"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          onClick={() => deleteCredit(c.id)}
                          className="p-1.5 text-slate-400 hover:text-red-600 transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {credits.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                        No subject credit configurations found.{' '}
                        {subjects.length === 0 ? 'Add subjects first before adding credits.' : "Click 'Add Subject Credit' to configure."}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      {showModal && (
        <Modal title={isEditing ? 'Edit Subject Credit' : 'Add Subject Credit'} onClose={() => setShowModal(false)}>
          <form onSubmit={saveCredit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Subject *</label>
              <select
                disabled={isEditing}
                value={creditForm.subject_id || ''}
                onChange={(e) => setCreditForm({ ...creditForm, subject_id: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100"
              >
                {subjects.map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.subject_name} ({sub.subject_code})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Scheme Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. CBCS 2023 or 2024 Scheme"
                value={creditForm.scheme_name || ''}
                onChange={(e) => setCreditForm({ ...creditForm, scheme_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Lecture (L) *</label>
                <input
                  type="number"
                  required
                  min={0}
                  value={creditForm.lecture_credits}
                  onChange={(e) => handleLTPChange('lecture_credits', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Tutorial (T) *</label>
                <input
                  type="number"
                  required
                  min={0}
                  value={creditForm.tutorial_credits}
                  onChange={(e) => handleLTPChange('tutorial_credits', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Practical (P) *</label>
                <input
                  type="number"
                  required
                  min={0}
                  value={creditForm.practical_credits}
                  onChange={(e) => handleLTPChange('practical_credits', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1 font-bold">Total Credits</label>
              <input
                type="number"
                readOnly
                value={creditForm.total_credits}
                className="w-full px-3 py-2 border border-slate-200 bg-slate-100 rounded-lg text-sm focus:outline-none font-bold text-blue-600"
              />
              <p className="text-xs text-slate-400 mt-1">Automatically calculated as L + T + P</p>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-75"
              >
                {submitting ? 'Saving...' : 'Save Config'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};

export default AddSubjectCredit;
