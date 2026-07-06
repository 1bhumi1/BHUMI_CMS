import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { useAuth } from '../../lib/AuthContext';
import { Navigate } from 'react-router-dom';
import { Plus, Edit2, Trash2, BookMarked } from 'lucide-react';
import Toast from '../../components/Toast';
import Modal from '../../components/Modal';

type Department = { id: number; name: string; dept_code: string };
type Subject = {
  id: number;
  subject_code: string;
  subject_name: string;
  department_id: number | null;
  active: number;
  department?: Department | null;
};

const AddSubject = () => {
  const { role } = useAuth();

  // Route Guard: Only HOD can access
  if (role !== 'HOD') {
    return <Navigate to="/unauthorized" replace />;
  }

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [subjectForm, setSubjectForm] = useState<Partial<Subject>>({ active: 1, department_id: null });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [subjectRes, deptRes] = await Promise.all([
        api.get('/academic/subjects'),
        api.get('/academic/departments')
      ]);
      setSubjects(subjectRes.data?.data || []);
      setDepartments(deptRes.data?.data || []);
    } catch (error) {
      setToast({ message: 'Failed to fetch academic data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openModal = (subject?: Subject) => {
    if (subject) {
      setSubjectForm(subject);
      setIsEditing(true);
    } else {
      setSubjectForm({ active: 1, department_id: departments[0]?.id || null });
      setIsEditing(false);
    }
    setShowModal(true);
  };

  const saveSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        subject_code: subjectForm.subject_code,
        subject_name: subjectForm.subject_name,
        department_id: subjectForm.department_id ? Number(subjectForm.department_id) : null,
        active: Number(subjectForm.active)
      };

      if (isEditing && subjectForm.id) {
        await api.put(`/academic/subjects/${subjectForm.id}`, payload);
        setToast({ message: 'Subject updated successfully', type: 'success' });
      } else {
        await api.post('/academic/subjects', payload);
        setToast({ message: 'Subject created successfully', type: 'success' });
      }
      setShowModal(false);
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.detail || 'Error saving subject', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const deleteSubject = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this subject? This will also remove any mapped credit rules.')) return;
    try {
      await api.delete(`/academic/subjects/${id}`);
      setToast({ message: 'Subject deleted successfully', type: 'success' });
      fetchData();
    } catch (error: any) {
      setToast({ message: error.response?.data?.detail || 'Error deleting subject', type: 'error' });
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50">
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
              <BookMarked className="text-blue-600" /> Subjects
            </h1>
            <p className="text-sm text-slate-500 mt-1">Manage academic subjects list</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-800">All Subjects</h2>
            <button
              onClick={() => openModal()}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              <Plus size={16} /> Add Subject
            </button>
          </div>

          <div className="overflow-x-auto">
            {loading ? (
              <div className="p-8 text-center text-slate-500">Loading subjects...</div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th className="px-6 py-3 font-semibold text-slate-600">Subject Code</th>
                    <th className="px-6 py-3 font-semibold text-slate-600">Subject Name</th>
                    <th className="px-6 py-3 font-semibold text-slate-600">Department</th>
                    <th className="px-6 py-3 font-semibold text-slate-600">Status</th>
                    <th className="px-6 py-3 font-semibold text-slate-600 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {subjects.map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-50/50">
                      <td className="px-6 py-4 font-medium text-slate-800">{sub.subject_code}</td>
                      <td className="px-6 py-4 text-slate-600">{sub.subject_name}</td>
                      <td className="px-6 py-4 text-slate-600">{sub.department?.name || 'Generic / Universal'}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            sub.active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-800'
                          }`}
                        >
                          {sub.active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => openModal(sub)}
                          className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors mr-2"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          onClick={() => deleteSubject(sub.id)}
                          className="p-1.5 text-slate-400 hover:text-red-600 transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {subjects.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                        No subjects found. Click 'Add Subject' to add one.
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
        <Modal title={isEditing ? 'Edit Subject' : 'Add Subject'} onClose={() => setShowModal(false)}>
          <form onSubmit={saveSubject} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Subject Code *</label>
              <input
                type="text"
                required
                placeholder="e.g. CS-301"
                value={subjectForm.subject_code || ''}
                onChange={(e) => setSubjectForm({ ...subjectForm, subject_code: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Subject Name *</label>
              <input
                type="text"
                required
                placeholder="e.g. Database Management Systems"
                value={subjectForm.subject_name || ''}
                onChange={(e) => setSubjectForm({ ...subjectForm, subject_name: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Department</label>
              <select
                value={subjectForm.department_id || ''}
                onChange={(e) => setSubjectForm({ ...subjectForm, department_id: e.target.value ? Number(e.target.value) : null })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Generic / Universal (No Specific Department)</option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name} ({dept.dept_code})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Status</label>
              <select
                value={subjectForm.active}
                onChange={(e) => setSubjectForm({ ...subjectForm, active: Number(e.target.value) })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={1}>Active</option>
                <option value={0}>Inactive</option>
              </select>
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
                {submitting ? 'Saving...' : 'Save Subject'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};

export default AddSubject;
