import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api';
import PermissionGuard from '../../components/PermissionGuard';
import {
  Plus, Search, Edit2, Trash2, Loader2, ChevronLeft, ChevronRight,
  X, Check, AlertCircle, Eye, Download, ClipboardList, ArrowUpDown, ArrowUp, ArrowDown
} from 'lucide-react';

interface AcademicSessionItem {
  id: number;
  session_name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

interface AcademicSessionFormData {
  session_name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

const Toast = ({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`fixed top-6 right-6 z-[100] flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl text-white text-sm font-medium animate-slide-in ${
      type === 'success' ? 'bg-emerald-600' : 'bg-red-600'
    }`}>
      {type === 'success' ? <Check size={18} /> : <AlertCircle size={18} />}
      {message}
      <button onClick={onClose} className="ml-2 hover:opacity-70"><X size={16} /></button>
    </div>
  );
};

const Modal = ({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
    <div className="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-hidden flex flex-col animate-fade-in-up">
      <div className="bg-white px-6 py-4 border-b border-slate-200 flex items-center justify-between rounded-t-2xl z-10 shrink-0">
        <h3 className="text-lg font-bold text-slate-800">{title}</h3>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
          <X size={20} />
        </button>
      </div>
      <div className="overflow-y-auto flex-1 p-6">
        {children}
      </div>
    </div>
  </div>
);

export default function AcademicSessionManagement() {
  const queryClient = useQueryClient();
  
  // State
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [sortBy, setSortBy] = useState('newest');
  const [sortOrder, setSortOrder] = useState<'asc'|'desc'>('desc');
  const [filterActive, setFilterActive] = useState<string>('');

  // UI State
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<AcademicSessionItem | null>(null);
  const [editingItem, setEditingItem] = useState<AcademicSessionItem | null>(null);

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<AcademicSessionFormData>();

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const { data: sessionsData, isLoading } = useQuery({
    queryKey: ['academic-sessions', { page, limit, search: debouncedSearch, sortBy, sortOrder, filterActive }],
    queryFn: async () => {
      const skip = (page - 1) * limit;
      let url = `/academic-sessions?skip=${skip}&limit=${limit}&sort_by=${sortBy}&sort_order=${sortOrder}`;
      if (debouncedSearch) url += `&search=${encodeURIComponent(debouncedSearch)}`;
      if (filterActive !== '') url += `&is_active=${filterActive}`;
      
      const res = await api.get(url);
      return res.data?.data || { items: [], total: 0 };
    },
  });

  const items: AcademicSessionItem[] = sessionsData?.items || [];
  const totalPages = sessionsData?.total ? Math.ceil(sessionsData.total / limit) : 1;

  const createMutation = useMutation({
    mutationFn: async (payload: AcademicSessionFormData) => {
      const res = await api.post('/academic-sessions/', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic-sessions'] });
      setToast({ message: 'Academic Session created successfully', type: 'success' });
      setIsModalOpen(false);
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || err.response?.data?.message || 'Creation failed', type: 'error' });
    }
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number, payload: AcademicSessionFormData }) => {
      const res = await api.put(`/academic-sessions/${id}`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic-sessions'] });
      setToast({ message: 'Academic Session updated successfully', type: 'success' });
      setIsModalOpen(false);
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || err.response?.data?.message || 'Update failed', type: 'error' });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/academic-sessions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic-sessions'] });
      setToast({ message: 'Academic Session deleted successfully', type: 'success' });
      setIsDeleteModalOpen(false);
      setSelectedItem(null);
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || err.response?.data?.message || 'Deletion failed', type: 'error' });
    }
  });

  const openCreateModal = () => {
    setEditingItem(null);
    reset({
      session_name: '',
      start_date: '',
      end_date: '',
      is_active: false
    });
    setIsModalOpen(true);
  };

  const openEditModal = (item: AcademicSessionItem) => {
    setEditingItem(item);
    reset({
      session_name: item.session_name,
      start_date: item.start_date,
      end_date: item.end_date,
      is_active: item.is_active
    });
    setIsModalOpen(true);
  };
  
  const openViewModal = (item: AcademicSessionItem) => {
    setSelectedItem(item);
    setIsViewModalOpen(true);
  };

  const onSubmit = (data: AcademicSessionFormData) => {
    const start = new Date(data.start_date);
    const end = new Date(data.end_date);
    if (start >= end) {
      setToast({ message: 'Start date must be before end date', type: 'error' });
      return;
    }

    if (editingItem) {
      updateMutation.mutate({ id: editingItem.id, payload: data });
    } else {
      createMutation.mutate(data);
    }
  };

  const confirmDelete = (item: AcademicSessionItem) => {
    setSelectedItem(item);
    setIsDeleteModalOpen(true);
  };

  const handleExport = async () => {
    try {
      const response = await api.get('/academic-sessions/export?format=csv', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'academic_sessions.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      setToast({ message: 'Exported successfully', type: 'success' });
    } catch (err) {
      setToast({ message: 'Failed to export', type: 'error' });
    }
  };
  
  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const SortIcon = ({ field }: { field: string }) => {
    if (sortBy !== field) return <ArrowUpDown size={14} className="text-slate-400 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />;
    return sortOrder === 'asc' ? <ArrowUp size={14} className="text-blue-600 ml-1" /> : <ArrowDown size={14} className="text-blue-600 ml-1" />;
  };

  return (
    <div className="min-h-screen bg-slate-50/50 flex flex-col">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <div className="p-8 max-w-7xl mx-auto w-full flex-1 flex flex-col">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
              <ClipboardList className="text-blue-600" size={32} />
              Academic Sessions
            </h1>
            <p className="text-slate-500 mt-1">Manage academic years and current sessions</p>
          </div>
          <div className="flex gap-3 w-full sm:w-auto">
            <PermissionGuard permission="academic_session.read">
              <button 
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
              >
                <Download size={18} />
                Export
              </button>
            </PermissionGuard>
            <PermissionGuard permission="academic_session.create">
              <button 
                onClick={openCreateModal}
                className="flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all shadow-lg shadow-blue-200 active:scale-95 font-medium flex-1 sm:flex-none"
              >
                <Plus size={18} />
                New Session
              </button>
            </PermissionGuard>
          </div>
        </div>

        {/* Toolbar & Filters */}
        <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="relative w-full md:w-1/2">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
              <input
                type="text"
                placeholder="Search sessions (e.g. 2026-2027)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
              />
            </div>
            
            <div className="flex items-center gap-3 w-full md:w-1/2">
              <select 
                value={filterActive} 
                onChange={(e) => { setFilterActive(e.target.value); setPage(1); }}
                className="w-full md:w-48 px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all text-sm"
              >
                <option value="">All Statuses</option>
                <option value="true">Current Session</option>
                <option value="false">Past/Future Session</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 flex-1 flex flex-col overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                <tr>
                  <th className="px-6 py-4 font-semibold cursor-pointer group select-none" onClick={() => handleSort('name')}>
                    <div className="flex items-center">Session Name <SortIcon field="name" /></div>
                  </th>
                  <th className="px-6 py-4 font-semibold cursor-pointer group select-none" onClick={() => handleSort('start_date')}>
                    <div className="flex items-center">Start Date <SortIcon field="start_date" /></div>
                  </th>
                  <th className="px-6 py-4 font-semibold cursor-pointer group select-none" onClick={() => handleSort('end_date')}>
                    <div className="flex items-center">End Date <SortIcon field="end_date" /></div>
                  </th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center">
                      <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
                      <p className="text-slate-500">Loading sessions...</p>
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                      No academic sessions found
                    </td>
                  </tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50/80 transition-colors group">
                      <td className="px-6 py-4 text-slate-700 font-medium">{item.session_name}</td>
                      <td className="px-6 py-4 text-slate-600">{new Date(item.start_date).toLocaleDateString()}</td>
                      <td className="px-6 py-4 text-slate-600">{new Date(item.end_date).toLocaleDateString()}</td>
                      <td className="px-6 py-4">
                        {item.is_active ? (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                            Current Session
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                            Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <PermissionGuard permission="academic_session.read">
                            <button onClick={() => openViewModal(item)} className="p-1.5 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors" title="View">
                              <Eye size={16} />
                            </button>
                          </PermissionGuard>
                          <PermissionGuard permission="academic_session.update">
                            <button onClick={() => openEditModal(item)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                              <Edit2 size={16} />
                            </button>
                          </PermissionGuard>
                          <PermissionGuard permission="academic_session.delete">
                            <button onClick={() => confirmDelete(item)} className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                              <Trash2 size={16} />
                            </button>
                          </PermissionGuard>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {!isLoading && items.length > 0 && (
            <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
              <span className="text-sm text-slate-500">
                Page <span className="font-medium text-slate-700">{page}</span> of <span className="font-medium text-slate-700">{totalPages}</span>
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 border border-slate-200 rounded-lg bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft size={18} />
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 border border-slate-200 rounded-lg bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* View Modal */}
      {isViewModalOpen && selectedItem && (
        <Modal title="View Academic Session" onClose={() => setIsViewModalOpen(false)}>
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <p className="text-sm text-slate-500">Session Name</p>
                <p className="font-medium text-slate-900 text-lg">{selectedItem.session_name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Start Date</p>
                <p className="font-medium text-slate-900">{new Date(selectedItem.start_date).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">End Date</p>
                <p className="font-medium text-slate-900">{new Date(selectedItem.end_date).toLocaleDateString()}</p>
              </div>
              <div className="col-span-2">
                <p className="text-sm text-slate-500 mb-1">Status</p>
                {selectedItem.is_active ? (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Current Session
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                    Inactive
                  </span>
                )}
              </div>
            </div>
            <div className="flex justify-end pt-4 border-t border-slate-100">
              <button 
                onClick={() => setIsViewModalOpen(false)}
                className="px-5 py-2.5 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Form Modal */}
      {isModalOpen && (
        <Modal title={editingItem ? 'Edit Academic Session' : 'Create Academic Session'} onClose={() => setIsModalOpen(false)}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Session Name *</label>
                <input
                  type="text"
                  placeholder="e.g. 2026-2027"
                  {...register('session_name', { required: 'Session name is required', maxLength: { value: 20, message: 'Max 20 characters' } })}
                  className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
                {errors.session_name && <p className="text-red-500 text-xs mt-1">{errors.session_name.message}</p>}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Start Date *</label>
                  <input
                    type="date"
                    {...register('start_date', { required: 'Start date is required' })}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                  {errors.start_date && <p className="text-red-500 text-xs mt-1">{errors.start_date.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">End Date *</label>
                  <input
                    type="date"
                    {...register('end_date', { required: 'End date is required' })}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                  {errors.end_date && <p className="text-red-500 text-xs mt-1">{errors.end_date.message}</p>}
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-blue-50/50 border border-blue-100 rounded-xl mt-2">
                <input
                  type="checkbox"
                  id="is_active"
                  {...register('is_active')}
                  className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="is_active" className="text-sm font-medium text-slate-700 select-none">
                  Set as Current Session
                </label>
              </div>
              <p className="text-xs text-slate-500 ml-1">
                Note: Setting this as the current session will automatically unset the previous current session.
              </p>
            </div>

            <div className="flex justify-end gap-3 pt-6 border-t border-slate-200">
              <button 
                type="button" 
                onClick={() => setIsModalOpen(false)}
                className="px-5 py-2.5 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                Cancel
              </button>
              <button 
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
                className="flex items-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-70 disabled:cursor-not-allowed shadow-lg shadow-blue-200"
              >
                {(createMutation.isPending || updateMutation.isPending) && <Loader2 className="w-4 h-4 animate-spin" />}
                {editingItem ? 'Save Changes' : 'Create Session'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      {isDeleteModalOpen && selectedItem && (
        <Modal title="Confirm Deletion" onClose={() => !deleteMutation.isPending && setIsDeleteModalOpen(false)}>
          <div className="p-2">
            <div className="flex items-center gap-4 text-amber-600 bg-amber-50 p-4 rounded-xl mb-6">
              <AlertCircle size={24} className="shrink-0" />
              <p className="text-sm">
                Are you sure you want to delete <span className="font-bold">{selectedItem.session_name}</span>? <br/>
                <span className="font-medium">This session may be linked with Students.</span> Deletion is not allowed if active links exist.
              </p>
            </div>
            
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setIsDeleteModalOpen(false)}
                className="px-5 py-2.5 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
                disabled={deleteMutation.isPending}
              >
                Cancel
              </button>
              <button 
                onClick={() => deleteMutation.mutate(selectedItem.id)}
                disabled={deleteMutation.isPending}
                className="flex items-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-red-600 rounded-xl hover:bg-red-700 transition-colors disabled:opacity-70 disabled:cursor-not-allowed shadow-lg shadow-red-200"
              >
                {deleteMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                Yes, Delete
              </button>
            </div>
          </div>
        </Modal>
      )}

    </div>
  );
}
