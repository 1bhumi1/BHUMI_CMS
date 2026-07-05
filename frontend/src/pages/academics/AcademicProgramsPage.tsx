import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api';
import PermissionGuard from '../../components/PermissionGuard';
import {
  Plus, Search, Edit2, Trash2, Loader2, ChevronLeft, ChevronRight,
  X, Check, AlertCircle, Eye, Download, BookOpen, ArrowUpDown, ArrowUp, ArrowDown, Filter
} from 'lucide-react';

// Interfaces
interface Department {
  id: number;
  name: string;
  code: string;
}

interface Program {
  id: number;
  name: string;
  code: string;
}

interface Specialization {
  id: number;
  name: string;
  code: string;
}

interface AcademicProgramItem {
  id: number;
  department: Department | null;
  program: Program | null;
  specialization: Specialization | null;
  duration_years: number;
  total_semesters: number;
  entry_semester: number;
}

interface AcademicProgramFormData {
  department_id: string;
  program_id: string;
  specialization_id: string;
  duration_years: string;
  total_semesters: string;
  entry_semester: string;
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
    <div className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col animate-fade-in-up">
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

export default function AcademicProgramManagement() {
  const queryClient = useQueryClient();
  
  // State
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [sortBy, setSortBy] = useState('newest');
  const [sortOrder, setSortOrder] = useState<'asc'|'desc'>('desc');
  
  // Filters
  const [filterDept, setFilterDept] = useState('');
  const [filterProg, setFilterProg] = useState('');
  const [filterSpec, setFilterSpec] = useState('');

  // UI State
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<AcademicProgramItem | null>(null);
  const [editingItem, setEditingItem] = useState<AcademicProgramItem | null>(null);

  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm<AcademicProgramFormData>();

  const selectedDept = watch("department_id");
  const selectedProg = watch("program_id");

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Queries
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: async () => {
      const res = await api.get('/academic-programs/dropdown/departments');
      return res.data?.data?.departments || [];
    }
  });

  const { data: filterPrograms = [] } = useQuery({
    queryKey: ['programs', filterDept],
    queryFn: async () => {
      const res = await api.get(`/academic-programs/dropdown/programs/${filterDept}`);
      return res.data?.data?.programs || [];
    },
    enabled: !!filterDept
  });

  const { data: formPrograms = [] } = useQuery({
    queryKey: ['programs', selectedDept],
    queryFn: async () => {
      const res = await api.get(`/academic-programs/dropdown/programs/${selectedDept}`);
      return res.data?.data?.programs || [];
    },
    enabled: !!selectedDept
  });

  const { data: filterSpecializations = [] } = useQuery({
    queryKey: ['specializations', filterProg],
    queryFn: async () => {
      const res = await api.get(`/academic-programs/dropdown/specializations/${filterProg}`);
      return res.data?.data?.specializations || [];
    },
    enabled: !!filterProg
  });

  const { data: formSpecializations = [] } = useQuery({
    queryKey: ['specializations', selectedProg],
    queryFn: async () => {
      const res = await api.get(`/academic-programs/dropdown/specializations/${selectedProg}`);
      return res.data?.data?.specializations || [];
    },
    enabled: !!selectedProg
  });

  const { data: programsData, isLoading } = useQuery({
    queryKey: ['academic-programs', { page, limit, search: debouncedSearch, sortBy, sortOrder, filterDept, filterProg, filterSpec }],
    queryFn: async () => {
      const skip = (page - 1) * limit;
      let url = `/academic-programs?skip=${skip}&limit=${limit}&sort_by=${sortBy}&sort_order=${sortOrder}`;
      if (debouncedSearch) url += `&search=${encodeURIComponent(debouncedSearch)}`;
      if (filterDept) url += `&department_id=${filterDept}`;
      if (filterProg) url += `&program_id=${filterProg}`;
      if (filterSpec) url += `&specialization_id=${filterSpec}`;
      const res = await api.get(url);
      return res.data?.data || { items: [], total: 0 };
    },
  });

  const items: AcademicProgramItem[] = programsData?.items || [];
  const totalPages = programsData?.total ? Math.ceil(programsData.total / limit) : 1;

  // Mutations
  const createMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await api.post('/academic-programs/', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic-programs'] });
      setToast({ message: 'Academic Program created successfully', type: 'success' });
      setIsModalOpen(false);
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || err.response?.data?.message || 'Creation failed', type: 'error' });
    }
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number, payload: any }) => {
      const res = await api.put(`/academic-programs/${id}`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic-programs'] });
      setToast({ message: 'Academic Program updated successfully', type: 'success' });
      setIsModalOpen(false);
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || err.response?.data?.message || 'Update failed', type: 'error' });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/academic-programs/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['academic-programs'] });
      setToast({ message: 'Academic Program deleted successfully', type: 'success' });
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
      department_id: '',
      program_id: '',
      specialization_id: '',
      duration_years: '',
      total_semesters: '',
      entry_semester: '1'
    });
    setIsModalOpen(true);
  };

  const openEditModal = (item: AcademicProgramItem) => {
    setEditingItem(item);
    reset({
      department_id: item.department?.id.toString() || '',
      program_id: item.program?.id.toString() || '',
      specialization_id: item.specialization?.id.toString() || '',
      duration_years: item.duration_years.toString(),
      total_semesters: item.total_semesters.toString(),
      entry_semester: item.entry_semester.toString()
    });
    setIsModalOpen(true);
  };
  
  const openViewModal = (item: AcademicProgramItem) => {
    setSelectedItem(item);
    setIsViewModalOpen(true);
  };

  const onSubmit = (data: AcademicProgramFormData) => {
    const payload = {
      department_id: parseInt(data.department_id),
      program_id: parseInt(data.program_id),
      specialization_id: data.specialization_id ? parseInt(data.specialization_id) : null,
      duration_years: parseInt(data.duration_years),
      total_semesters: parseInt(data.total_semesters),
      entry_semester: parseInt(data.entry_semester)
    };

    if (editingItem) {
      updateMutation.mutate({ id: editingItem.id, payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const confirmDelete = (item: AcademicProgramItem) => {
    setSelectedItem(item);
    setIsDeleteModalOpen(true);
  };

  const handleExport = async () => {
    try {
      const response = await api.get('/academic-programs/export?format=csv', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'academic_programs.csv');
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
              <BookOpen className="text-blue-600" size={32} />
              Academic Programs
            </h1>
            <p className="text-slate-500 mt-1">Manage departments, programs, and specializations</p>
          </div>
          <div className="flex gap-3 w-full sm:w-auto">
            <PermissionGuard permission="academic_program.read">
              <button 
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
              >
                <Download size={18} />
                Export
              </button>
            </PermissionGuard>
            <PermissionGuard permission="academic_program.create">
              <button 
                onClick={openCreateModal}
                className="flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all shadow-lg shadow-blue-200 active:scale-95 font-medium flex-1 sm:flex-none"
              >
                <Plus size={18} />
                New Program
              </button>
            </PermissionGuard>
          </div>
        </div>

        {/* Toolbar & Filters */}
        <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="relative w-full md:w-1/3">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
              <input
                type="text"
                placeholder="Search programs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
              />
            </div>
            
            <div className="flex items-center gap-3 w-full md:w-2/3 flex-wrap md:flex-nowrap">
              <div className="flex items-center gap-2 w-full">
                <Filter size={18} className="text-slate-400 shrink-0 hidden md:block" />
                <select 
                  value={filterDept} 
                  onChange={(e) => { setFilterDept(e.target.value); setFilterProg(''); setFilterSpec(''); setPage(1); }}
                  className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all text-sm"
                >
                  <option value="">All Departments</option>
                  {departments.map((d: any) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="w-full">
                <select 
                  value={filterProg} 
                  onChange={(e) => { setFilterProg(e.target.value); setFilterSpec(''); setPage(1); }}
                  disabled={!filterDept}
                  className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all text-sm disabled:opacity-50"
                >
                  <option value="">All Programs</option>
                  {filterPrograms.map((p: any) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="w-full">
                <select 
                  value={filterSpec} 
                  onChange={(e) => { setFilterSpec(e.target.value); setPage(1); }}
                  disabled={!filterProg}
                  className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all text-sm disabled:opacity-50"
                >
                  <option value="">All Specializations</option>
                  {filterSpecializations.map((s: any) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 flex-1 flex flex-col overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                <tr>
                  <th className="px-6 py-4 font-semibold cursor-pointer group select-none" onClick={() => handleSort('department')}>
                    <div className="flex items-center">Department <SortIcon field="department" /></div>
                  </th>
                  <th className="px-6 py-4 font-semibold cursor-pointer group select-none" onClick={() => handleSort('program')}>
                    <div className="flex items-center">Program <SortIcon field="program" /></div>
                  </th>
                  <th className="px-6 py-4 font-semibold cursor-pointer group select-none" onClick={() => handleSort('specialization')}>
                    <div className="flex items-center">Specialization <SortIcon field="specialization" /></div>
                  </th>
                  <th className="px-6 py-4 font-semibold cursor-pointer group select-none" onClick={() => handleSort('duration_years')}>
                    <div className="flex items-center">Duration (Yrs) <SortIcon field="duration_years" /></div>
                  </th>
                  <th className="px-6 py-4 font-semibold cursor-pointer group select-none" onClick={() => handleSort('total_semesters')}>
                    <div className="flex items-center">Semesters <SortIcon field="total_semesters" /></div>
                  </th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center">
                      <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
                      <p className="text-slate-500">Loading programs...</p>
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                      No academic programs found
                    </td>
                  </tr>
                ) : (
                  items.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50/80 transition-colors group">
                      <td className="px-6 py-4 text-slate-700">{item.department?.name}</td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                          {item.program?.name}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-600">{item.specialization?.name || '-'}</td>
                      <td className="px-6 py-4 text-slate-600">{item.duration_years}</td>
                      <td className="px-6 py-4 text-slate-600">{item.total_semesters}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <PermissionGuard permission="academic_program.read">
                            <button onClick={() => openViewModal(item)} className="p-1.5 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors" title="View">
                              <Eye size={16} />
                            </button>
                          </PermissionGuard>
                          <PermissionGuard permission="academic_program.update">
                            <button onClick={() => openEditModal(item)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                              <Edit2 size={16} />
                            </button>
                          </PermissionGuard>
                          <PermissionGuard permission="academic_program.delete">
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
        <Modal title="View Academic Program" onClose={() => setIsViewModalOpen(false)}>
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-500">Department</p>
                <p className="font-medium text-slate-900">{selectedItem.department?.name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Program</p>
                <p className="font-medium text-slate-900">{selectedItem.program?.name}</p>
              </div>
              <div className="col-span-2">
                <p className="text-sm text-slate-500">Specialization</p>
                <p className="font-medium text-slate-900">{selectedItem.specialization?.name || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Duration</p>
                <p className="font-medium text-slate-900">{selectedItem.duration_years} Years</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Semesters</p>
                <p className="font-medium text-slate-900">{selectedItem.total_semesters}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Entry Semester</p>
                <p className="font-medium text-slate-900">{selectedItem.entry_semester}</p>
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
        <Modal title={editingItem ? 'Edit Academic Program' : 'Create Academic Program'} onClose={() => setIsModalOpen(false)}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-slate-900 border-b pb-2">Academic Information</h4>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Department *</label>
                  <select 
                    {...register('department_id', { required: 'Department is required' })} 
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  >
                    <option value="">Select Department</option>
                    {departments.map((d: any) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                  {errors.department_id && <p className="text-red-500 text-xs mt-1">{errors.department_id.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Program *</label>
                  <select 
                    {...register('program_id', { required: 'Program is required' })} 
                    disabled={!selectedDept}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 disabled:opacity-50"
                  >
                    <option value="">Select Program</option>
                    {formPrograms.map((p: any) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                  {errors.program_id && <p className="text-red-500 text-xs mt-1">{errors.program_id.message}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Specialization (Optional)</label>
                  <select 
                    {...register('specialization_id')} 
                    disabled={!selectedProg}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 disabled:opacity-50"
                  >
                    <option value="">No Specialization / Select Specialization</option>
                    {formSpecializations.map((s: any) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-slate-900 border-b pb-2">Curriculum</h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Duration (Years) *</label>
                  <input 
                    type="number" 
                    min="1"
                    {...register('duration_years', { required: 'Required', min: 1 })}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                  {errors.duration_years && <p className="text-red-500 text-xs mt-1">{errors.duration_years.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Total Semesters *</label>
                  <input 
                    type="number" 
                    min="1"
                    {...register('total_semesters', { required: 'Required', min: 1 })}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                  {errors.total_semesters && <p className="text-red-500 text-xs mt-1">{errors.total_semesters.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Entry Semester *</label>
                  <input 
                    type="number" 
                    min="1"
                    {...register('entry_semester', { required: 'Required', min: 1 })}
                    className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                  {errors.entry_semester && <p className="text-red-500 text-xs mt-1">{errors.entry_semester.message}</p>}
                </div>
              </div>
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
                {editingItem ? 'Save Changes' : 'Create Program'}
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
                Are you sure you want to delete this Academic Program? <br/>
                <span className="font-medium">This Academic Program may be linked with Students.</span> Deletion is not allowed if active links exist.
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
