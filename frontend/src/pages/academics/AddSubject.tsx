import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { api } from '../../lib/api';
import { useAuth } from '../../lib/AuthContext';
import { Navigate } from 'react-router-dom';
import { 
  BookMarked, Plus, Edit2, Trash2, Search, Filter, 
  RotateCcw, X, ChevronLeft, ChevronRight, CheckCircle, AlertTriangle
} from 'lucide-react';
import Toast from '../../components/Toast';
import { useAcademicSession } from '../../lib/AcademicSessionContext';

// Form Data Type Definition matching the detailed database schema
type SubjectFormData = {
  academic_session: string;
  category: 'Compulsory Subject' | 'Department Subject' | 'Open Elective Subject';
  subject_category_id: string;
  subject_code_id: string;
  sequence_number: string;
  university_subject_code: string;
  subject_code: string;
  subject_name: string;
  subject_type: string;
  semester: string;
  department_id: string; // empty string represents null/not selected
  active: number;
};

type Department = { id: number; name: string; dept_code: string };

type DBSubjectCategory = {
  id: number;
  category: string;
  category_code: string;
  active: number;
};

type DBSubjectCode = {
  id: number;
  sub_code: string;
  hod_computer_code: number | null;
  department: number | null;
};

// Fixed Frontend Constants as per constraints
const SUBJECT_TYPES = ["Theory", "Practical", "Non-Credit Theory", "Non-Credit Practical"];
const SEMESTERS = ["1", "2", "3", "4", "5", "6", "7", "8"];

