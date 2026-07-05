import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../lib/AuthContext';
import PermissionGuard from '../components/PermissionGuard';
import {
  Plus, Search, Edit2, Trash2, Loader2, ChevronLeft, ChevronRight,
  X, Check, AlertCircle, UserPlus, Users, Eye, ArrowRight, ArrowLeft
} from 'lucide-react';

// ─── Types ───────────────────────────────────────────────────────
interface StaffItem {
  id: number;
  computer_code: number;
  title: string | null;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  date_of_birth: string | null;
  gender: string | null;
  mobile1: string;
  mobile2: string | null;
  email: string | null;
  abc_id: string;
  aadhar_number: number;
  permanent_address: string;
  city: number;
  active: boolean;
  date_join: string;
  date_leave: string | null;
  created_at: string;
  updated_at: string;
}

interface StaffFormData {
  computer_code: string;
  title: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  mobile1: string;
  mobile2: string;
  email: string;
  abc_id: string;
  aadhar_number: string;
  permanent_address: string;
  city: string;
  date_join: string;
  date_leave: string;
  role_id: string;
  department_id: string;
  designation_id: string;
  bank_name: string;
  account_number: string;
  ifsc: string;
  qualification: string;
  experience_years: string;
  academic_session_id: string;
  academic_term_id: string;
  start_date: string;
  end_date: string;
}

const emptyForm: StaffFormData = {
  computer_code: '', title: '', first_name: '', middle_name: '', last_name: '',
  date_of_birth: '', gender: '', mobile1: '', mobile2: '', email: '',
  abc_id: '', aadhar_number: '', permanent_address: '', city: '',
  date_join: '', date_leave: '', role_id: '', department_id: '',
  designation_id: '', bank_name: '', account_number: '', ifsc: '',
  qualification: '', experience_years: '', academic_session_id: '',
  academic_term_id: '', start_date: '', end_date: ''
};

// ─── Toast Notification ──────────────────────────────────────────
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

// ─── Modal Wrapper ─────────────────────────────────────────
const Modal = ({ title, onClose, children, wide = false }: {
  title: string; onClose: () => void; children: React.ReactNode; wide?: boolean;
}) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
    <div className={`relative bg-white rounded-2xl shadow-2xl ${wide ? 'max-w-4xl' : 'max-w-md'} w-full max-h-[90vh] overflow-hidden flex flex-col`}>
      <div className="bg-white px-6 py-4 border-b border-slate-200 flex items-center justify-between rounded-t-2xl z-10 shrink-0">
        <h3 className="text-lg font-bold text-slate-800">{title}</h3>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
          <X size={20} />
        </button>
      </div>
      <div className="p-6 overflow-y-auto flex-1">{children}</div>
    </div>
  </div>
);

