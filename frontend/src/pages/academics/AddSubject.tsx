import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { useAuth } from '../../lib/AuthContext';
import {
  Plus, Edit2, Trash2, BookMarked, Search, Loader2, ChevronLeft,
  ChevronRight, Check, AlertCircle, X, Filter
} from 'lucide-react';

// Form validation schema with Zod
const subjectFormSchema = z.object({
  academic_session_id: z.coerce.number().min(1, 'Academic Session is required'),
  academic_session_half: z.string().min(1, 'Academic Session period is required'),
  semester: z.coerce.number().min(1, 'Semester is required'),
  subject_category: z.string().min(1, 'Subject Category is required'),
  univ_category_code: z.string().min(1, 'Category Code is required'),
  univ_subject_code_prefix: z.string().min(1, 'Subject Code Prefix is required'),
  univ_subject_code_number: z.string().min(1, 'Subject Code Number is required'),
  univ_subject_code_suffix: z.string().min(1, 'Suffix is required'),
  subject_name: z.string().min(1, 'Subject Name is required').max(150, 'Subject Name cannot exceed 150 characters'),
  subject_type: z.string().min(1, 'Subject Type is required'),
  active: z.coerce.number().default(1)
});

type SubjectFormValues = z.infer<typeof subjectFormSchema>;

const defaultValues: SubjectFormValues = {
  academic_session_id: 0,
  academic_session_half: '',
  semester: 0,
  subject_category: '',
  univ_category_code: '',
  univ_subject_code_prefix: '',
  univ_subject_code_number: '',
  univ_subject_code_suffix: 'NO',
  subject_name: '',
  subject_type: '',
  active: 1
};