const AddSubject = () => {
  const { role } = useAuth();
  const queryClient = useQueryClient();

  // Route Guard: HOD only access
  if (role !== 'HOD') {
    return <Navigate to="/unauthorized" replace />;
  }

  // Toast notification state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Dynamic dropdown data
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loadingDepts, setLoadingDepts] = useState(true);

  // DB backed categories and subject codes
  const [dbCategories, setDbCategories] = useState<DBSubjectCategory[]>([]);
  const [dbSubjectCodes, setDbSubjectCodes] = useState<DBSubjectCode[]>([]);
  const [loadingDropdowns, setLoadingDropdowns] = useState(true);

  // Database session matching list
  const [dbSessions, setDbSessions] = useState<{ id: number; name: string }[]>([]);

  // Frontend datatable state populated from DB
  const [subjectsList, setSubjectsList] = useState<any[]>([]);
  const [totalSubjects, setTotalSubjects] = useState(0);
  const [loadingSubjects, setLoadingSubjects] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Table Pagination, Filters and Search State
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSemester, setFilterSemester] = useState('');
  const [filterDept, setFilterDept] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);

  const { currentSession } = useAcademicSession();

  // React Hook Form initialization
  const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm<SubjectFormData>({
    defaultValues: {
      academic_session: '',
      category: 'Compulsory Subject',
      subject_category_id: '',
      subject_code_id: '',
      sequence_number: '',
      university_subject_code: '',
      subject_code: '',
      subject_name: '',
      subject_type: '',
      semester: '',
      department_id: '',
      active: 1
    }
  });

  // Watch fields for conditional layout and calculations
  const selectedCategory = watch('category');
  const watchAcademicSession = watch('academic_session');
  const watchCategory = watch('subject_category_id');
  const watchCode = watch('subject_code_id');
  const watchSequence = watch('sequence_number');

  // Match selected top bar session name to database session ID
  const matchSessionToDBId = (sessionStr: string, sessionsList: { id: number; name: string }[]) => {
    if (!sessionStr) return null;
    const match = sessionStr.match(/^(\d{4})-(\d{4})/);
    if (!match) return null;
    const startYear = match[1]; // "2025"
    const endYearShort = match[2].slice(2); // "26"
    const targetName = `${startYear}-${endYearShort}`; // "2025-26"
    const found = sessionsList.find(s => s.name === targetName);
    return found ? found.id : null;
  };

  // Determine available semesters based on the selected academic session
  const getAvailableSemesters = (session: string) => {
    if (!session) return [];
    if (session.includes('Jan-Jun') || session.includes('Jan-June')) {
      return ['2', '4', '6', '8'];
    }
    if (session.includes('July-Dec')) {
      return ['1', '3', '5', '7'];
    }
    return [];
  };

  const availableSemesters = getAvailableSemesters(watchAcademicSession);

  // Clear semester selection when Academic Session changes
  useEffect(() => {
    setValue('semester', '');
  }, [watchAcademicSession, setValue]);

  // Sync global session to form value
  useEffect(() => {
    setValue('academic_session', currentSession);
  }, [currentSession, setValue]);

  // Fetch subjects from the backend DB based on pagination, filters and search
  const fetchSubjects = async () => {
    if (dbSessions.length === 0) return;
    setLoadingSubjects(true);
    try {
      const sessionId = matchSessionToDBId(currentSession, dbSessions);
      const params: any = {
        skip: (currentPage - 1) * itemsPerPage,
        limit: itemsPerPage,
      };
      if (searchTerm) params.search = searchTerm;
      if (filterSemester) params.semester = Number(filterSemester);
      if (filterDept) params.department = Number(filterDept);
      if (sessionId) params.academic_session = sessionId;

      const res = await api.get('/academic/subjects', { params });
      setSubjectsList(res.data?.data?.items || []);
      setTotalSubjects(res.data?.data?.total || 0);
    } catch (e) {
      console.error('Failed to fetch subjects:', e);
      setToast({ message: 'Failed to load subjects from database', type: 'error' });
    } finally {
      setLoadingSubjects(false);
    }
  };

  // Load dropdown options and sessions on mount
  useEffect(() => {
    const loadDropdowns = async () => {
      setLoadingDepts(true);
      setLoadingDropdowns(true);
      try {
        const [deptRes, catRes, codeRes, sessionRes] = await Promise.all([
          api.get('/academic/departments'),
          api.get('/academic/subject-categories'),
          api.get('/academic/subject-codes'),
          api.get('/academic-sessions/dropdown')
        ]);
        setDepartments(deptRes.data?.data || []);
        
        // Active categories
        setDbCategories((catRes.data?.data || []).filter((c: any) => c.active === 1));
        setDbSubjectCodes(codeRes.data?.data || []);
        setDbSessions(sessionRes.data?.data?.sessions || []);
      } catch (e) {
        console.error('Error loading dropdown options:', e);
        setToast({ message: 'Error loading dropdown configurations', type: 'error' });
      } finally {
        setLoadingDepts(false);
        setLoadingDropdowns(false);
      }
    };
    loadDropdowns();
  }, []);

  // Fetch subjects whenever pagination or filters change
  useEffect(() => {
    fetchSubjects();
  }, [currentPage, searchTerm, filterSemester, filterDept, currentSession, dbSessions]);

  // Generate university subject code in real time
  useEffect(() => {
    const category = dbCategories.find(c => c.id === Number(watchCategory));
    const code = dbSubjectCodes.find(c => c.id === Number(watchCode));
    const seq = (watchSequence || '').trim();

    if (category && code && seq) {
      const generated = `${category.category_code}-${code.sub_code}-${seq}`;
      setValue('university_subject_code', generated);
    } else {
      setValue('university_subject_code', '');
    }
  }, [watchCategory, watchCode, watchSequence, dbCategories, dbSubjectCodes, setValue]);

  // Handle Form Submission (Real backend integration)
  const onSubmit = async (data: SubjectFormData) => {
    try {
      const sessionId = matchSessionToDBId(currentSession, dbSessions);
      if (!sessionId) {
        setToast({ message: 'Invalid academic session selected.', type: 'error' });
        return;
      }

      // Determine category code
      const cat = dbCategories.find(c => c.id === Number(data.subject_category_id));
      const categoryCode = cat ? cat.category_code : 'PCC';

      // Determine elective value
      const electiveVal = (categoryCode === 'PCC') ? 0 : 1;

      // Resolve selected sub_code from subject_code table
      const subCodeObj = dbSubjectCodes.find(c => c.id === Number(data.subject_code_id));
      const subCodeStr = subCodeObj ? subCodeObj.sub_code : '';

      const payload = {
        semester: Number(data.semester),
        academic_session: sessionId,
        clg_sub_code: data.subject_code, // College Subject Code user entered
        university_sub_code: data.university_subject_code, // Selected university subject code complete string
        subject_name: data.subject_name,
        type: data.subject_type,
        department: data.category !== 'Compulsory Subject' && data.department_id ? Number(data.department_id) : null,
        active: Number(data.active),
        elective: electiveVal,
        priority: categoryCode, // store category code in priority
        remark: cat ? cat.category : ''
      };

      if (editingId !== null) {
        await api.put(`/academic/subjects/${editingId}`, payload);
        setToast({ message: 'Subject updated successfully in database', type: 'success' });
        setEditingId(null);
      } else {
        await api.post('/academic/subjects', payload);
        setToast({ message: 'Subject created successfully in database', type: 'success' });
      }

      // Reset form
      handleFormReset();
      // Reload list
      fetchSubjects();
    } catch (e: any) {
      console.error('Error saving subject:', e);
      setToast({ message: e.response?.data?.detail || 'Error saving subject to database', type: 'error' });
    }
  };

  // Edit Mode Activation (pre-fills form)
  const handleEdit = (sub: any) => {
    setEditingId(sub.id);

    // Resolve category select values
    const catCode = sub.priority || 'PCC';
    const cat = dbCategories.find(c => c.category_code === catCode);
    const categorySelId = cat ? cat.id.toString() : '';

    // Resolve subject code select values
    const subCodeStr = sub.university_sub_code || '';
    let codeSelId = '';
    let seqStr = '';
    
    // Parse PCC-CS-01 to find CS in subject codes and 01 as sequence
    if (subCodeStr.includes('-')) {
      const parts = subCodeStr.split('-');
      if (parts.length === 3) {
        const [_, subCode, seq] = parts;
        const codeObj = dbSubjectCodes.find(c => c.sub_code === subCode);
        if (codeObj) codeSelId = codeObj.id.toString();
        seqStr = seq;
      }
    }

    // Set category string matching form
    let categoryName: any = 'Compulsory Subject';
    if (catCode === 'PEC') categoryName = 'Department Subject';
    if (catCode === 'OEC') categoryName = 'Open Elective Subject';

    reset({
      academic_session: currentSession,
      category: categoryName,
      subject_category_id: categorySelId,
      subject_code_id: codeSelId,
      sequence_number: seqStr,
      university_subject_code: subCodeStr,
      subject_code: sub.clg_sub_code || '', // College code
      subject_name: sub.subject_name || '',
      subject_type: sub.type || '',
      semester: sub.semester ? sub.semester.toString() : '',
      department_id: sub.department ? sub.department.toString() : '',
      active: sub.active
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Delete Action
  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this subject?')) {
      try {
        await api.delete(`/academic/subjects/${id}`);
        setToast({ message: 'Subject deleted successfully from database', type: 'success' });
        fetchSubjects();
        if (editingId === id) {
          setEditingId(null);
          handleFormReset();
        }
      } catch (e: any) {
        setToast({ message: e.response?.data?.detail || 'Error deleting subject', type: 'error' });
      }
    }
  };

  // Form Reset handler
  const handleFormReset = () => {
    reset({
      academic_session: currentSession,
      category: 'Compulsory Subject',
      subject_category_id: '',
      subject_code_id: '',
      sequence_number: '',
      university_subject_code: '',
      subject_code: '',
      subject_name: '',
      subject_type: '',
      semester: '',
      department_id: '',
      active: 1
    });
  };

  // Cancel Edit Mode
  const handleCancelEdit = () => {
    setEditingId(null);
    handleFormReset();
  };

  // Pagination calculation
  const totalPages = Math.ceil(totalSubjects / itemsPerPage) || 1;

  return (
    <div className="flex-1 min-h-screen bg-slate-50/50">
      <div className="p-8 max-w-6xl mx-auto space-y-8">
        
        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

        {/* Title and Header Banner */}
        <div className="flex justify-between items-center border-b border-slate-200 pb-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 flex items-center gap-3">
              <BookMarked className="text-blue-600 w-8 h-8" /> 
              <span>Add Subject</span>
            </h1>
            <p className="text-sm text-slate-500 mt-1">Configure, catalog and view academic course subjects</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
              Module: Schema Management
            </span>
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

        {/* Card Form */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-md">
          <div className="p-6 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <Plus className="text-blue-600" /> 
              <span>{editingId !== null ? 'Modify Subject Record' : 'Configure New Subject'}</span>
            </h2>
            {editingId !== null && (
              <span className="px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-100 rounded-full text-xxs font-bold animate-pulse">
                Editing Mode Active
              </span>
            )}
          </div>

          <form id="subject-form" onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
            
            {/* 1. Subject Category (Radio Buttons) */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-slate-700">Subject Category *</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { value: 'Compulsory Subject', label: 'Compulsory Subject', desc: 'Required for all students in the cohort' },
                  { value: 'Department Subject', label: 'Department Subject', desc: 'Core subject specific to a chosen department' },
                  { value: 'Open Elective Subject', label: 'Open Elective Subject', desc: 'Interdisciplinary elective open across college' }
                ].map(opt => (
                  <label 
                    key={opt.value} 
                    className={`flex flex-col p-4 border rounded-xl cursor-pointer transition-all duration-200 hover:border-blue-400 ${
                      selectedCategory === opt.value 
                        ? 'border-blue-600 bg-blue-50/40 ring-1 ring-blue-500' 
                        : 'border-slate-200 bg-white'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <input 
                        type="radio" 
                        value={opt.value}
                        {...register('category')}
                        className="w-4.5 h-4.5 text-blue-600 border-slate-300 focus:ring-blue-500" 
                      />
                      <span className="text-sm font-semibold text-slate-800">{opt.label}</span>
                    </div>
                    <span className="text-xs text-slate-500 mt-2 ml-7 leading-relaxed">{opt.desc}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 2. Dynamic University Subject Code Generator Row */}
            <div className="space-y-2.5 border border-slate-200 p-5 rounded-2xl bg-slate-50/30">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                University Subject Code Configuration *
              </label>
              
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                {/* A. Subject Category Dropdown */}
                <div className="space-y-1.5">
                  <label className="block text-xxs font-bold text-slate-500 uppercase tracking-wider">Category *</label>
                  <select
                    {...register('subject_category_id', { required: 'Category is required' })}
                    className={`w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-700 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${
                      errors.subject_category_id ? 'border-red-500 focus:ring-red-500/20' : 'border-slate-300'
                    }`}
                  >
                    <option value="">Select Category</option>
                    {dbCategories.map(cat => (
                      <option key={cat.id} value={cat.id}>{cat.category} ({cat.category_code})</option>
                    ))}
                  </select>
                  {errors.subject_category_id && (
                    <p className="text-xxs font-medium text-red-500 flex items-center gap-1 mt-0.5">
                      <AlertTriangle size={10} /> {errors.subject_category_id.message}
                    </p>
                  )}
                </div>

                {/* B. Subject Code Dropdown */}
                <div className="space-y-1.5">
                  <label className="block text-xxs font-bold text-slate-500 uppercase tracking-wider">Subject Code *</label>
                  <select
                    disabled={!watchCategory}
                    {...register('subject_code_id', { required: 'Subject code prefix is required' })}
                    className={`w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-700 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${
                      !watchCategory ? 'opacity-50 cursor-not-allowed bg-slate-100' : ''
                    } ${
                      errors.subject_code_id ? 'border-red-500 focus:ring-red-500/20' : 'border-slate-300'
                    }`}
                  >
                    <option value="">Select Code</option>
                    {dbSubjectCodes.map(code => (
                      <option key={code.id} value={code.id}>{code.sub_code}</option>
                    ))}
                  </select>
                  {errors.subject_code_id && (
                    <p className="text-xxs font-medium text-red-500 flex items-center gap-1 mt-0.5">
                      <AlertTriangle size={10} /> {errors.subject_code_id.message}
                    </p>
                  )}
                </div>

                {/* C. Subject Sequence Input */}
                <div className="space-y-1.5">
                  <label className="block text-xxs font-bold text-slate-500 uppercase tracking-wider">Sequence / Number *</label>
                  <input
                    type="text"
                    placeholder="e.g. 01"
                    disabled={!watchCode}
                    {...register('sequence_number', { 
                      required: 'Sequence number is required',
                      pattern: {
                        value: /^[0-9]+$/,
                        message: 'Digits only'
                      }
                    })}
                    className={`w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-700 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${
                      !watchCode ? 'opacity-50 cursor-not-allowed bg-slate-100' : ''
                    } ${
                      errors.sequence_number ? 'border-red-500 focus:ring-red-500/20' : 'border-slate-300'
                    }`}
                  />
                  {errors.sequence_number && (
                    <p className="text-xxs font-medium text-red-500 flex items-center gap-1 mt-0.5">
                      <AlertTriangle size={10} /> {errors.sequence_number.message}
                    </p>
                  )}
                </div>

                {/* D. Read-only Complete Subject Code */}
                <div className="space-y-1.5">
                  <label className="block text-xxs font-bold text-blue-600 uppercase tracking-wider">Complete Subject Code (Auto)</label>
                  <input
                    type="text"
                    readOnly
                    placeholder="Auto-generated"
                    {...register('university_subject_code')}
                    className="w-full px-3.5 py-2.5 bg-blue-50/50 border border-blue-200 rounded-xl text-sm font-bold text-blue-600 focus:outline-none cursor-not-allowed"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              
              {/* College Subject Code */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">College Subject Code *</label>
                <input
                  type="text"
                  placeholder="e.g. CS-402"
                  {...register('subject_code', { required: 'College subject code is required' })}
                  className={`w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${
                    errors.subject_code ? 'border-red-500 focus:ring-red-500/20' : 'border-slate-300'
                  }`}
                />
                {errors.subject_code && (
                  <p className="text-xs font-medium text-red-500 flex items-center gap-1 mt-1">
                    <AlertTriangle size={12} /> {errors.subject_code.message}
                  </p>
                )}
              </div>

              {/* Subject Name */}
              <div className="space-y-1.5 md:col-span-2">
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">Subject Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Artificial Intelligence"
                  {...register('subject_name', { required: 'Subject name is required' })}
                  className={`w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${
                    errors.subject_name ? 'border-red-500 focus:ring-red-500/20' : 'border-slate-300'
                  }`}
                />
                {errors.subject_name && (
                  <p className="text-xs font-medium text-red-500 flex items-center gap-1 mt-1">
                    <AlertTriangle size={12} /> {errors.subject_name.message}
                  </p>
                )}
              </div>

              {/* Subject Type */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">Subject Type *</label>
                <select
                  {...register('subject_type', { required: 'Subject type is required' })}
                  className={`w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${
                    errors.subject_type ? 'border-red-500 focus:ring-red-500/20' : 'border-slate-300'
                  }`}
                >
                  <option value="">Select Type</option>
                  {SUBJECT_TYPES.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                {errors.subject_type && (
                  <p className="text-xs font-medium text-red-500 flex items-center gap-1 mt-1">
                    <AlertTriangle size={12} /> {errors.subject_type.message}
                  </p>
                )}
              </div>

              {/* Semester */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">Semester *</label>
                <select
                  disabled={!watchAcademicSession}
                  {...register('semester', { required: 'Semester is required' })}
                  className={`w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${
                    !watchAcademicSession ? 'opacity-50 cursor-not-allowed bg-slate-100' : ''
                  } ${
                    errors.semester ? 'border-red-500 focus:ring-red-500/20' : 'border-slate-300'
                  }`}
                >
                  <option value="">Select Semester</option>
                  {availableSemesters.map(sem => (
                    <option key={sem} value={sem}>Semester {sem}</option>
                  ))}
                </select>
                {errors.semester && (
                  <p className="text-xs font-medium text-red-500 flex items-center gap-1 mt-1">
                    <AlertTriangle size={12} /> {errors.semester.message}
                  </p>
                )}
              </div>

              {/* Department */}
              {selectedCategory !== 'Compulsory Subject' ? (
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">Department *</label>
                  <select
                    {...register('department_id', { 
                      required: 'Department is required for this category'
                    })}
                    className={`w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 transition-all ${
                      errors.department_id ? 'border-red-500 focus:ring-red-500/20' : 'border-slate-300'
                    }`}
                  >
                    <option value="">Select Department</option>
                    {departments.map(dept => (
                      <option key={dept.id} value={dept.id}>{dept.name} ({dept.dept_code})</option>
                    ))}
                  </select>
                  {errors.department_id && (
                    <p className="text-xs font-medium text-red-500 flex items-center gap-1 mt-1">
                      <AlertTriangle size={12} /> {errors.department_id.message}
                    </p>
                  )}
                </div>
              ) : (
                <div className="bg-slate-50 p-4 border border-dashed border-slate-200 rounded-xl flex items-center justify-center text-center">
                  <span className="text-xs font-medium text-slate-400">Department hidden for Compulsory Subject</span>
                </div>
              )}
            </div>

            {/* Active Status Checkbox */}
            <div className="flex items-center gap-2.5">
              <input
                id="active"
                type="checkbox"
                checked={watch('active') === 1}
                onChange={e => setValue('active', e.target.checked ? 1 : 0)}
                className="w-4.5 h-4.5 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="active" className="text-sm font-medium text-slate-700 cursor-pointer">
                Mark Subject as Active
              </label>
            </div>

            {/* Form Action Buttons */}
            <div className="flex justify-end gap-3 pt-6 border-t border-slate-100">
              <button
                type="button"
                onClick={handleFormReset}
                className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-medium transition-all active:scale-95 flex items-center gap-1.5"
              >
                <RotateCcw size={15} /> Reset
              </button>
              {editingId !== null ? (
                <>
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="px-5 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded-xl text-sm font-medium transition-all active:scale-95"
                  >
                    Cancel Edit
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-all shadow-lg shadow-blue-150 active:scale-95 flex items-center gap-1.5"
                  >
                    <CheckCircle size={15} /> Save Changes
                  </button>
                </>
              ) : (
                <button
                  type="submit"
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-all shadow-lg shadow-blue-150 active:scale-95 flex items-center gap-1.5"
                >
                  <Plus size={15} /> Create Subject
                </button>
              )}
            </div>

          </form>
        </div>

        {/* Section 2: View Subjects Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden transition-all duration-300 hover:shadow-md">
          <div className="p-6 border-b border-slate-100 bg-slate-50/70">
            <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
              <BookMarked size={18} className="text-blue-600" /> View Subjects List
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Filter, search, view details, edit or delete courses</p>
          </div>

          <div className="p-6 space-y-6">
            
            {/* Filter Toolbar */}
            <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
              
              {/* Search Box */}
              <div className="relative flex-1">
                <Search size={16} className="absolute left-3.5 top-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by code, name, or university code..."
                  value={searchTerm}
                  onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                />
                {searchTerm && (
                  <button 
                    onClick={() => setSearchTerm('')} 
                    className="absolute right-3.5 top-3.5 text-slate-400 hover:text-slate-600"
                  >
                    <X size={15} />
                  </button>
                )}
              </div>

              {/* Semester Filter */}
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3.5 py-2 rounded-xl text-sm">
                  <Filter size={14} className="text-slate-500" />
                  <span className="text-slate-500 font-medium text-xs">Sem:</span>
                  <select
                    value={filterSemester}
                    onChange={e => { setFilterSemester(e.target.value); setCurrentPage(1); }}
                    className="bg-transparent focus:outline-none font-semibold text-slate-700"
                  >
                    <option value="">All Semesters</option>
                    {SEMESTERS.map(sem => (
                      <option key={sem} value={sem}>Semester {sem}</option>
                    ))}
                  </select>
                </div>

                {/* Department Filter */}
                <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3.5 py-2 rounded-xl text-sm">
                  <Filter size={14} className="text-slate-500" />
                  <span className="text-slate-500 font-medium text-xs">Dept:</span>
                  <select
                    value={filterDept}
                    onChange={e => { setFilterDept(e.target.value); setCurrentPage(1); }}
                    className="bg-transparent focus:outline-none font-semibold text-slate-700 max-w-[200px]"
                  >
                    <option value="">All Departments</option>
                    {departments.map(dept => (
                      <option key={dept.id} value={dept.id}>{dept.dept_code} - {dept.name}</option>
                    ))}
                  </select>
                </div>
              </div>

            </div>

            {/* Subjects List Data Table */}
            <div className="overflow-x-auto border border-slate-100 rounded-xl">
              {loadingSubjects ? (
                <div className="p-8 text-center text-slate-400 font-medium">Loading subjects data...</div>
              ) : (
                <table className="w-full text-left text-sm text-slate-600">
                  <thead className="bg-slate-50 border-b border-slate-150">
                    <tr>
                      <th className="px-5 py-3.5 font-semibold text-slate-700">Subject Code</th>
                      <th className="px-5 py-3.5 font-semibold text-slate-700">University Code</th>
                      <th className="px-5 py-3.5 font-semibold text-slate-700">Subject Name</th>
                      <th className="px-5 py-3.5 font-semibold text-slate-700">Category</th>
                      <th className="px-5 py-3.5 font-semibold text-slate-700">Type</th>
                      <th className="px-5 py-3.5 font-semibold text-slate-700 text-center">Semester</th>
                      <th className="px-5 py-3.5 font-semibold text-slate-700">Department</th>
                      <th className="px-5 py-3.5 font-semibold text-slate-700">Academic Session</th>
                      <th className="px-5 py-3.5 font-semibold text-slate-700 text-center">Status</th>
                      <th className="px-5 py-3.5 font-semibold text-slate-700 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {subjectsList.map(sub => {
                      const categoryCode = sub.priority || 'PCC';
                      let catName = 'Compulsory Subject';
                      if (categoryCode === 'PEC') catName = 'Department Subject';
                      if (categoryCode === 'OEC') catName = 'Open Elective Subject';

                      const sessionObj = dbSessions.find(s => s.id === sub.academic_session);
                      const sessionName = sessionObj ? sessionObj.name : `Session ID: ${sub.academic_session}`;

                      const deptObj = departments.find(d => d.id === sub.department);
                      const deptName = deptObj ? deptObj.name : 'Universal / All';

                      return (
                        <tr key={sub.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-5 py-4 font-bold text-slate-900">{sub.clg_sub_code}</td>
                          <td className="px-5 py-4 font-mono text-xs text-blue-600 font-bold">{sub.university_sub_code}</td>
                          <td className="px-5 py-4 font-medium text-slate-800">{sub.subject_name}</td>
                          <td className="px-5 py-4">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xxs font-semibold ${
                              categoryCode === 'PCC' 
                                ? 'bg-purple-50 text-purple-700 border border-purple-100'
                                : categoryCode === 'PEC'
                                ? 'bg-blue-50 text-blue-700 border border-blue-100'
                                : 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                            }`}>
                              {catName}
                            </span>
                          </td>
                          <td className="px-5 py-4 text-xs font-semibold text-slate-600">{sub.type}</td>
                          <td className="px-5 py-4 text-center text-slate-700">Sem {sub.semester}</td>
                          <td className="px-5 py-4 text-xs text-slate-500 font-medium">
                            {deptName}
                          </td>
                          <td className="px-5 py-4 text-xs text-slate-600 font-semibold">{sessionName}</td>
                          <td className="px-5 py-4 text-center">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xxs font-bold ${
                              sub.active === 1 
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                                : 'bg-slate-150 text-slate-600 border border-slate-200'
                            }`}>
                              {sub.active === 1 ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="px-5 py-4 text-right">
                            <div className="flex justify-end gap-1.5">
                              <button
                                onClick={() => handleEdit(sub)}
                                title="Edit Subject"
                                className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors duration-200"
                              >
                                <Edit2 size={15} />
                              </button>
                              <button
                                onClick={() => handleDelete(sub.id)}
                                title="Delete Subject"
                                className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200"
                              >
                                <Trash2 size={15} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {subjectsList.length === 0 && (
                      <tr>
                        <td colSpan={10} className="px-5 py-8 text-center text-slate-400 font-medium">
                          No subjects match your criteria. Reset filters or search.
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
                <span className="text-xs font-semibold text-slate-500">
                  Showing {Math.min(totalSubjects, (currentPage - 1) * itemsPerPage + 1)} to {Math.min(totalSubjects, currentPage * itemsPerPage)} of {totalSubjects} subjects
                </span>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 transition-colors"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  {[...Array(totalPages)].map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => setCurrentPage(idx + 1)}
                      className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                        currentPage === idx + 1 
                          ? 'bg-blue-600 text-white' 
                          : 'border border-slate-200 text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {idx + 1}
                    </button>
                  ))}
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 transition-colors"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}

          </div>
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