// ─── Form Field Component ─────────────────────────────────────
const FormField = ({ label, name, type = 'text', required = false, disabled = false, placeholder = '', value, onChange, error }: {
  label: string; name: string; type?: string; required?: boolean; disabled?: boolean; placeholder?: string;
  value: string; onChange: (val: string) => void; error?: string;
}) => (
  <div>
    <label className="block text-xs font-semibold text-slate-600 mb-1.5">
      {label} {required && <span className="text-red-500">*</span>}
    </label>
    {name === 'gender' ? (
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${
          error ? 'border-red-400' : 'border-slate-300'
        } ${disabled ? 'bg-slate-100 cursor-not-allowed' : ''}`}
      >
        <option value="">Select</option>
        <option value="M">Male</option>
        <option value="F">Female</option>
        <option value="O">Other</option>
      </select>
    ) : (
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className={`w-full px-3 py-2.5 border rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${
          error ? 'border-red-400' : 'border-slate-300'
        } ${disabled ? 'bg-slate-100 cursor-not-allowed' : ''}`}
      />
    )}
    {error && (
      <p className="text-xs text-red-500 mt-1">{error}</p>
    )}
  </div>
);

// ─── Staff Form ───────────────────────────────────────────
const StaffForm = ({ 
  isCreate, onSubmit, onCancel, form, setForm, formErrors, submitting, roles, departments, designations, sessions, terms
}: { 
  isCreate: boolean; onSubmit: () => void; onCancel: () => void; form: StaffFormData; setForm: (f: StaffFormData) => void; formErrors: Record<string, string>; submitting: boolean;
  roles: {id: number; role_type: string}[];
  departments: {id: number; name: string}[];
  designations: {id: number; designation: string}[];
  sessions: {id: number; session_name: string}[];
  terms: {id: number; term_name: string}[];
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const handleChange = (name: keyof StaffFormData) => (val: string) => setForm({ ...form, [name]: val });

  const tabs = ["Personal Info", "Employment", "Bank & Qualifications", "Preview"];

  const renderTabContent = () => {
    switch(activeTab) {
      case 0:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Title" name="title" value={form.title} onChange={handleChange('title')} error={formErrors.title} placeholder="Mr. / Mrs. / Dr." />
            <FormField label="First Name" name="first_name" value={form.first_name} onChange={handleChange('first_name')} error={formErrors.first_name} required placeholder="First name" />
            <FormField label="Middle Name" name="middle_name" value={form.middle_name} onChange={handleChange('middle_name')} error={formErrors.middle_name} placeholder="Middle name" />
            <FormField label="Last Name" name="last_name" value={form.last_name} onChange={handleChange('last_name')} error={formErrors.last_name} required placeholder="Last name" />
            <FormField label="Gender" name="gender" value={form.gender} onChange={handleChange('gender')} error={formErrors.gender} />
            <FormField label="Date of Birth" name="date_of_birth" value={form.date_of_birth} onChange={handleChange('date_of_birth')} error={formErrors.date_of_birth} type="date" />
            <FormField label="Mobile 1" name="mobile1" value={form.mobile1} onChange={handleChange('mobile1')} error={formErrors.mobile1} required placeholder="10-15 digits" />
            <FormField label="Mobile 2" name="mobile2" value={form.mobile2} onChange={handleChange('mobile2')} error={formErrors.mobile2} placeholder="Optional" />
            <FormField label="Email" name="email" value={form.email} onChange={handleChange('email')} error={formErrors.email} type="email" placeholder="email@example.com" />
            <FormField label="ABC ID" name="abc_id" value={form.abc_id} onChange={handleChange('abc_id')} error={formErrors.abc_id} required={isCreate} disabled={!isCreate} placeholder="ABC ID" />
            <FormField label="Aadhar Number" name="aadhar_number" value={form.aadhar_number} onChange={handleChange('aadhar_number')} error={formErrors.aadhar_number} required={isCreate} disabled={!isCreate} placeholder="12 digits" />
            <FormField label="City Code" name="city" value={form.city} onChange={handleChange('city')} error={formErrors.city} required={isCreate} disabled={!isCreate} placeholder="City ID" />
            <div className="md:col-span-2">
              <FormField label="Permanent Address" name="permanent_address" value={form.permanent_address} onChange={handleChange('permanent_address')} error={formErrors.permanent_address} required={isCreate} placeholder="Full address" />
            </div>
          </div>
        );
      case 1:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Computer Code" name="computer_code" value={form.computer_code} onChange={handleChange('computer_code')} error={formErrors.computer_code} required={isCreate} disabled={!isCreate} placeholder="e.g. 50001" type="number" />
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Department {isCreate && <span className="text-red-500">*</span>}</label>
              <select
                value={form.department_id}
                onChange={(e) => handleChange('department_id')(e.target.value)}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${formErrors.department_id ? 'border-red-400' : 'border-slate-300'}`}
              >
                <option value="">Select Department</option>
                {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
              {formErrors.department_id && <p className="text-xs text-red-500 mt-1">{formErrors.department_id}</p>}
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Designation</label>
              <select
                value={form.designation_id}
                onChange={(e) => handleChange('designation_id')(e.target.value)}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${formErrors.designation_id ? 'border-red-400' : 'border-slate-300'}`}
              >
                <option value="">Select Designation</option>
                {designations.map(d => <option key={d.id} value={d.id}>{d.designation}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Role {isCreate && <span className="text-red-500">*</span>}</label>
              <select
                value={form.role_id}
                onChange={(e) => handleChange('role_id')(e.target.value)}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${formErrors.role_id ? 'border-red-400' : 'border-slate-300'}`}
              >
                <option value="">Select Role</option>
                {roles.map(r => <option key={r.id} value={r.id}>{r.role_type}</option>)}
              </select>
              {formErrors.role_id && <p className="text-xs text-red-500 mt-1">{formErrors.role_id}</p>}
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Academic Session</label>
              <select
                value={form.academic_session_id}
                onChange={(e) => handleChange('academic_session_id')(e.target.value)}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 border-slate-300`}
              >
                <option value="">Select Session</option>
                {sessions.map(s => <option key={s.id} value={s.id}>{s.session_name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Academic Term</label>
              <select
                value={form.academic_term_id}
                onChange={(e) => handleChange('academic_term_id')(e.target.value)}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 border-slate-300`}
              >
                <option value="">Select Term</option>
                {terms.map(t => <option key={t.id} value={t.id}>{t.term_name}</option>)}
              </select>
            </div>
            <FormField label="Role Start Date" name="start_date" value={form.start_date} onChange={handleChange('start_date')} error={formErrors.start_date} type="date" />
            <FormField label="Role End Date" name="end_date" value={form.end_date} onChange={handleChange('end_date')} error={formErrors.end_date} type="date" />
            <FormField label="Date of Joining" name="date_join" value={form.date_join} onChange={handleChange('date_join')} error={formErrors.date_join} type="date" required={isCreate} disabled={!isCreate} />
            <FormField label="Date of Leaving" name="date_leave" value={form.date_leave} onChange={handleChange('date_leave')} error={formErrors.date_leave} type="date" />
          </div>
        );
      case 2:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <h4 className="md:col-span-2 text-sm font-bold text-slate-800 border-b pb-2 mt-2">Bank Details</h4>
            <FormField label="Bank Name" name="bank_name" value={form.bank_name} onChange={handleChange('bank_name')} error={formErrors.bank_name} placeholder="e.g. State Bank of India" />
            <FormField label="Account Number" name="account_number" value={form.account_number} onChange={handleChange('account_number')} error={formErrors.account_number} placeholder="Account No" />
            <FormField label="IFSC Code" name="ifsc" value={form.ifsc} onChange={handleChange('ifsc')} error={formErrors.ifsc} placeholder="IFSC Code" />
            
            <h4 className="md:col-span-2 text-sm font-bold text-slate-800 border-b pb-2 mt-4">Qualifications & Experience</h4>
            <FormField label="Highest Qualification" name="qualification" value={form.qualification} onChange={handleChange('qualification')} error={formErrors.qualification} placeholder="e.g. Ph.D. in Computer Science" />
            <FormField label="Experience (Years)" name="experience_years" value={form.experience_years} onChange={handleChange('experience_years')} error={formErrors.experience_years} type="number" placeholder="e.g. 5.5" />
          </div>
        );
      case 3:
        const generatedPassword = form.date_of_birth ? form.date_of_birth.split('-').reverse().join('') : '12345';
        return (
          <div className="flex flex-col items-center justify-center p-8 bg-slate-50 rounded-xl border border-slate-200">
            <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4">
              <UserPlus size={32} />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">Ready to Submit</h3>
            <p className="text-sm text-slate-500 mb-6 text-center max-w-md">
              Please review the details. Once created, the staff member will be able to log in using the credentials below.
            </p>
            <div className="w-full max-w-sm bg-white rounded-lg border border-slate-200 p-4 space-y-3 shadow-sm">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">Username / Code:</span>
                <span className="font-mono text-sm font-bold text-slate-800 bg-slate-100 px-2 py-1 rounded">{form.computer_code || 'TBD'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">Initial Password:</span>
                <span className="font-mono text-sm font-bold text-slate-800 bg-slate-100 px-2 py-1 rounded">{generatedPassword}</span>
              </div>
            </div>
          </div>
        );
      default: return null;
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tabs Header */}
      <div className="flex overflow-x-auto border-b border-slate-200 mb-6 shrink-0 no-scrollbar">
        {tabs.map((tab, idx) => (
          <button
            key={idx}
            onClick={() => setActiveTab(idx)}
            className={`whitespace-nowrap px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === idx ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <span className="inline-block w-5 h-5 rounded-full text-xs leading-5 text-center mr-2 bg-slate-100 text-slate-500 font-bold">
              {idx + 1}
            </span>
            {tab}
          </button>
        ))}
      </div>

      {/* Form Content */}
      <div className="flex-1">
        {renderTabContent()}
      </div>

      {/* Footer Controls */}
      <div className="flex justify-between items-center mt-6 pt-4 border-t border-slate-200 shrink-0">
        <button
          onClick={onCancel}
          className="px-4 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
        >
          Cancel
        </button>
        <div className="flex items-center gap-3">
          {activeTab > 0 && (
            <button
              onClick={() => setActiveTab(prev => prev - 1)}
              className="px-4 py-2.5 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors flex items-center gap-2"
            >
              <ArrowLeft size={16} /> Back
            </button>
          )}
          {activeTab < tabs.length - 1 ? (
            <button
              onClick={() => setActiveTab(prev => prev + 1)}
              className="px-4 py-2.5 text-sm font-medium text-white bg-slate-800 hover:bg-slate-900 rounded-lg transition-colors flex items-center gap-2"
            >
              Next <ArrowRight size={16} />
            </button>
          ) : (
            <button
              onClick={onSubmit}
              disabled={submitting}
              className="px-6 py-2.5 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm disabled:opacity-60 flex items-center gap-2"
            >
              {submitting ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
              {isCreate ? 'Create Staff' : 'Save Changes'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── Main Component ──────────────────────────────────────────────
const StaffManagement = () => {
  const { hasPermission } = useAuth();

  // Data state
  const [staff, setStaff] = useState<StaffItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Master data
  const [roles, setRoles] = useState<{id: number; role_type: string}[]>([]);
  const [departments, setDepartments] = useState<{id: number; name: string}[]>([]);
  const [designations, setDesignations] = useState<{id: number; designation: string}[]>([]);
  const [sessions, setSessions] = useState<{id: number; session_name: string}[]>([]);
  const [terms, setTerms] = useState<{id: number; term_name: string}[]>([]);

  // Fetch master data
  useEffect(() => {
    const fetchMasterData = async () => {
      try {
        const [rolesRes, deptsRes, desigRes, sessionsRes, termsRes] = await Promise.all([
          api.get('/rbac/roles'),
          api.get('/academic/departments'),
          api.get('/staff/designations'),
          api.get('/academic/academic-sessions'),
          api.get('/academic/academic-terms')
        ]);
        setRoles(rolesRes.data?.data || []);
        setDepartments(deptsRes.data?.data || []);
        setDesignations(desigRes.data?.data || []);
        setSessions(sessionsRes.data?.data || []);
        setTerms(termsRes.data?.data || []);
      } catch (e) {
        console.error("Failed to load master data", e);
      }
    };
    fetchMasterData();
  }, []);

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Search & Filters
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState<string>('');

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedStaff, setSelectedStaff] = useState<StaffItem | null>(null);

  // Form
  const [form, setForm] = useState<StaffFormData>(emptyForm);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [search]);

  // Fetch staff list
  const fetchStaff = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('skip', String((page - 1) * pageSize));
      params.append('limit', String(pageSize));
      params.append('sort_by', 'id');
      params.append('sort_order', 'desc');
      if (debouncedSearch) params.append('search', debouncedSearch);
      if (activeFilter) params.append('active', activeFilter);

      const res = await api.get(`/staff/?${params.toString()}`);
      const data = res.data?.data;
      setStaff(data?.items || []);
      setTotal(data?.total || 0);
    } catch (error) {
      console.error('Failed to fetch staff', error);
      setToast({ message: 'Failed to load staff data', type: 'error' });
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, debouncedSearch, activeFilter]);

  useEffect(() => {
    fetchStaff();
  }, [fetchStaff]);

  const totalPages = Math.ceil(total / pageSize);

  // ─── Form Validation ────────────────────────────────────────
  const validateForm = (isCreate: boolean): boolean => {
    const errors: Record<string, string> = {};

    if (isCreate && !form.role_id) errors.role_id = 'Required';
    if (isCreate && !form.department_id) errors.department_id = 'Required';

    if (isCreate && !form.computer_code.trim()) errors.computer_code = 'Required';
    if (!form.first_name.trim()) errors.first_name = 'Required';
    if (!form.last_name.trim()) errors.last_name = 'Required';
    if (!form.mobile1.trim()) errors.mobile1 = 'Required';
    if (isCreate && !form.abc_id.trim()) errors.abc_id = 'Required';
    if (isCreate && !form.permanent_address.trim()) errors.permanent_address = 'Required';
    if (isCreate && !form.city.trim()) errors.city = 'Required';
    if (isCreate && !form.date_join) errors.date_join = 'Required';

    if (isCreate && !form.aadhar_number.trim()) {
      errors.aadhar_number = 'Required';
    } else if (form.aadhar_number && form.aadhar_number.length !== 12) {
      errors.aadhar_number = 'Must be 12 digits';
    }

    if (form.mobile1 && !/^\+?[0-9]{10,15}$/.test(form.mobile1)) {
      errors.mobile1 = 'Invalid phone number';
    }

    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      errors.email = 'Invalid email format';
    }

    if (form.gender && !['M', 'F', 'O'].includes(form.gender)) {
      errors.gender = 'Must be M, F, or O';
    }

    setFormErrors(errors);
    if(Object.keys(errors).length > 0) {
      setToast({ message: 'Please correct the errors in the form before submitting.', type: 'error' });
    }
    return Object.keys(errors).length === 0;
  };

  // ─── Create Staff ───────────────────────────────────────────
  const handleCreate = async () => {
    if (!validateForm(true)) return;
    setSubmitting(true);
    try {
      const staffData: Record<string, string | number | null> = {
        computer_code: parseInt(form.computer_code),
        first_name: form.first_name,
        last_name: form.last_name,
        mobile1: form.mobile1,
        abc_id: form.abc_id,
        aadhar_number: parseInt(form.aadhar_number),
        permanent_address: form.permanent_address,
        city: parseInt(form.city),
        date_join: form.date_join,
        role_id: parseInt(form.role_id),
        department_id: parseInt(form.department_id),
      };
      if (form.academic_session_id) staffData.academic_session_id = parseInt(form.academic_session_id);
      if (form.academic_term_id) staffData.academic_term_id = parseInt(form.academic_term_id);
      if (form.start_date) staffData.start_date = form.start_date;
      if (form.end_date) staffData.end_date = form.end_date;
      if (form.title) staffData.title = form.title;
      if (form.middle_name) staffData.middle_name = form.middle_name;
      if (form.date_of_birth) staffData.date_of_birth = form.date_of_birth;
      if (form.gender) staffData.gender = form.gender;
      if (form.mobile2) staffData.mobile2 = form.mobile2;
      if (form.email) staffData.email = form.email;
      if (form.date_leave) staffData.date_leave = form.date_leave;

      const detailsData: Record<string, string | number | null> = {};
      if (form.designation_id) detailsData.designation_id = parseInt(form.designation_id);
      if (form.department_id) detailsData.dept_id = parseInt(form.department_id); // Sync with staff role
      if (form.bank_name) detailsData.bank_name = form.bank_name;
      if (form.account_number) detailsData.account_number = form.account_number;
      if (form.ifsc) detailsData.ifsc = form.ifsc;
      if (form.qualification) detailsData.qualification = form.qualification;
      if (form.experience_years) detailsData.experience_years = parseFloat(form.experience_years);

      await api.post('/staff/', { staff: staffData, details: detailsData, roles: [] });

      setToast({ message: 'Staff member created successfully', type: 'success' });
      setShowCreateModal(false);
      setForm(emptyForm);
      setFormErrors({});
      fetchStaff();
    } catch (error) {
      const err = error as { response?: { data?: { message?: string } } };
      const detail = err.response?.data?.message || 'Failed to create staff member';
      setToast({ message: detail, type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Update Staff ───────────────────────────────────────────
  const handleUpdate = async () => {
    if (!validateForm(false)) return;
    if (!selectedStaff) return;
    setSubmitting(true);
    try {
      const updateData: Record<string, any> = {};
      if (form.title !== (selectedStaff.title || '')) updateData.title = form.title || null;
      if (form.first_name !== selectedStaff.first_name) updateData.first_name = form.first_name;
      if (form.middle_name !== (selectedStaff.middle_name || '')) updateData.middle_name = form.middle_name || null;
      if (form.last_name !== selectedStaff.last_name) updateData.last_name = form.last_name;
      if (form.date_of_birth !== (selectedStaff.date_of_birth || '')) updateData.date_of_birth = form.date_of_birth || null;
      if (form.gender !== (selectedStaff.gender || '')) updateData.gender = form.gender || null;
      if (form.mobile1 !== selectedStaff.mobile1) updateData.mobile1 = form.mobile1;
      if (form.mobile2 !== (selectedStaff.mobile2 || '')) updateData.mobile2 = form.mobile2 || null;
      if (form.email !== (selectedStaff.email || '')) updateData.email = form.email || null;
      if (form.permanent_address !== selectedStaff.permanent_address) updateData.permanent_address = form.permanent_address;
      if (form.date_join !== selectedStaff.date_join) updateData.date_join = form.date_join;
      if (form.date_leave !== (selectedStaff.date_leave || '')) updateData.date_leave = form.date_leave || null;
      if (form.role_id) updateData.role_id = parseInt(form.role_id);
      if (form.department_id) updateData.department_id = parseInt(form.department_id);
      if (form.academic_session_id) updateData.academic_session_id = parseInt(form.academic_session_id);
      if (form.academic_term_id) updateData.academic_term_id = parseInt(form.academic_term_id);
      if (form.start_date) updateData.start_date = form.start_date;
      if (form.end_date) updateData.end_date = form.end_date;

      const detailsData: Record<string, string | number | null> = {};
      if (form.designation_id) detailsData.designation_id = parseInt(form.designation_id);
      if (form.department_id) detailsData.dept_id = parseInt(form.department_id);
      if (form.bank_name) detailsData.bank_name = form.bank_name;
      if (form.account_number) detailsData.account_number = form.account_number;
      if (form.ifsc) detailsData.ifsc = form.ifsc;
      if (form.qualification) detailsData.qualification = form.qualification;
      if (form.experience_years) detailsData.experience_years = parseFloat(form.experience_years);
      
      updateData.details = detailsData;

      await api.put(`/staff/${selectedStaff.id}`, updateData);

      setToast({ message: 'Staff member updated successfully', type: 'success' });
      setShowEditModal(false);
      setSelectedStaff(null);
      setForm(emptyForm);
      setFormErrors({});
      fetchStaff();
    } catch (error) {
      const err = error as { response?: { data?: { message?: string } } };
      const detail = err.response?.data?.message || 'Failed to update staff member';
      setToast({ message: detail, type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Delete Staff ───────────────────────────────────────────
  const handleDelete = async () => {
    if (!selectedStaff) return;
    setSubmitting(true);
    try {
      await api.delete(`/staff/${selectedStaff.id}`);
      setToast({ message: 'Staff member deactivated successfully', type: 'success' });
      setShowDeleteModal(false);
      setSelectedStaff(null);
      fetchStaff();
    } catch (error) {
      const err = error as { response?: { data?: { message?: string } } };
      const detail = err.response?.data?.message || 'Failed to deactivate staff member';
      setToast({ message: detail, type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Open View Modal ───────────────────────────────────────
  const openView = (s: StaffItem) => {
    setSelectedStaff(s);
    setShowViewModal(true);
  };

  // ─── Open Edit Modal ───────────────────────────────────────
  const openEdit = async (s: StaffItem) => {
    setSelectedStaff(s);
    setForm({
      computer_code: String(s.computer_code),
      title: s.title || '',
      first_name: s.first_name,
      middle_name: s.middle_name || '',
      last_name: s.last_name,
      date_of_birth: s.date_of_birth || '',
      gender: s.gender || '',
      mobile1: s.mobile1,
      mobile2: s.mobile2 || '',
      email: s.email || '',
      abc_id: s.abc_id,
      aadhar_number: String(s.aadhar_number),
      permanent_address: s.permanent_address,
      city: String(s.city),
      date_join: s.date_join,
      date_leave: s.date_leave || '',
      role_id: '',
      department_id: '',
      designation_id: '',
      bank_name: '',
      account_number: '',
      ifsc: '',
      qualification: '',
      experience_years: '',
      academic_session_id: '',
      academic_term_id: '',
      start_date: '',
      end_date: ''
    });
    setFormErrors({});
    setShowEditModal(true);
    
    try {
      const res = await api.get(`/staff/${s.id}`);
      const profile = res.data?.data;
      if (profile) {
        setForm(prev => ({
          ...prev,
          role_id: profile.roles?.length ? String(profile.roles[0].role_id) : '',
          department_id: profile.roles?.length ? String(profile.roles[0].department_id) : '',
          academic_session_id: (profile.roles?.length && profile.roles[0].academic_session_id) ? String(profile.roles[0].academic_session_id) : '',
          academic_term_id: (profile.roles?.length && profile.roles[0].academic_term_id) ? String(profile.roles[0].academic_term_id) : '',
          start_date: (profile.roles?.length && profile.roles[0].start_date) ? profile.roles[0].start_date : '',
          end_date: (profile.roles?.length && profile.roles[0].end_date) ? profile.roles[0].end_date : '',
          designation_id: profile.details?.designation_id ? String(profile.details.designation_id) : '',
          bank_name: profile.details?.bank_name || '',
          account_number: profile.details?.account_number || '',
          ifsc: profile.details?.ifsc || '',
          qualification: profile.details?.qualification || '',
          experience_years: profile.details?.experience_years ? String(profile.details.experience_years) : ''
        }));
      }
    } catch (e) {
      console.error("Failed to fetch staff profile for editing", e);
    }
  };

  // ─── Open Delete Modal ─────────────────────────────────────
  const openDelete = (s: StaffItem) => {
    setSelectedStaff(s);
    setShowDeleteModal(true);
  };


  // ─── Render ─────────────────────────────────────────────────
  return (
    <div className="space-y-6 pb-12">
      {/* Toast */}
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center">
            <Users size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Staff Management</h1>
            <p className="text-sm text-slate-500">{total} staff member{total !== 1 ? 's' : ''} total</p>
          </div>
        </div>
        <PermissionGuard permission="staff.create">
          <button
            onClick={() => { setForm(emptyForm); setFormErrors({}); setShowCreateModal(true); }}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl transition-all shadow-sm hover:shadow-md"
          >
            <UserPlus size={18} />
            Add Staff
          </button>
        </PermissionGuard>
      </div>

      {/* Filters Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name, code, email, or mobile..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-colors"
            />
          </div>
          <select
            value={activeFilter}
            onChange={(e) => { setActiveFilter(e.target.value); setPage(1); }}
            className="px-3 py-2.5 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500"
          >
            <option value="">All Status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
            className="px-3 py-2.5 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500"
          >
            <option value={10}>10 / page</option>
            <option value={25}>25 / page</option>
            <option value={50}>50 / page</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center text-slate-400 gap-3">
            <Loader2 className="animate-spin" size={32} />
            <p className="text-sm">Loading staff data...</p>
          </div>
        ) : staff.length === 0 ? (
          <div className="p-16 flex flex-col items-center justify-center text-slate-400 gap-3">
            <Users size={40} className="opacity-40" />
            <p className="text-sm font-medium">No staff members found</p>
            {debouncedSearch && <p className="text-xs">Try adjusting your search query</p>}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="px-6 py-3.5 font-semibold text-slate-600 text-xs uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3.5 font-semibold text-slate-600 text-xs uppercase tracking-wider">Code</th>
                  <th className="px-6 py-3.5 font-semibold text-slate-600 text-xs uppercase tracking-wider hidden md:table-cell">Email</th>
                  <th className="px-6 py-3.5 font-semibold text-slate-600 text-xs uppercase tracking-wider hidden lg:table-cell">Mobile</th>
                  <th className="px-6 py-3.5 font-semibold text-slate-600 text-xs uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3.5 font-semibold text-slate-600 text-xs uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {staff.map((s) => (
                  <tr key={s.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-lg flex items-center justify-center text-xs font-bold shadow-sm">
                          {s.first_name[0]}{s.last_name[0]}
                        </div>
                        <div>
                          <p className="font-semibold text-slate-800">{s.title ? `${s.title} ` : ''}{s.first_name} {s.last_name}</p>
                          <p className="text-xs text-slate-500">{s.gender === 'M' ? 'Male' : s.gender === 'F' ? 'Female' : s.gender === 'O' ? 'Other' : '—'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-mono text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded-md">{s.computer_code}</span>
                    </td>
                    <td className="px-6 py-4 text-slate-600 hidden md:table-cell">{s.email || '—'}</td>
                    <td className="px-6 py-4 text-slate-600 hidden lg:table-cell">{s.mobile1}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${
                        s.active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${s.active ? 'bg-emerald-500' : 'bg-red-500'}`} />
                        {s.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => openView(s)}
                          className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="View"
                        >
                          <Eye size={16} />
                        </button>
                        <PermissionGuard permission="staff.update">
                          <button
                            onClick={() => openEdit(s)}
                            className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Edit"
                          >
                            <Edit2 size={16} />
                          </button>
                        </PermissionGuard>
                        {s.active && (
                          <PermissionGuard permission="staff.delete">
                            <button
                              onClick={() => openDelete(s)}
                              className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              title="Deactivate"
                            >
                              <Trash2 size={16} />
                            </button>
                          </PermissionGuard>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!loading && total > 0 && (
          <div className="px-6 py-4 border-t border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-xs text-slate-500">
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} results
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={18} />
              </button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum: number;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`w-9 h-9 text-sm font-medium rounded-lg transition-colors ${
                      page === pageNum
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <Modal title="Add New Staff Member" onClose={() => { setShowCreateModal(false); setFormErrors({}); }} wide>
          <StaffForm isCreate onSubmit={handleCreate} onCancel={() => { setShowCreateModal(false); setFormErrors({}); }} form={form} setForm={setForm} formErrors={formErrors} submitting={submitting} roles={roles} departments={departments} designations={designations} sessions={sessions} terms={terms} />
        </Modal>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedStaff && (
        <Modal title={`Edit: ${selectedStaff.first_name} ${selectedStaff.last_name}`} onClose={() => { setShowEditModal(false); setFormErrors({}); }} wide>
          <StaffForm isCreate={false} onSubmit={handleUpdate} onCancel={() => { setShowEditModal(false); setFormErrors({}); }} form={form} setForm={setForm} formErrors={formErrors} submitting={submitting} roles={roles} departments={departments} designations={designations} sessions={sessions} terms={terms} />
        </Modal>
      )}

      {/* View Modal */}
      {showViewModal && selectedStaff && (
        <Modal title="Staff Details" onClose={() => setShowViewModal(false)} wide>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-y-4 gap-x-6 text-sm">
            <div><span className="text-slate-500 block text-xs">Computer Code</span><span className="font-medium text-slate-800">{selectedStaff.computer_code}</span></div>
            <div><span className="text-slate-500 block text-xs">Full Name</span><span className="font-medium text-slate-800">{selectedStaff.title ? `${selectedStaff.title} ` : ''}{selectedStaff.first_name} {selectedStaff.middle_name ? `${selectedStaff.middle_name} ` : ''}{selectedStaff.last_name}</span></div>
            <div><span className="text-slate-500 block text-xs">Gender</span><span className="font-medium text-slate-800">{selectedStaff.gender === 'M' ? 'Male' : selectedStaff.gender === 'F' ? 'Female' : selectedStaff.gender === 'O' ? 'Other' : '—'}</span></div>
            <div><span className="text-slate-500 block text-xs">Date of Birth</span><span className="font-medium text-slate-800">{selectedStaff.date_of_birth || '—'}</span></div>
            <div><span className="text-slate-500 block text-xs">Mobile 1</span><span className="font-medium text-slate-800">{selectedStaff.mobile1}</span></div>
            <div><span className="text-slate-500 block text-xs">Mobile 2</span><span className="font-medium text-slate-800">{selectedStaff.mobile2 || '—'}</span></div>
            <div><span className="text-slate-500 block text-xs">Email</span><span className="font-medium text-slate-800">{selectedStaff.email || '—'}</span></div>
            <div><span className="text-slate-500 block text-xs">ABC ID</span><span className="font-medium text-slate-800">{selectedStaff.abc_id}</span></div>
            <div><span className="text-slate-500 block text-xs">Aadhar Number</span><span className="font-medium text-slate-800">{selectedStaff.aadhar_number}</span></div>
            <div><span className="text-slate-500 block text-xs">City Code</span><span className="font-medium text-slate-800">{selectedStaff.city}</span></div>
            <div className="md:col-span-2"><span className="text-slate-500 block text-xs">Permanent Address</span><span className="font-medium text-slate-800">{selectedStaff.permanent_address}</span></div>
            <div><span className="text-slate-500 block text-xs">Date Joined</span><span className="font-medium text-slate-800">{selectedStaff.date_join}</span></div>
            <div><span className="text-slate-500 block text-xs">Date Left</span><span className="font-medium text-slate-800">{selectedStaff.date_leave || '—'}</span></div>
          </div>
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-200">
            <button
              onClick={() => setShowViewModal(false)}
              className="px-4 py-2.5 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </Modal>
      )}

      {/* Delete Confirmation */}
      {showDeleteModal && selectedStaff && (
        <Modal title="Confirm Deactivation" onClose={() => setShowDeleteModal(false)}>
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle size={32} />
            </div>
            <p className="text-slate-800 font-medium mb-2">
              Deactivate <strong>{selectedStaff.first_name} {selectedStaff.last_name}</strong>?
            </p>
            <p className="text-sm text-slate-500 mb-6">
              This will deactivate the staff member and their login credentials. This action can be reversed by an admin.
            </p>
            <div className="flex justify-center gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2.5 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={submitting}
                className="px-5 py-2.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-60 flex items-center gap-2"
              >
                {submitting ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                Deactivate
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default StaffManagement;
