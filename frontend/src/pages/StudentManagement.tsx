import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../lib/AuthContext';
import PermissionGuard from '../components/PermissionGuard';
import {
  Plus, Search, Edit2, Trash2, Loader2, ChevronLeft, ChevronRight,
  X, Check, AlertCircle, Users, Eye, ArrowRight, ArrowLeft, Key, UserPlus
} from 'lucide-react';

// ─── Types ───────────────────────────────────────────────────────
interface StudentItem {
  id: number;
  computer_code: number;
  enrollment_no: string | null;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  date_of_birth: string | null;
  gender: string | null;
  mobile: string | null;
  email: string | null;
  abc_id: string | null;
  aadhar_no: string | null;
  active: boolean;
}

interface StudentFormData {
  // Personal
  computer_code: string;
  enrollment_no: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  mobile: string;
  email: string;
  abc_id: string;
  aadhar_no: string;
  blood_group: string;
  category: string;
  religion: string;
  
  // Admission
  academic_program_id: string;
  academic_session_id: string;
  admission_date: string;
  admission_type: string;
  quota: string;
  admission_round: string;
  entry_semester: string;
  status: string;
  
  // Address
  address_type: string;
  address_line: string;
  district: string;
  state: string;
  pincode: string;
  
  // Guardian
  guardian_relation: string;
  guardian_name: string;
  guardian_mobile: string;
  guardian_email: string;
  guardian_occupation: string;
  
  // Qualification
  qual_type: string;
  qual_board: string;
  qual_year: string;
  qual_percentage: string;
  
  // Entrance
  exam_name: string;
  exam_roll: string;
  exam_score: string;
}

const emptyForm: StudentFormData = {
  computer_code: '', enrollment_no: '',
  first_name: '', middle_name: '', last_name: '',
  date_of_birth: '', gender: '', mobile: '', email: '',
  abc_id: '', aadhar_no: '', blood_group: '', category: '', religion: '',
  academic_program_id: '', academic_session_id: '', admission_date: '', admission_type: 'regular',
  quota: '', admission_round: '', entry_semester: '1', status: 'active',
  address_type: 'permanent', address_line: '', district: '', state: '', pincode: '',
  guardian_relation: 'father', guardian_name: '', guardian_mobile: '', guardian_email: '', guardian_occupation: '',
  qual_type: '12th', qual_board: '', qual_year: '', qual_percentage: '',
  exam_name: '', exam_roll: '', exam_score: ''
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
        className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${error ? 'border-red-400' : 'border-slate-300'}`}
      >
        <option value="">Select</option>
        <option value="M">Male</option>
        <option value="F">Female</option>
        <option value="O">Other</option>
      </select>
    ) : name === 'guardian_relation' ? (
        <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${error ? 'border-red-400' : 'border-slate-300'}`}
      >
        <option value="father">Father</option>
        <option value="mother">Mother</option>
        <option value="guardian">Guardian</option>
      </select>
    ) : (
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className={`w-full px-3 py-2.5 border rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${error ? 'border-red-400' : 'border-slate-300'} ${disabled ? 'bg-slate-100 cursor-not-allowed' : ''}`}
      />
    )}
    {error && (
      <p className="text-xs text-red-500 mt-1">{error}</p>
    )}
  </div>
);