export default function AddSubject() {
  const { role } = useAuth();
  const queryClient = useQueryClient();

  // Route Guard: Only HOD can access
  if (role !== 'HOD') {
    return <Navigate to="/unauthorized" replace />;
  }

  // Toast notifications state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  
  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Form setup
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors }
  } = useForm<SubjectFormValues>({
    resolver: zodResolver(subjectFormSchema),
    defaultValues
  });

  const watchedCategory = watch('subject_category');
  const watchedSessionId = watch('academic_session_id');
  const watchedSessionHalf = watch('academic_session_half');

  // We maintain selected session option in a state formatted as "id_half" to drive both fields
  const [selectedSessionOption, setSelectedSessionOption] = useState<string>('');

  // View subjects filters & pagination state
  const [filterSessionVal, setFilterSessionVal] = useState<string>('');
  const [filterSemester, setFilterSemester] = useState<string>('');
  const [filterSearch, setFilterSearch] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');
  const [page, setPage] = useState(1);
  const limit = 10;

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(filterSearch);
      setPage(1);
    }, 500);
    return () => clearTimeout(handler);
  }, [filterSearch]);

  // Load master data from DB
  const { data: sessionsData = [] } = useQuery({
    queryKey: ['academic-sessions-dropdown'],
    queryFn: async () => {
      const res = await api.get('/academic-sessions/dropdown');
      return res.data?.data?.sessions || [];
    }
  });

  const { data: categoriesRes = [] } = useQuery({
    queryKey: ['subject-categories'],
    queryFn: async () => {
      const res = await api.get('/academic/subject-categories');
      return res.data?.data || [];
    }
  });

  const { data: codePrefixesRes = [] } = useQuery({
    queryKey: ['subject-code-prefixes'],
    queryFn: async () => {
      const res = await api.get('/academic/subject-code-prefixes');
      return res.data?.data || [];
    }
  });

  const { data: classificationsRes = [] } = useQuery({
    queryKey: ['subject-classifications'],
    queryFn: async () => {
      const res = await api.get('/academic/subject-classifications');
      return res.data?.data || [];
    }
  });

  const { data: typesRes = [] } = useQuery({
    queryKey: ['subject-types'],
    queryFn: async () => {
      const res = await api.get('/academic/subject-types');
      return res.data?.data || [];
    }
  });

  // Fetch paginated subjects list
  const [filterSessionId, filterSessionHalf] = filterSessionVal ? filterSessionVal.split('_') : [undefined, undefined];
  const { data: subjectsData, isLoading: subjectsLoading } = useQuery({
    queryKey: ['subjects', { page, limit, search: debouncedSearch, sessionId: filterSessionId, semester: filterSemester }],
    queryFn: async () => {
      let url = `/academic/subjects?skip=${(page - 1) * limit}&limit=${limit}`;
      if (debouncedSearch) url += `&search=${encodeURIComponent(debouncedSearch)}`;
      if (filterSessionId) url += `&academic_session_id=${filterSessionId}`;
      if (filterSemester) url += `&semester=${filterSemester}`;
      const res = await api.get(url);
      return res.data?.data || { items: [], total: 0 };
    }
  });

  const subjects = subjectsData?.items || [];
  const total = subjectsData?.total || 0;
  const totalPages = Math.ceil(total / limit) || 1;

  // Process Academic Sessions options (dynamic format with July-Dec and Jan-June)
  const sessionOptions = React.useMemo(() => {
    const list: Array<{ id: number; half: string; name: string }> = [];
    sessionsData.forEach((s: any) => {
      // e.g. "2025-26" -> "2025-2026"
      let formattedName = s.name;
      const match = s.name.match(/^(\d{4})-(\d{2})$/);
      if (match) {
        const year1 = match[1];
        const year2 = parseInt(match[2]);
        formattedName = `${year1}-20${year2}`;
      }
      
      list.push({
        id: s.id,
        half: 'July-Dec',
        name: `${formattedName} (July-Dec)`
      });
      list.push({
        id: s.id,
        half: 'Jan-June',
        name: `${formattedName} (Jan-June)`
      });
    });
    return list;
  }, [sessionsData]);

  // Semester dropdown options change dynamically based on July-Dec vs Jan-June
  const semesterOptions = React.useMemo(() => {
    if (watchedSessionHalf === 'July-Dec') {
      return [1, 3, 5, 7];
    } else if (watchedSessionHalf === 'Jan-June') {
      return [2, 4, 6, 8];
    }
    return [];
  }, [watchedSessionHalf]);

  // Reset semester selection instantly when academic session half changes
  useEffect(() => {
    setValue('semester', 0, { shouldValidate: isEditing });
  }, [watchedSessionHalf, setValue, isEditing]);

  const handleSessionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedSessionOption(val);
    if (val) {
      const [id, half] = val.split('_');
      setValue('academic_session_id', Number(id), { shouldValidate: true });
      setValue('academic_session_half', half, { shouldValidate: true });
    } else {
      setValue('academic_session_id', 0);
      setValue('academic_session_half', '');
    }
  };

  // Mutations
  const createMutation = useMutation({
    mutationFn: async (payload: SubjectFormValues) => {
      const res = await api.post('/academic/subjects', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] });
      setToast({ message: 'Subject added successfully', type: 'success' });
      reset(defaultValues);
      setSelectedSessionOption('');
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || 'Failed to add subject', type: 'error' });
    }
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: SubjectFormValues }) => {
      const res = await api.put(`/academic/subjects/${id}`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] });
      setToast({ message: 'Subject updated successfully', type: 'success' });
      setIsEditing(false);
      setEditingId(null);
      reset(defaultValues);
      setSelectedSessionOption('');
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || 'Failed to update subject', type: 'error' });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/academic/subjects/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] });
      setToast({ message: 'Subject deleted successfully', type: 'success' });
      if (subjects.length === 1 && page > 1) {
        setPage(page - 1);
      }
    },
    onError: (err: any) => {
      setToast({ message: err.response?.data?.detail || 'Failed to delete subject', type: 'error' });
    }
  });

  const onSubmit = (data: SubjectFormValues) => {
    if (isEditing && editingId) {
      updateMutation.mutate({ id: editingId, payload: data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleEditClick = (sub: any) => {
    setIsEditing(true);
    setEditingId(sub.id);
    reset({
      academic_session_id: sub.academic_session_id,
      academic_session_half: sub.academic_session_half,
      semester: sub.semester,
      subject_category: sub.subject_category,
      univ_category_code: sub.univ_category_code || '',
      univ_subject_code_prefix: sub.univ_subject_code_prefix || '',
      univ_subject_code_number: sub.univ_subject_code_number || '',
      univ_subject_code_suffix: sub.univ_subject_code_suffix || '',
      subject_name: sub.subject_name,
      subject_type: sub.subject_type,
      active: sub.active
    });
    setSelectedSessionOption(`${sub.academic_session_id}_${sub.academic_session_half}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditingId(null);
    reset(defaultValues);
    setSelectedSessionOption('');
  };

  const handleDeleteClick = (id: number) => {
    if (window.confirm('Are you sure you want to delete this subject?')) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50 min-h-screen">
      <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in">
        {toast && (
          <div className={`fixed top-6 right-6 z-[100] flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl text-white text-sm font-semibold animate-slide-in ${
            toast.type === 'success' ? 'bg-emerald-600' : 'bg-red-600'
          }`}>
            {toast.type === 'success' ? <Check size={18} /> : <AlertCircle size={18} />}
            {toast.message}
            <button onClick={() => setToast(null)} className="ml-2 hover:opacity-75"><X size={16} /></button>
          </div>
        )}

        {/* Form Container */}
        <div className="bg-white rounded-2xl shadow-md border border-slate-100 p-6 md:p-8 space-y-6 transition-all hover:shadow-lg">
          {/* Header & Session selector */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              <BookMarked className="text-blue-600 animate-pulse" /> {isEditing ? 'Edit Subject:' : 'Add Subject:'}
            </h2>
            
            <div className="flex items-center gap-2">
              <label className="text-sm font-semibold text-slate-600">Academic Session *</label>
              <select
                value={selectedSessionOption}
                onChange={handleSessionChange}
                className="px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all cursor-pointer"
              >
                <option value="">Select Session</option>
                {sessionOptions.map((opt) => (
                  <option key={`${opt.id}_${opt.half}`} value={`${opt.id}_${opt.half}`}>
                    {opt.name}
                  </option>
                ))}
              </select>
              {errors.academic_session_id && (
                <span className="text-xs text-red-500 font-bold ml-1">Required</span>
              )}
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Subject Category Radio Buttons */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Subject Category *</label>
              <div className="flex flex-wrap gap-6 items-center">
                {classificationsRes.map((cls: any) => (
                  <label key={cls.id} className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer font-medium hover:text-blue-600 transition-colors">
                    <input
                      type="radio"
                      value={cls.name}
                      checked={watchedCategory === cls.name}
                      onChange={() => setValue('subject_category', cls.name, { shouldValidate: true })}
                      className="w-4 h-4 text-blue-600 border-slate-300 focus:ring-blue-500 transition-all cursor-pointer"
                    />
                    {cls.name}
                  </label>
                ))}
              </div>
              {errors.subject_category && (
                <p className="mt-1 text-xs text-red-500 font-medium">{errors.subject_category.message}</p>
              )}
            </div>

            {/* University Subject Code (4 parts) */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">University Subject Code *</label>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <select
                  {...register('univ_category_code')}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer"
                >
                  <option value="">Select Category</option>
                  {categoriesRes.map((c: any) => (
                    <option key={c.id} value={c.category_code}>
                      {c.category_code}
                    </option>
                  ))}
                </select>
                
                <select
                  {...register('univ_subject_code_prefix')}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer"
                >
                  <option value="">Select Code</option>
                  {codePrefixesRes.map((c: any) => (
                    <option key={c.id} value={c.sub_code}>
                      {c.sub_code}
                    </option>
                  ))}
                </select>
                
                <input
                  type="text"
                  placeholder="e.g. 501"
                  {...register('univ_subject_code_number')}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                />
                
                <input
                  type="text"
                  placeholder="NO"
                  {...register('univ_subject_code_suffix')}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all bg-slate-50 text-slate-600 font-semibold"
                />
              </div>
              {(errors.univ_category_code || errors.univ_subject_code_prefix || errors.univ_subject_code_number || errors.univ_subject_code_suffix) && (
                <p className="mt-1.5 text-xs text-red-500 font-medium">
                  {errors.univ_category_code?.message || errors.univ_subject_code_prefix?.message || errors.univ_subject_code_number?.message || errors.univ_subject_code_suffix?.message || 'Subject Code fields are required'}
                </p>
              )}
            </div>

            {/* Subject Name */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Subject Name *</label>
              <input
                type="text"
                placeholder="Subject Name"
                {...register('subject_name')}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              />
              {errors.subject_name && (
                <p className="mt-1 text-xs text-red-500 font-medium">{errors.subject_name.message}</p>
              )}
            </div>

            {/* Subject Type */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Subject Type *</label>
              <select
                {...register('subject_type')}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer"
              >
                <option value="">Select Subject Type</option>
                {typesRes.map((t: any) => (
                  <option key={t.id} value={t.name}>
                    {t.name}
                  </option>
                ))}
              </select>
              {errors.subject_type && (
                <p className="mt-1 text-xs text-red-500 font-medium">{errors.subject_type.message}</p>
              )}
            </div>

            {/* Semester */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Semester *</label>
              <select
                {...register('semester')}
                disabled={!watchedSessionHalf}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all disabled:opacity-60 cursor-pointer"
              >
                <option value="">Select Semester</option>
                {semesterOptions.map((sem) => (
                  <option key={sem} value={sem}>
                    {sem}
                  </option>
                ))}
              </select>
              {errors.semester && (
                <p className="mt-1 text-xs text-red-500 font-medium">{errors.semester.message}</p>
              )}
            </div>

            {/* Submit Actions */}
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold shadow-sm hover:shadow transition-all flex items-center gap-2 cursor-pointer disabled:opacity-75"
              >
                {(createMutation.isPending || updateMutation.isPending) && (
                  <Loader2 size={16} className="animate-spin" />
                )}
                {isEditing ? 'Update Subject' : 'Submit'}
              </button>
              
              {isEditing && (
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="px-6 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-sm font-semibold transition-colors cursor-pointer"
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>

        {/* View Subjects Section */}
        <div className="bg-white rounded-2xl shadow-md border border-slate-100 p-6 md:p-8 space-y-6">
          <div>
            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
              <ClipboardList className="text-blue-600" /> View Subjects
            </h2>
            <p className="text-sm text-slate-500 mt-1">Search, filter, and manage existing subjects</p>
          </div>

          {/* Filters Toolbar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Academic Session</label>
              <select
                value={filterSessionVal}
                onChange={(e) => { setFilterSessionVal(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer"
              >
                <option value="">All Sessions</option>
                {sessionOptions.map((opt) => (
                  <option key={`filter_${opt.id}_${opt.half}`} value={`${opt.id}_${opt.half}`}>
                    {opt.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Semester</label>
              <select
                value={filterSemester}
                onChange={(e) => { setFilterSemester(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer"
              >
                <option value="">All Semesters</option>
                {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => (
                  <option key={`filter_sem_${sem}`} value={sem}>
                    Semester {sem}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Search Code / Name</label>
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Type to search..."
                  value={filterSearch}
                  onChange={(e) => setFilterSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                />
              </div>
            </div>
          </div>

          {/* Subjects Table */}
          <div className="overflow-x-auto border border-slate-100 rounded-xl">
            {subjectsLoading ? (
              <div className="p-12 text-center text-slate-500 flex flex-col items-center gap-2">
                <Loader2 size={32} className="animate-spin text-blue-600" />
                <span>Loading subjects list...</span>
              </div>
            ) : (
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                    <th className="px-6 py-3.5 font-bold text-slate-600">Subject Code</th>
                    <th className="px-6 py-3.5 font-bold text-slate-600">Subject Name</th>
                    <th className="px-6 py-3.5 font-bold text-slate-600">Session</th>
                    <th className="px-6 py-3.5 font-bold text-slate-600">Semester</th>
                    <th className="px-6 py-3.5 font-bold text-slate-600">Category</th>
                    <th className="px-6 py-3.5 font-bold text-slate-600">Type</th>
                    <th className="px-6 py-3.5 font-bold text-slate-600 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {subjects.map((sub: any) => {
                    // Format session name
                    let sessName = '-';
                    if (sub.academic_session?.session_name) {
                      let formatted = sub.academic_session.session_name;
                      const match = formatted.match(/^(\d{4})-(\d{2})$/);
                      if (match) {
                        formatted = `${match[1]}-20${match[2]}`;
                      }
                      sessName = `${formatted} (${sub.academic_session_half || ''})`;
                    }

                    return (
                      <tr key={sub.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 font-semibold text-slate-800">{sub.subject_code}</td>
                        <td className="px-6 py-4 text-slate-600 font-medium">{sub.subject_name}</td>
                        <td className="px-6 py-4 text-slate-500 text-xs font-semibold">{sessName}</td>
                        <td className="px-6 py-4 text-slate-600 font-medium">Semester {sub.semester || '-'}</td>
                        <td className="px-6 py-4">
                          <span className="inline-flex px-2 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
                            {sub.subject_category || '-'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex px-2 py-1 rounded-full text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200">
                            {sub.subject_type || '-'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex justify-end gap-1.5">
                            <button
                              onClick={() => handleEditClick(sub)}
                              className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all cursor-pointer"
                              title="Edit Subject"
                            >
                              <Edit2 size={16} />
                            </button>
                            <button
                              onClick={() => handleDeleteClick(sub.id)}
                              className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all cursor-pointer"
                              title="Delete Subject"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {subjects.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-6 py-12 text-center text-slate-400 font-medium">
                        No subjects found matching the filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <span className="text-sm text-slate-500 font-medium">
                Showing Page {page} of {totalPages} ({total} total subjects)
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                  className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage(page + 1)}
                  className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Icon helper that wasn't imported from lucide-react directly
const ClipboardList = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    style={{ width: '1.25rem', height: '1.25rem' }}
  >
    <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
    <path d="M12 11h4" />
    <path d="M12 16h4" />
    <path d="M8 11h.01" />
    <path d="M8 16h.01" />
  </svg>
);