// ─── Student Form ───────────────────────────────────────────
const StudentForm = ({ 
  isCreate, onSubmit, onCancel, form, setForm, formErrors, submitting, programs, sessions
}: { 
  isCreate: boolean; onSubmit: () => void; onCancel: () => void; form: StudentFormData; setForm: (f: StudentFormData) => void; formErrors: Record<string, string>; submitting: boolean;
  programs: any[];
  sessions: any[];
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const handleChange = (name: keyof StudentFormData) => (val: string) => setForm({ ...form, [name]: val });

  useEffect(() => {
    if (Object.keys(formErrors).length > 0) {
      const firstErrorField = Object.keys(formErrors)[0];
      const tab0Fields = [
        'computer_code', 'enrollment_no', 'first_name', 'middle_name', 
        'last_name', 'gender', 'date_of_birth', 'mobile', 'email', 
        'aadhar_no', 'abc_id', 'blood_group', 'category', 'religion'
      ];
      const tab1Fields = [
        'academic_program_id', 'academic_session_id', 'admission_date', 
        'admission_type', 'quota', 'admission_round', 'entry_semester', 'status'
      ];
      const tab2Fields = [
        'address_type', 'address_line', 'district', 'state', 'pincode', 
        'guardian_relation', 'guardian_name', 'guardian_mobile', 'guardian_email', 'guardian_occupation'
      ];
      const tab3Fields = [
        'qual_type', 'qual_board', 'qual_year', 'qual_percentage', 
        'exam_name', 'exam_roll', 'exam_score'
      ];
      
      if (tab0Fields.includes(firstErrorField)) {
        setActiveTab(0);
      } else if (tab1Fields.includes(firstErrorField)) {
        setActiveTab(1);
      } else if (tab2Fields.includes(firstErrorField)) {
        setActiveTab(2);
      } else if (tab3Fields.includes(firstErrorField)) {
        setActiveTab(3);
      }
    }
  }, [formErrors]);

  const tabs = ["Personal", "Academic", "Address & Guardian", "Qualifications", "Preview"];

  const renderTabContent = () => {
    switch(activeTab) {
      case 0:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Computer Code" name="computer_code" value={form.computer_code} onChange={handleChange('computer_code')} error={formErrors.computer_code} required placeholder="e.g. 260001" disabled={!isCreate} type="number" />
            <FormField label="Enrollment No" name="enrollment_no" value={form.enrollment_no} onChange={handleChange('enrollment_no')} error={formErrors.enrollment_no} placeholder="e.g. EN123456" />
            <FormField label="First Name" name="first_name" value={form.first_name} onChange={handleChange('first_name')} error={formErrors.first_name} required placeholder="First name" />
            <FormField label="Middle Name" name="middle_name" value={form.middle_name} onChange={handleChange('middle_name')} error={formErrors.middle_name} placeholder="Middle name" />
            <FormField label="Last Name" name="last_name" value={form.last_name} onChange={handleChange('last_name')} error={formErrors.last_name} placeholder="Last name" />
            <FormField label="Gender" name="gender" value={form.gender} onChange={handleChange('gender')} error={formErrors.gender} />
            <FormField label="Date of Birth" name="date_of_birth" value={form.date_of_birth} onChange={handleChange('date_of_birth')} error={formErrors.date_of_birth} type="date" required={isCreate} />
            <FormField label="Mobile" name="mobile" value={form.mobile} onChange={handleChange('mobile')} error={formErrors.mobile} placeholder="10-15 digits" />
            <FormField label="Email" name="email" value={form.email} onChange={handleChange('email')} error={formErrors.email} type="email" placeholder="email@example.com" />
            <FormField label="Aadhar Number" name="aadhar_no" value={form.aadhar_no} onChange={handleChange('aadhar_no')} error={formErrors.aadhar_no} placeholder="12 digits" />
            <FormField label="ABC ID" name="abc_id" value={form.abc_id} onChange={handleChange('abc_id')} error={formErrors.abc_id} placeholder="ABC ID" />
            <FormField label="Blood Group" name="blood_group" value={form.blood_group} onChange={handleChange('blood_group')} error={formErrors.blood_group} placeholder="e.g. O+" />
            <FormField label="Category" name="category" value={form.category} onChange={handleChange('category')} error={formErrors.category} placeholder="General/OBC/SC/ST" />
            <FormField label="Religion" name="religion" value={form.religion} onChange={handleChange('religion')} error={formErrors.religion} placeholder="e.g. Hindu" />
          </div>
        );
      case 1:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Academic Program {isCreate && <span className="text-red-500">*</span>}</label>
              <select
                value={form.academic_program_id}
                onChange={(e) => handleChange('academic_program_id')(e.target.value)}
                disabled={!isCreate}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${formErrors.academic_program_id ? 'border-red-400' : 'border-slate-300'}`}
              >
                <option value="">Select Program</option>
                {programs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              {formErrors.academic_program_id && <p className="text-xs text-red-500 mt-1">{formErrors.academic_program_id}</p>}
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Academic Session {isCreate && <span className="text-red-500">*</span>}</label>
              <select
                value={form.academic_session_id}
                onChange={(e) => handleChange('academic_session_id')(e.target.value)}
                disabled={!isCreate}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 ${formErrors.academic_session_id ? 'border-red-400' : 'border-slate-300'}`}
              >
                <option value="">Select Session</option>
                {sessions.map(s => <option key={s.id} value={s.id}>{s.session_name}</option>)}
              </select>
              {formErrors.academic_session_id && <p className="text-xs text-red-500 mt-1">{formErrors.academic_session_id}</p>}
            </div>
            <FormField label="Admission Date" name="admission_date" value={form.admission_date} onChange={handleChange('admission_date')} error={formErrors.admission_date} type="date" required={isCreate} disabled={!isCreate} />
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Admission Type</label>
              <select
                value={form.admission_type}
                onChange={(e) => handleChange('admission_type')(e.target.value)}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 border-slate-300`}
              >
                <option value="regular">Regular</option>
                <option value="lateral">Lateral</option>
                <option value="transfer">Transfer</option>
              </select>
            </div>
            <FormField label="Quota" name="quota" value={form.quota} onChange={handleChange('quota')} error={formErrors.quota} placeholder="e.g. Management" />
            <FormField label="Entry Semester" name="entry_semester" value={form.entry_semester} onChange={handleChange('entry_semester')} error={formErrors.entry_semester} type="number" />
          </div>
        );
      case 2:
        return (
          <div className="space-y-6">
            <div>
                <h4 className="font-semibold text-slate-800 border-b pb-2 mb-4">Address</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="md:col-span-2">
                    <FormField label="Address Line" name="address_line" value={form.address_line} onChange={handleChange('address_line')} error={formErrors.address_line} required={isCreate} placeholder="Full address" />
                    </div>
                    <FormField label="District" name="district" value={form.district} onChange={handleChange('district')} error={formErrors.district} placeholder="District" />
                    <FormField label="State" name="state" value={form.state} onChange={handleChange('state')} error={formErrors.state} placeholder="State" />
                    <FormField label="Pincode" name="pincode" value={form.pincode} onChange={handleChange('pincode')} error={formErrors.pincode} placeholder="e.g. 452012" />
                </div>
            </div>
            <div>
                <h4 className="font-semibold text-slate-800 border-b pb-2 mb-4">Guardian Details</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField label="Relation" name="guardian_relation" value={form.guardian_relation} onChange={handleChange('guardian_relation')} error={formErrors.guardian_relation} />
                    <FormField label="Name" name="guardian_name" value={form.guardian_name} onChange={handleChange('guardian_name')} error={formErrors.guardian_name} required={isCreate} placeholder="Guardian name" />
                    <FormField label="Mobile" name="guardian_mobile" value={form.guardian_mobile} onChange={handleChange('guardian_mobile')} error={formErrors.guardian_mobile} placeholder="10-15 digits" />
                    <FormField label="Occupation" name="guardian_occupation" value={form.guardian_occupation} onChange={handleChange('guardian_occupation')} error={formErrors.guardian_occupation} placeholder="Occupation" />
                </div>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-6">
            <div>
                <h4 className="font-semibold text-slate-800 border-b pb-2 mb-4">Previous Qualification</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1.5">Qualification Type</label>
                    <select
                        value={form.qual_type}
                        onChange={(e) => handleChange('qual_type')(e.target.value)}
                        className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 border-slate-300`}
                    >
                        <option value="10th">10th</option>
                        <option value="12th">12th</option>
                        <option value="Diploma">Diploma</option>
                        <option value="UG">UG</option>
                        <option value="PG">PG</option>
                        <option value="Other">Other</option>
                    </select>
                    </div>
                    <FormField label="Board / University" name="qual_board" value={form.qual_board} onChange={handleChange('qual_board')} error={formErrors.qual_board} placeholder="e.g. CBSE" />
                    <FormField label="Passing Year" name="qual_year" value={form.qual_year} onChange={handleChange('qual_year')} error={formErrors.qual_year} type="number" placeholder="YYYY" />
                    <FormField label="Percentage / CGPA" name="qual_percentage" value={form.qual_percentage} onChange={handleChange('qual_percentage')} error={formErrors.qual_percentage} type="number" placeholder="e.g. 85.5" />
                </div>
            </div>
            <div>
                <h4 className="font-semibold text-slate-800 border-b pb-2 mb-4">Entrance Exam</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField label="Exam Name" name="exam_name" value={form.exam_name} onChange={handleChange('exam_name')} error={formErrors.exam_name} placeholder="e.g. JEE Mains" />
                    <FormField label="Roll Number" name="exam_roll" value={form.exam_roll} onChange={handleChange('exam_roll')} error={formErrors.exam_roll} placeholder="Roll no" />
                    <FormField label="Score / Rank" name="exam_score" value={form.exam_score} onChange={handleChange('exam_score')} error={formErrors.exam_score} type="number" />
                </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-6">
            <div className="bg-slate-50 p-6 rounded-xl border border-slate-100 text-center">
              <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users size={32} />
              </div>
              <h3 className="text-xl font-bold text-slate-800">
                {form.first_name} {form.last_name}
              </h3>
              <p className="text-slate-500 mt-1">{form.email || 'No email provided'}</p>
            </div>

            {isCreate && (
              <div className="bg-amber-50 p-6 rounded-xl border border-amber-200">
                <h4 className="font-semibold text-amber-800 mb-3 flex items-center gap-2">
                  <Key size={18} /> Default Credentials
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-amber-100">
                    <span className="text-slate-500 text-sm">Username</span>
                    <span className="font-mono font-medium text-slate-800">Auto-generated</span>
                  </div>
                  <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-amber-100">
                    <span className="text-slate-500 text-sm">Password</span>
                    <span className="font-mono font-medium text-slate-800">
                      {form.date_of_birth ? form.date_of_birth.split('-').reverse().join('') : 'password'}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-amber-600 mt-4 text-center">
                  Students cannot change their passwords. Admins can reset passwords to DOB.
                </p>
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex border-b border-slate-200 mb-6 overflow-x-auto shrink-0 hide-scrollbar">
        {tabs.map((tab, idx) => (
          <button
            key={tab}
            onClick={() => setActiveTab(idx)}
            className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              activeTab === idx 
                ? 'border-blue-600 text-blue-600' 
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-h-[300px] pb-4">
        {renderTabContent()}
      </div>

      {/* Footer Navigation */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200 mt-auto shrink-0 bg-white">
        <button
          onClick={activeTab === 0 ? onCancel : () => setActiveTab(activeTab - 1)}
          className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors font-medium text-sm flex items-center gap-2"
        >
          {activeTab === 0 ? 'Cancel' : <><ChevronLeft size={16} /> Back</>}
        </button>

        {activeTab < tabs.length - 1 ? (
          <button
            onClick={() => setActiveTab(activeTab + 1)}
            className="px-4 py-2 bg-slate-800 text-white hover:bg-slate-700 rounded-lg transition-colors font-medium text-sm flex items-center gap-2 shadow-sm"
          >
            Next <ChevronRight size={16} />
          </button>
        ) : (
          <button
            onClick={onSubmit}
            disabled={submitting}
            className="px-6 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-all font-medium text-sm flex items-center gap-2 shadow-md shadow-blue-500/20 disabled:opacity-70"
          >
            {submitting ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
            {isCreate ? 'Admit Student' : 'Save Changes'}
          </button>
        )}
      </div>
    </div>
  );
};
export default function StudentManagement() {
  const { user } = useAuth();
  const [students, setStudents] = useState<StudentItem[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Master data
  const [programs, setPrograms] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [limit] = useState(10);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<StudentItem | null>(null);
  const [form, setForm] = useState<StudentFormData>(emptyForm);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  
  const [toast, setToast] = useState<{msg: string, type: 'success'|'error'} | null>(null);

  const fetchStudents = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get('/students', { params: { skip: page * limit, limit } });
      setStudents(res.data?.data || []);
    } catch (e) {
      console.error("Failed to load students", e);
    } finally {
      setLoading(false);
    }
  }, [page, limit]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  useEffect(() => {
    const fetchMasterData = async () => {
      try {
        const [progRes, sessRes] = await Promise.all([
          api.get('/academic/programs'),
          api.get('/academic/academic-sessions')
        ]);
        setPrograms(progRes.data?.data || []);
        setSessions(sessRes.data?.data || []);
      } catch (e) {
        console.error("Failed to load master data", e);
      }
    };
    fetchMasterData();
  }, []);

  const openCreateModal = () => {
    setSelectedStudent(null);
    setForm(emptyForm);
    setFormErrors({});
    setIsModalOpen(true);
  };

  const openEditModal = async (s: StudentItem) => {
    try {
      setLoading(true);
      const res = await api.get(`/students/${s.id}`);
      const data = res.data?.data;
      const st = data.student;
      const adm = data.admission || {};
      const addr = data.addresses?.[0] || {};
      const gd = data.guardians?.[0] || {};
      const ql = data.qualifications?.[0] || {};
      const ex = data.entrance_exams?.[0] || {};

      setForm({
        computer_code: st.computer_code?.toString() || '',
        enrollment_no: st.enrollment_no || '',
        first_name: st.first_name || '', middle_name: st.middle_name || '', last_name: st.last_name || '',
        date_of_birth: st.date_of_birth || '', gender: st.gender || '', mobile: st.mobile || '',
        email: st.email || '', abc_id: st.abc_id || '', aadhar_no: st.aadhar_no || '',
        blood_group: st.blood_group || '', category: st.category || '', religion: st.religion || '',
        
        academic_program_id: adm.academic_program_id?.toString() || '',
        academic_session_id: adm.academic_session_id?.toString() || '',
        admission_date: adm.admission_date || '',
        admission_type: adm.admission_type || 'regular',
        quota: adm.quota || '', admission_round: adm.admission_round || '',
        entry_semester: adm.entry_semester?.toString() || '1', status: adm.status || 'active',
        
        address_type: addr.address_type || 'permanent',
        address_line: addr.address_line || '', district: addr.district || '',
        state: addr.state || '', pincode: addr.pincode || '',
        
        guardian_relation: gd.relation || 'father', guardian_name: gd.name || '',
        guardian_mobile: gd.mobile || '', guardian_email: gd.email || '', guardian_occupation: gd.occupation || '',
        
        qual_type: ql.qualification_type || '12th', qual_board: ql.board_university || '',
        qual_year: ql.passing_year?.toString() || '', qual_percentage: ql.percentage?.toString() || '',
        
        exam_name: ex.exam_name || '', exam_roll: ex.roll_no || '', exam_score: ex.score?.toString() || ''
      });
      setSelectedStudent(s);
      setFormErrors({});
      setIsModalOpen(true);
    } catch (e) {
      setToast({ msg: 'Failed to fetch student details', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to deactivate/delete this student?")) return;
    try {
      await api.delete(`/students/${id}`);
      setToast({ msg: 'Student deactivated successfully', type: 'success' });
      fetchStudents();
    } catch (e) {
      setToast({ msg: 'Failed to deactivate student', type: 'error' });
    }
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.computer_code) errs.computer_code = "Required";
    if (!form.first_name) errs.first_name = "Required";
    if (!selectedStudent) {
        if (!form.date_of_birth) errs.date_of_birth = "Required";
        if (!form.academic_program_id) errs.academic_program_id = "Required";
        if (!form.academic_session_id) errs.academic_session_id = "Required";
        if (!form.admission_date) errs.admission_date = "Required";
        
        if (!form.address_line) {
          errs.address_line = "Required";
        } else if (form.address_line.length < 5) {
          errs.address_line = "Must be at least 5 characters";
        }
        
        if (!form.guardian_name) errs.guardian_name = "Required";
    } else {
        if (form.address_line && form.address_line.length < 5) {
          errs.address_line = "Must be at least 5 characters";
        }
    }
    
    if (form.aadhar_no && !/^\d{12}$/.test(form.aadhar_no)) {
      errs.aadhar_no = "Must be exactly 12 digits";
    }
    if (form.mobile && !/^\+?\d{10,15}$/.test(form.mobile)) {
      errs.mobile = "Must be 10-15 digits";
    }
    if (form.guardian_mobile && !/^\+?\d{10,15}$/.test(form.guardian_mobile)) {
      errs.guardian_mobile = "Must be 10-15 digits";
    }
    
    setFormErrors(errs);
    if (Object.keys(errs).length > 0) {
      setToast({ msg: "Please fix validation errors", type: "error" });
    }
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    
    const payload = {
      student: {
        computer_code: parseInt(form.computer_code),
        enrollment_no: form.enrollment_no || null,
        first_name: form.first_name,
        middle_name: form.middle_name || null,
        last_name: form.last_name || null,
        gender: form.gender || null,
        date_of_birth: form.date_of_birth || null,
        mobile: form.mobile || null,
        email: form.email || null,
        abc_id: form.abc_id || null,
        aadhar_no: form.aadhar_no || null,
        blood_group: form.blood_group || null,
        category: form.category || null,
        religion: form.religion || null
      },
      admission: {
        academic_program_id: parseInt(form.academic_program_id),
        academic_session_id: parseInt(form.academic_session_id),
        admission_date: form.admission_date,
        admission_type: form.admission_type,
        quota: form.quota || null,
        admission_round: form.admission_round || null,
        entry_semester: parseInt(form.entry_semester) || 1,
        status: form.status
      },
      addresses: form.address_line ? [{
        address_type: form.address_type,
        address_line: form.address_line,
        district: form.district || null,
        state: form.state || null,
        pincode: form.pincode || null
      }] : [],
      guardians: form.guardian_name ? [{
        relation: form.guardian_relation,
        name: form.guardian_name,
        mobile: form.guardian_mobile || null,
        email: form.guardian_email || null,
        occupation: form.guardian_occupation || null
      }] : [],
      qualifications: form.qual_type ? [{
        qualification_type: form.qual_type,
        board_university: form.qual_board || null,
        passing_year: form.qual_year ? parseInt(form.qual_year) : null,
        percentage: form.qual_percentage ? parseFloat(form.qual_percentage) : null
      }] : [],
      entrance_exams: form.exam_name ? [{
        exam_name: form.exam_name,
        roll_no: form.exam_roll || null,
        score: form.exam_score ? parseFloat(form.exam_score) : null
      }] : []
    };

    try {
      setSubmitting(true);
      if (selectedStudent) {
        // Drop admission if it's empty (during edit) to avoid NaN parsing issues
        const updatePayload = { ...payload };
        if (isNaN(updatePayload.admission.academic_program_id)) {
            // Remove admission from update payload if not provided
            delete (updatePayload as any).admission;
        }
        await api.put(`/students/${selectedStudent.id}`, updatePayload);
        setToast({ msg: 'Student updated successfully', type: 'success' });
      } else {
        await api.post('/students', payload);
        setToast({ msg: 'Student admitted successfully', type: 'success' });
      }
      setIsModalOpen(false);
      fetchStudents();
    } catch (err: any) {
      setToast({ msg: err.response?.data?.detail || 'Failed to save student', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const filteredStudents = students.filter(s => 
    (s.first_name + ' ' + (s.last_name || '')).toLowerCase().includes(search.toLowerCase()) ||
    s.computer_code?.toString().includes(search) ||
    s.mobile?.includes(search)
  );

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-screen space-y-8 animate-fade-in">
      {toast && <Toast message={toast.msg} type={toast.type} onClose={() => setToast(null)} />}

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Student Directory</h1>
          <p className="text-slate-500 mt-1">Manage admissions, academic records, and student profiles.</p>
        </div>
        <PermissionGuard permission="student.create">
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-500/20 transition-all font-medium whitespace-nowrap"
          >
            <UserPlus size={18} />
            Admit Student
          </button>
        </PermissionGuard>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative w-full sm:w-80 group">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 group-focus-within:text-blue-500 transition-colors">
              <Search size={18} />
            </div>
            <input
              type="text"
              placeholder="Search by name, code, or mobile..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          {loading && !isModalOpen ? (
            <div className="flex justify-center items-center h-64 text-blue-500">
              <Loader2 className="animate-spin" size={32} />
            </div>
          ) : (
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4">Comp. Code</th>
                  <th className="px-6 py-4">Name</th>
                  <th className="px-6 py-4">Mobile</th>
                  <th className="px-6 py-4">Enrollment No.</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredStudents.length === 0 ? (
                  <tr><td colSpan={6} className="text-center py-12 text-slate-500">No students found.</td></tr>
                ) : filteredStudents.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-900">{s.computer_code}</td>
                    <td className="px-6 py-4 font-medium">{s.first_name} {s.last_name}</td>
                    <td className="px-6 py-4">{s.mobile || '-'}</td>
                    <td className="px-6 py-4">{s.enrollment_no || '-'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${s.active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                        {s.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <PermissionGuard permission="student.delete">
                            <button onClick={() => handleDelete(s.id)} className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors" title="Deactivate/Delete">
                                <Trash2 size={16} />
                            </button>
                        </PermissionGuard>
                        <PermissionGuard permission="student.update">
                            <button onClick={() => openEditModal(s)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Edit">
                                <Edit2 size={16} />
                            </button>
                        </PermissionGuard>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between bg-slate-50/50">
          <span className="text-sm text-slate-500 font-medium">Showing {filteredStudents.length} students</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="p-2 border border-slate-200 rounded-lg hover:bg-white disabled:opacity-50 transition-colors bg-slate-50">
              <ChevronLeft size={16} />
            </button>
            <button onClick={() => setPage(p => p + 1)} disabled={students.length < limit} className="p-2 border border-slate-200 rounded-lg hover:bg-white disabled:opacity-50 transition-colors bg-slate-50">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {isModalOpen && (
        <Modal title={selectedStudent ? 'Edit Student' : 'Admit New Student'} onClose={() => setIsModalOpen(false)} wide>
          <StudentForm
            isCreate={!selectedStudent}
            onSubmit={handleSubmit}
            onCancel={() => setIsModalOpen(false)}
            form={form}
            setForm={setForm}
            formErrors={formErrors}
            submitting={submitting}
            programs={programs}
            sessions={sessions}
          />
        </Modal>
      )}
    </div>
  );
}
