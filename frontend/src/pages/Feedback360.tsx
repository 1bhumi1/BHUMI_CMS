import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { Send } from "lucide-react";
import FeedbackChatbot from '../components/FeedbackChatbot';
import { useAuth } from '../lib/AuthContext';
import {
  Loader2, X, Check, AlertCircle, Eye, ChevronDown, ChevronUp,
  Save, BookOpen, Info, Users, School, HeartHandshake, Star,
  Printer, ArrowRight, ArrowLeft, Plus, Trash2, ShieldCheck, Lock,
  FileSpreadsheet, ClipboardList, CheckCircle2, AlertOctagon, HelpCircle
} from 'lucide-react';

// ─── Constants & Metadata ────────────────────────────────────────
const cat2Categories = [
  { key: '1', sno: '1', particulars: 'Research Papers in Peer-Reviewed or UGC listed journals (08 points per paper for Faculty of Sciences/Engineering, 10 points per paper for Humanities)', indent: 0 },
  { key: '2', sno: '2', particulars: 'Publications (other than Research papers)', indent: 0, headerOnly: true },
  { key: '2.a', sno: '(a)', particulars: 'Books authored which are published by:', indent: 1, headerOnly: true },
  { key: '2.a.i', sno: '(i)', particulars: 'International publishers (12 points max)', indent: 2 },
  { key: '2.a.ii', sno: '(ii)', particulars: 'National publishers (10 points max)', indent: 2 },
  { key: '2.a.iii', sno: '(iii)', particulars: 'Chapter in edited book (5 points max)', indent: 2 },
  { key: '2.a.iv', sno: '(iv)', particulars: 'Editor of book by International Publisher (10 points max)', indent: 2 },
  { key: '2.a.v', sno: '(v)', particulars: 'Editor of book by National Publisher (08 points max)', indent: 2 },
  { key: '2.b', sno: '(b)', particulars: 'Translation works in Indian and Foreign Languages by qualified faculties', indent: 1, headerOnly: true },
  { key: '2.b.i', sno: '(i)', particulars: 'Chapter or Research Paper (03 points max)', indent: 2 },
  { key: '2.b.ii', sno: '(ii)', particulars: 'Book (08 points max)', indent: 2 },
  { key: '3', sno: '3', particulars: 'Creation of ICT mediated Teaching Learning pedagogy and content and development of new and innovative courses and curricula', indent: 0, headerOnly: true },
  { key: '3.a', sno: '(a)', particulars: 'Development of Innovative pedagogy (05 points max)', indent: 1 },
  { key: '3.b', sno: '(b)', particulars: 'Design of new curricula and courses (02 points per curricula/courses)', indent: 1 },
  { key: '3.c', sno: '(c)', particulars: 'MOOCs', indent: 1, headerOnly: true },
  { key: '3.c.i', sno: '(i)', particulars: 'Development of complete MOOCs in 4 quadrants (4 credit course)(In case of MOOCs of lesser credits 05 marks/credit)(20 points max)', indent: 2 },
  { key: '3.c.ii', sno: '(ii)', particulars: 'MOOCs (developed in 4 quadrant) per module/lecture (05 points max)', indent: 2 },
  { key: '3.c.iii', sno: '(iii)', particulars: 'Content writer/subject matter expert for each module of MOOCs (at least one quadrant) (02 points max)', indent: 2 },
  { key: '3.c.iv', sno: '(iv)', particulars: 'Course Coordinator for MOOCs (4 credit course)(in case of MOOCs of lesser credits 02 credit)(08 points max)', indent: 2 },
  { key: '3.d', sno: '(d)', particulars: 'E-Content', indent: 1, headerOnly: true },
  { key: '3.d.i', sno: '(i)', particulars: 'Development of e-Content in 4 quadrants for a complete course/e-book (12 points max)', indent: 2 },
  { key: '3.d.ii', sno: '(ii)', particulars: 'e-Content developed in 4 quadrants for a complete course/e-book (05 points max)', indent: 2 },
  { key: '3.d.iii', sno: '(iii)', particulars: 'Contribution to development of e-content module in complete course/paper/e-book (at least one quadrant) (02 points max)', indent: 2 },
  { key: '3.d.iv', sno: '(iv)', particulars: 'Editor of e-content for complete course/paper/e-book (10 points max)', indent: 2 },
  { key: '4.a', sno: '4', particulars: '(a) Research guidance', indent: 0, headerOnly: true },
  { key: '4.a.i', sno: '(i)', particulars: 'Ph.D. (10 points per degree awarded, 05 points per thesis submitted)', indent: 1 },
  { key: '4.a.ii', sno: '(ii)', particulars: 'M.Phil/P.G. dissertation (02 per degree awarded)', indent: 1 },
  { key: '4.b', sno: '', particulars: '(b) Research Projects Completed', indent: 0, headerOnly: true },
  { key: '4.b.i', sno: '(i)', particulars: 'More than 10 lakhs (10 points max)', indent: 1 },
  { key: '4.b.ii', sno: '(ii)', particulars: 'Less than 10 lakhs (05 points max)', indent: 1 },
  { key: '4.c', sno: '', particulars: '(c) Research Projects Ongoing', indent: 0, headerOnly: true },
  { key: '4.c.i', sno: '(i)', particulars: 'More than 10 lakhs (05 points max)', indent: 1 },
  { key: '4.c.ii', sno: '(ii)', particulars: 'Less than 10 lakhs (02 points max)', indent: 1 },
  { key: '4.d', sno: '(d)', particulars: 'Consultancy (03 points max)', indent: 0 },
  { key: '5.a', sno: '5', particulars: '(a) Patents', indent: 0, headerOnly: true },
  { key: '5.a.i', sno: '(i)', particulars: 'International (10 points max)', indent: 1 },
  { key: '5.a.ii', sno: '(ii)', particulars: 'National (07 points max)', indent: 1 },
  { key: '5.b', sno: '', particulars: '(b) *Policy Document (submitted to an International body/organisation like UNO/UNESCO/World Bank/International Monetary Fund etc. or Central Government)', indent: 0, headerOnly: true },
  { key: '5.b.i', sno: '(i)', particulars: 'International (10 points max)', indent: 1 },
  { key: '5.b.ii', sno: '(ii)', particulars: 'National (07 points max)', indent: 1 },
  { key: '5.b.iii', sno: '(iii)', particulars: 'State (04 points max)', indent: 1 },
  { key: '5.c', sno: '', particulars: '(c) Awards/Fellowship', indent: 0, headerOnly: true },
  { key: '5.c.i', sno: '(i)', particulars: 'International (07 points max)', indent: 1 },
  { key: '5.c.ii', sno: '(ii)', particulars: 'National (05 points max)', indent: 1 },
  { key: '6', sno: '6', particulars: '*Invited lectures/Resource Person/paper presentation in seminars/conferences/full paper in Conference Proceedings (Paper presented in seminars/conferences and also published as full paper in Conference Proceedings will be counted only once)', indent: 0, headerOnly: true },
  { key: '6.i', sno: '(i)', particulars: 'International (Abroad) (07 points max)', indent: 1 },
  { key: '6.ii', sno: '(ii)', particulars: 'International (Within Country) (05 points max)', indent: 1 },
  { key: '6.iii', sno: '(iii)', particulars: 'National (03 points max)', indent: 1 },
  { key: '6.iv', sno: '(iv)', particulars: 'State/University (02 points max)', indent: 1 }
];

const cat3Categories = [
  { key: '1', sno: '1', particulars: 'Research paper in SCI Journal – 05 marks per paper.' },
  { key: '2', sno: '2', particulars: 'Research paper in Referred/ UGC approved Journal – 03 marks per paper equally distributed amongst the authors.' },
  { key: '3', sno: '3', particulars: 'Research paper presented in conferences – 02 marks per paper.' },
  { key: '4', sno: '4', particulars: 'Reviewer for research paper in referred/UGC journal – 02 marks per paper.' },
  { key: '5', sno: '5', particulars: 'Books/ patents published – 06 marks per book/ patent.' },
  { key: '6', sno: '6', particulars: 'Certification of online courses such as MOOCs – 04 marks per course successfully completed.' },
  { key: '7', sno: '7', particulars: 'Contribution to the development of e-content for complete course – 04 marks per course.' },
  { key: '8', sno: '8', particulars: 'Award of Ph.D. degree - 05 marks.' },
  { key: '9', sno: '9', particulars: 'Ph.D. guidance successfully completed - 05 marks per guidance.' },
  { key: '10', sno: '10', particulars: 'PG guidance successfully completed – 02 marks per project.' },
  { key: '11', sno: '11', particulars: 'Sponsored R & D projects completed - 03 marks per project.' },
  { key: '12', sno: '12', particulars: 'Sponsored R & D projects ongoing - 02 marks per project.' },
  { key: '13', sno: '13', particulars: 'Awards/ fellowships (only National/ International level) – 05 marks.' },
  { key: '14', sno: '14', particulars: 'Guest/ Expert lectures delivered - Local 01 marks per hr. - State level 02 marks per hr. - National level 04 marks per hr.' }
];

const confidentialParameters = [
  { sno: 1, key: 'parameter_1', label: 'Punctuality & sincerity in conducting classes' },
  { sno: 2, key: 'parameter_2', label: 'Punctuality & reporting to the department for duty' },
  { sno: 3, key: 'parameter_3', label: 'Leave Record (Deduct 1 mark per LWP and assess accordingly)' },
  { sno: 4, key: 'parameter_4', label: 'Behaviour with students and stakeholders' },
  { sno: 5, key: 'parameter_5', label: 'Sense of responsibility' },
  { sno: 6, key: 'parameter_6', label: 'Completion of assigned work in time' },
  { sno: 7, key: 'parameter_7', label: 'Contribution to laboratories and department development' }
];

const emptyForm = () => ({
  faculty_computer_code: '',
  academic_session: '',
  submited: false,
  hod_approval: false,
  cr: {
    cr1: 10, cr2: 10, cr3: 10, cr4: 10, cr5: 10,
    cr6: 10, cr7: 10, cr8: 10, cr9: 10, cr10: 10
  },
  cat1i: [] as any[],
  cat1ii: [] as any[],
  cat1iii: [] as any[],
  cat1iv: [] as any[],
  cat1v: [] as any[],
  cat2: cat2Categories.filter(c => !c.headerOnly).map(c => ({ sno: c.key, score: '0' })),
  cat3: cat3Categories.map(c => ({ sno: c.key, score: '0' }))
});

// Toast notification helper
const Toast = ({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`fixed top-6 right-6 z-[100] flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl text-white text-sm font-medium animate-slide-in ${type === 'success' ? 'bg-emerald-600' : 'bg-red-600'
      }`}>
      {type === 'success' ? <Check size={18} /> : <AlertCircle size={18} />}
      <span className="whitespace-pre-wrap">{message}</span>
      <button onClick={onClose} className="ml-2 hover:opacity-70"><X size={16} /></button>
    </div>
  );
};

const parseError = (e: any): string => {
  console.error("API Error details:", e.response?.data || e);
  if (e.response?.data) {
    const data = e.response.data;
    if (data.detail) {
      if (Array.isArray(data.detail)) {
        return data.detail.map((err: any) => {
          const field = err.loc ? err.loc.slice(1).join('.') : '';
          return field ? `${field}: ${err.msg}` : err.msg;
        }).join('\n');
      }
      return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    }
    if (data.message) {
      return String(data.message);
    }
  }
  return e.message || "Network Error";
};

export default function Feedback360() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, role, isAdmin, isStaff } = useAuth();

  // Mode states
  const [viewMode, setViewMode] = useState<'teacher' | 'review' | 'principal' | 'staff-review'>('teacher');
  const [activeSubForm, setActiveSubForm] = useState<'none' | 'cat1i' | 'cat1ii' | 'cat1iii' | 'cat1iv' | 'cat1v' | 'cat2' | 'cat3' | 'confidential'>('none');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

  // Core metadata appraisal states
  const [appraisalStatus, setAppraisalStatus] = useState<
    'Draft' | 'Submitted' | 'Under HOD Review' | 'Forwarded to Principal' | 'Principal Approved' | 'Principal Rejected' | 'HOD Approved' | 'HOD Rejected' | 'Confidential Report Submitted' | 'Submitted to HOD'
  >('Draft');
  const [hodRemarks, setHodRemarks] = useState('');
  const [submittedAt, setSubmittedAt] = useState('');
  const [approvedAt, setApprovedAt] = useState('');
  const [lastModified, setLastModified] = useState('');

  // Role lists
  const [departmentList, setDepartmentList] = useState<any[]>([]);
  const [principalList, setPrincipalList] = useState<any[]>([]);
  const [staffCache, setStaffCache] = useState<{ [code: string]: any }>({});
  const [isHOD, setIsHOD] = useState(false);

  // Selection targets
  const [selectedFacultyCode, setSelectedFacultyCode] = useState<string>('');
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null);

  // Dropdown lists
  const [sessionsDropdown, setSessionsDropdown] = useState<any[]>([]);
  const [designations, setDesignations] = useState<any[]>([]);
  const [activeSession, setActiveSession] = useState<any>(null);
  const [staffProfile, setStaffProfile] = useState<any>(null);
  const [facultyName, setFacultyName] = useState<string>('');

  // Confidential Form states & handlers
  const [loadedConfidential, setLoadedConfidential] = useState<any>(null);
  const [confidentialTargetFaculty, setConfidentialTargetFaculty] = useState<any>(null);

  // Bulk selection & printing states
  const [selectedAppraisals, setSelectedAppraisals] = useState<number[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [isStaffReviewOpen, setIsStaffReviewOpen] = useState(true);
  const [isCategory1Open, setIsCategory1Open] = useState(true);
  const [printType, setPrintType] = useState<'none' | 'cr' | 'api' | 'summary'>('none');
  const [printTarget, setPrintTarget] = useState<any>(null);
  const [confidentialForm, setConfidentialForm] = useState<{
    parameter_1: number | '';
    parameter_2: number | '';
    parameter_3: number | '';
    parameter_4: number | '';
    parameter_5: number | '';
    parameter_6: number | '';
    parameter_7: number | '';
    remarks: string;
    status: 'Draft' | 'Submitted';
  }>({
    parameter_1: '',
    parameter_2: '',
    parameter_3: '',
    parameter_4: '',
    parameter_5: '',
    parameter_6: '',
    parameter_7: '',
    remarks: '',
    status: 'Draft'
  });

  const handleOpenConfidentialAssessment = async (item: any) => {
    if (role !== 'HOD' && !isAdmin()) {
      setToast({ msg: "Access Denied: Only HOD can access Confidential Reports.", type: 'error' });
      return;
    }
    setLoading(true);
    setConfidentialTargetFaculty(item);
    setSelectedRecordId(item.api_id);

    try {
      await loadRecordDetails(item.api_id);
      const res = await api.get(`/api360/confidential/${item.api_id}`);
      if (res.data?.success && res.data.data) {
        const d = res.data.data;
        setConfidentialForm({
          parameter_1: d.parameter_1 !== null ? d.parameter_1 : '',
          parameter_2: d.parameter_2 !== null ? d.parameter_2 : '',
          parameter_3: d.parameter_3 !== null ? d.parameter_3 : '',
          parameter_4: d.parameter_4 !== null ? d.parameter_4 : '',
          parameter_5: d.parameter_5 !== null ? d.parameter_5 : '',
          parameter_6: d.parameter_6 !== null ? d.parameter_6 : '',
          parameter_7: d.parameter_7 !== null ? d.parameter_7 : '',
          remarks: d.remarks || '',
          status: d.status || 'Draft'
        });
      } else {
        setConfidentialForm({
          parameter_1: '',
          parameter_2: '',
          parameter_3: '',
          parameter_4: '',
          parameter_5: '',
          parameter_6: '',
          parameter_7: '',
          remarks: '',
          status: 'Draft'
        });
      }
      setActiveSubForm('confidential' as any);
    } catch (e: any) {
      setToast({ msg: "Failed to load confidential report: " + parseError(e), type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfidentialAssessment = async (status: 'Draft' | 'Submitted') => {
    if (!selectedRecordId) return;

    if (status === 'Submitted') {
      const emptyParams = [
        confidentialForm.parameter_1, confidentialForm.parameter_2, confidentialForm.parameter_3,
        confidentialForm.parameter_4, confidentialForm.parameter_5, confidentialForm.parameter_6,
        confidentialForm.parameter_7
      ].some(p => p === '');

      if (emptyParams) {
        setToast({ msg: "Validation Error: All 7 parameters are mandatory for final submission.", type: 'error' });
        return;
      }

      if (!window.confirm("Are you sure you want to submit the Confidential Report?")) {
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload = {
        faculty_feedback_id: selectedRecordId,
        parameter_1: confidentialForm.parameter_1 === '' ? null : Number(confidentialForm.parameter_1),
        parameter_2: confidentialForm.parameter_2 === '' ? null : Number(confidentialForm.parameter_2),
        parameter_3: confidentialForm.parameter_3 === '' ? null : Number(confidentialForm.parameter_3),
        parameter_4: confidentialForm.parameter_4 === '' ? null : Number(confidentialForm.parameter_4),
        parameter_5: confidentialForm.parameter_5 === '' ? null : Number(confidentialForm.parameter_5),
        parameter_6: confidentialForm.parameter_6 === '' ? null : Number(confidentialForm.parameter_6),
        parameter_7: confidentialForm.parameter_7 === '' ? null : Number(confidentialForm.parameter_7),
        remarks: confidentialForm.remarks,
        status: status
      };

      const res = await api.post('/api360/confidential', payload);
      if (res.data?.success) {
        setToast({ msg: status === 'Submitted' ? "Confidential report submitted successfully!" : "Confidential report draft saved successfully", type: 'success' });
        await loadHODDashboard();
        setActiveSubForm('none');
        await loadRecordDetails(selectedRecordId);
      }
    } catch (e: any) {
      setToast({ msg: "Action failed: " + parseError(e), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleBulkForward = async () => {
    if (selectedAppraisals.length === 0) return;

    const unsubmitted = selectedAppraisals.map(id => departmentList.find(x => x.api_id === id)).filter(Boolean);
    const missingCR = unsubmitted.filter(item => {
      return !item.confidential || item.confidential.status !== 'Submitted';
    });

    if (missingCR.length > 0) {
      const names = missingCR.map(item => {
        const cache = staffCache[item.faculty_computer_code];
        return cache ? `${cache.staff?.first_name || ''} ${cache.staff?.last_name || ''}` : `Code ${item.faculty_computer_code}`;
      }).join(', ');

      alert(`Cannot forward selection. Please fill and submit the Confidential Report (CR) first for: ${names}`);
      return;
    }

    if (!window.confirm(`Are you sure you want to forward ${selectedAppraisals.length} selected appraisal(s) to the Principal? This will make them read-only.`)) {
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post('/api360/bulk-forward', selectedAppraisals);
      if (res.data?.success) {
        setToast({ msg: `Successfully forwarded ${selectedAppraisals.length} appraisal(s) to the Principal.`, type: 'success' });
        setSelectedAppraisals([]);
        await loadHODDashboard();
      }
    } catch (e: any) {
      setToast({ msg: "Forwarding failed: " + (e.response?.data?.detail || "Error"), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleToolbarFillCredit = () => {
    if (selectedAppraisals.length !== 1) {
      alert("Please select one faculty to fill Confidential Report.");
      setToast({ msg: "Please select one faculty to fill Confidential Report.", type: 'error' });
      return;
    }
    const targetId = selectedAppraisals[0];
    const targetItem = departmentList.find(x => x.api_id === targetId);
    if (targetItem) {
      handleOpenConfidentialAssessment(targetItem);
    }
  };

  const calculatePrintTeachingScore = (target: any) => {
    const cat1i = (target.cat1i || []).filter((x: any) => x.sno !== -999);
    if (cat1i.length === 0) return 0;
    let totalScore = 0;
    cat1i.forEach((row: any) => {
      const scheduled = Number(row.nsc) || 0;
      const held = (Number(row.nahcof) || 0) + (Number(row.nahcon) || 0);
      if (scheduled > 0) {
        totalScore += Math.min(25, (held / scheduled) * 25);
      }
    });
    return Math.min(25, Math.round((totalScore / cat1i.length) * 10) / 10);
  };

  const calculatePrintFeedbackScore = (target: any) => {
    const cat1ii = target.cat1ii || [];
    if (cat1ii.length === 0) return 0;
    let totalScore = 0;
    cat1ii.forEach((row: any) => { totalScore += Number(row.asf) || 0; });
    return Math.min(25, totalScore);
  };

  const calculatePrintDeptScore = (target: any) => Math.min(20, (target.cat1iii || []).length * 5);

  const calculatePrintInstScore = (target: any) => {
    let total = 0;
    (target.cat1iv || []).forEach((row: any) => { total += Number(row.pe) || 0; });
    return Math.min(10, total);
  };

  const calculatePrintSocietyScore = (target: any) => {
    let total = 0;
    (target.cat1v || []).forEach((row: any) => { total += Number(row.pe) || 0; });
    return Math.min(10, total);
  };

  const calculatePrintAnnexureITotal = (target: any) => {
    return Math.round((
      calculatePrintTeachingScore(target) +
      calculatePrintFeedbackScore(target) +
      calculatePrintDeptScore(target) +
      calculatePrintInstScore(target) +
      calculatePrintSocietyScore(target)
    ) * 10) / 10;
  };

  const calculatePrintAnnexureIITotal = (target: any) => {
    let sum = 0;
    (target.cat2 || []).forEach((c: any) => { sum += Number(c.score) || 0; });
    return sum;
  };

  const calculatePrintAnnexureIIITotal = (target: any) => {
    let sum = 0;
    (target.cat3 || []).forEach((c: any) => { sum += Number(c.score) || 0; });
    return sum;
  };

  const handlePrintCR = async (item: any) => {
    setLoading(true);
    try {
      const freshDetail = await loadRecordDetails(item.api_id);
      if (freshDetail) {
        setPrintTarget(freshDetail);
        setPrintType('cr');
      }
    } catch (e) {
      setToast({ msg: "Loading details failed", type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handlePrintAPI = async (item: any) => {
    setLoading(true);
    try {
      const freshDetail = await loadRecordDetails(item.api_id);
      if (freshDetail) {
        setPrintTarget(freshDetail);
        setPrintType('api');
      }
    } catch (e) {
      setToast({ msg: "Loading details failed", type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handlePrintSummary = async (item: any) => {
    setLoading(true);
    try {
      const freshDetail = await loadRecordDetails(item.api_id);
      if (freshDetail) {
        setPrintTarget(freshDetail);
        setPrintType('summary');
      }
    } catch (e) {
      setToast({ msg: "Loading details failed", type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Primary data form
  const [form, setForm] = useState(emptyForm());
  const isSelf = !form.faculty_computer_code || Number(form.faculty_computer_code) === Number(user?.computer_code);
  const canEditSelfAppraisal = !form.hod_approval && isSelf && ['Draft', 'HOD Rejected', 'Principal Rejected'].includes(appraisalStatus);

  // Accordion collapsed state
  const [accordions, setAccordions] = useState({
    annexure1: true,
    annexure2: true,
    annexure3: true
  });

  // Dynamic Designation resolver
  const getDesignationName = (designationId: number | null) => {
    if (!designationId) return 'Not assigned';
    const match = designations.find(d => d.id === designationId);
    return match ? match.designation : 'Not assigned';
  };

  const getDepartmentName = (deptId: number | null) => {
    if (!deptId) return 'Not assigned';
    const match = departments.find(d => d.id === deptId);
    return match ? match.name : 'Not assigned';
  };

  const calculateExperience = (dateJoinStr: string) => {
    if (!dateJoinStr) return 'Not available';
    const joinDate = new Date(dateJoinStr);
    const now = new Date();
    let years = now.getFullYear() - joinDate.getFullYear();
    let months = now.getMonth() - joinDate.getMonth();
    let days = now.getDate() - joinDate.getDate();

    if (days < 0) {
      months--;
      const lastMonth = new Date(now.getFullYear(), now.getMonth(), 0);
      days += lastMonth.getDate();
    }
    if (months < 0) {
      years--;
      months += 12;
    }
    return `${years} Years ${months} Months ${days} days`;
  };

  // Printing trigger hook
  useEffect(() => {
    if (printType !== 'none') {
      const timer = setTimeout(() => {
        window.print();
        setPrintType('none');
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [printType]);

  // Initialize and load
  useEffect(() => {
    const initPage = async () => {
      setLoading(true);
      try {
        const [sessionRes, currentSessionRes] = await Promise.all([
          api.get('/academic-sessions/dropdown'),
          api.get('/academic-sessions/current')
        ]);
        if (sessionRes.data?.success) {
          setSessionsDropdown(sessionRes.data.data.sessions || []);
        }

        let sessionToUse = null;
        if (currentSessionRes.data?.success && currentSessionRes.data.data) {
          setActiveSession(currentSessionRes.data.data);
          sessionToUse = currentSessionRes.data.data;
        }

        // Set HOD flag
        const isUserHOD = role === 'HOD';
        setIsHOD(isUserHOD);

        // Routing checks for review and principal views
        const queryParams = new URLSearchParams(location.search);
        const isReviewView = queryParams.get('view') === 'review';
        const isStaffReviewView = queryParams.get('view') === 'staff-review';
        const isPrincipalView = queryParams.get('view') === 'principal';
        const queryId = queryParams.get('id');

        if (queryId) {
          setViewMode('teacher');
          await loadRecordDetails(Number(queryId));
        } else if (isReviewView && (isUserHOD || isAdmin())) {
          setSelectedRecordId(null);
          setViewMode('review');
          await loadHODDashboard();
        } else if (isStaffReviewView && (isUserHOD || isAdmin())) {
          setSelectedRecordId(null);
          setViewMode('staff-review');
          await loadHODDashboard();
        } else if (isPrincipalView && (role === 'Principal' || isAdmin())) {
          setSelectedRecordId(null);
          setViewMode('principal');
          await loadPrincipalDashboard();
        } else {
          setViewMode('teacher');
        }

        // Fetch designations and departments for Admin / HOD / Principal
        if (isAdmin() || role === 'HOD' || role === 'Principal') {
          try {
            const [designationsRes, departmentsRes] = await Promise.all([
              api.get('/staff/designations'),
              api.get('/academic-programs/dropdown/departments')
            ]);
            if (designationsRes.data?.success) {
              setDesignations(designationsRes.data.data || []);
            }
            if (departmentsRes.data?.success) {
              setDepartments(departmentsRes.data.data?.departments || []);
            }
          } catch (e) {
            console.error("Failed to load designations or departments", e);
          }
        }

        // Auto-load for Staff / Faculty
        if (isStaff() && role !== 'Principal' && !isReviewView && !isPrincipalView) {
          setSelectedFacultyCode(user?.computer_code.toString() || '');
          if (sessionToUse) {
            setSelectedSessionId(sessionToUse.id.toString());
          }
          setFacultyName(user?.name || '');

          // Load or initialize evaluation record
          if (sessionToUse && user?.computer_code) {
            await loadOrCreateRecord(user.computer_code, sessionToUse.id);
          }
        }
      } catch (err) {
        console.error("Failed page initialization", err);
      } finally {
        setLoading(false);
      }
    };
    initPage();
  }, [role, user?.computer_code, location.search]);

  // Load HOD dashboard department list
  const loadHODDashboard = async () => {
    try {
      const res = await api.get(`/api360/?_t=${Date.now()}`);
      if (res.data?.success) {
        const records = res.data.data.items || [];
        setDepartmentList(records);

        records.forEach((r: any) => {
          preloadStaffDetails(r.faculty_computer_code);
        });
      }
    } catch (e) {
      console.error("Failed to load department reviews", e);
    }
  };

  // Load Principal dashboard list
  const loadPrincipalDashboard = async () => {
    try {
      const res = await api.get(`/api360/?_t=${Date.now()}`);
      if (res.data?.success) {
        const records = res.data.data.items || [];
        setPrincipalList(records);

        records.forEach((r: any) => {
          preloadStaffDetails(r.faculty_computer_code);
        });
      }
    } catch (e) {
      console.error("Failed to load Principal dashboard reviews", e);
    }
  };

  // Helper to load staff details
  const preloadStaffDetails = async (computerCode: number) => {
    if (staffCache[computerCode]) return;
    try {
      const res = await api.get('/staff/', { params: { search: computerCode } });
      if (res.data?.success && res.data.data.items?.length > 0) {
        const matched = res.data.data.items.find((item: any) => item.computer_code === computerCode);
        if (matched) {
          const detailRes = await api.get(`/staff/${matched.id}`);
          if (detailRes.data?.success) {
            setStaffCache(prev => ({
              ...prev,
              [computerCode]: detailRes.data.data
            }));
          }
        }
      }
    } catch (e) {
      console.error("Failed staff details preloading", e);
    }
  };

  // Load record or create draft record
  const loadOrCreateRecord = async (computerCode: string | number, sessionId: number) => {
    try {
      const searchRes = await api.get('/api360/', {
        params: { faculty_computer_code: Number(computerCode), academic_session: sessionId }
      });
      if (searchRes.data?.success && searchRes.data.data.items?.length > 0) {
        const found = searchRes.data.data.items[0];
        await loadRecordDetails(found.api_id);
      } else {
        // Initialize blank draft record in database
        const payload = {
          faculty_computer_code: Number(computerCode),
          academic_session: sessionId,
          submited: false,
          hod_approval: false,
          cr: { cr1: 10, cr2: 10, cr3: 10, cr4: 10, cr5: 10, cr6: 10, cr7: 10, cr8: 10, cr9: 10, cr10: 10 },
          cat1i: [], cat1ii: [], cat1iii: [], cat1iv: [], cat1v: [],
          cat2: cat2Categories.filter(c => !c.headerOnly).map(c => ({ sno: c.key, score: '0' })),
          cat3: cat3Categories.map(c => ({ sno: c.key, score: '0' }))
        };
        const createRes = await api.post('/api360/', payload);
        if (createRes.data?.success) {
          await loadRecordDetails(createRes.data.data.api_id);
        }
      }
    } catch (e: any) {
      setToast({ msg: "Initialization failed: " + parseError(e), type: 'error' });
    }
  };

  // Load record details
  const loadRecordDetails = async (id: number) => {
    setSelectedRecordId(id);
    try {
      const res = await api.get(`/api360/${id}?_t=${Date.now()}`);
      if (res.data?.success) {
        const detail = res.data.data;

        // Map category 2 and 3 list values back to fixed categories
        const mappedCat2 = cat2Categories.map(c => {
          const found = detail.cat2?.find((x: any) => String(x.sno) === c.key);
          return { sno: c.key, score: found ? String(found.score) : '0' };
        });
        const mappedCat3 = cat3Categories.map(c => {
          const found = detail.cat3?.find((x: any) => String(x.sno) === c.key);
          return { sno: c.key, score: found ? String(found.score) : '0' };
        });

        // 1. Extract metadata JSON row from cat1i
        const metadataRow = detail.cat1i?.find((x: any) => x.sno === -999);
        let statusValue: any = 'Draft';
        let remarksValue = '';
        let submittedAtValue = '';
        let approvedAtValue = '';
        let lastModifiedValue = '';

        if (metadataRow && metadataRow.ccnc) {
          try {
            const meta = JSON.parse(metadataRow.ccnc);
            statusValue = meta.status || 'Draft';
            remarksValue = meta.hod_remarks || '';
            submittedAtValue = meta.submitted_at || '';
            approvedAtValue = meta.approved_at || '';
            lastModifiedValue = meta.last_modified || '';
          } catch (e) {
            console.error("Failed to parse appraisal metadata", e);
          }
        } else {
          // Fallback legacy mappings
          if (detail.hod_approval) statusValue = 'Approved';
          else if (detail.submited) statusValue = 'Submitted';
        }

        setAppraisalStatus(statusValue);
        setHodRemarks(remarksValue);
        setSubmittedAt(submittedAtValue);
        setApprovedAt(approvedAtValue);
        setLastModified(lastModifiedValue);
        setLoadedConfidential(detail.confidential || null);

        // Filter out metadata row from visual category 1i lists
        const cleanCat1i = (detail.cat1i || []).filter((x: any) => x.sno !== -999);

        // Set faculty details if Admin / HOD / Principal is looking up another faculty code
        if (isAdmin() || isHOD || role === 'Principal') {
          try {
            const staffRes = await api.get('/staff/', { params: { search: detail.faculty_computer_code.toString() } });
            if (staffRes.data?.success && staffRes.data.data.items?.length > 0) {
              const matched = staffRes.data.data.items.find((item: any) => item.computer_code === detail.faculty_computer_code);
              if (matched) {
                setFacultyName(`${matched.title || ''} ${matched.first_name} ${matched.last_name}`);
                const detailRes = await api.get(`/staff/${matched.id}`);
                if (detailRes.data?.success) {
                  setStaffProfile(detailRes.data.data);
                }
              }
            }
          } catch (err) {
            console.error("Admin metadata lookup failed", err);
          }
        }

        setForm({
          faculty_computer_code: detail.faculty_computer_code.toString(),
          academic_session: detail.academic_session.toString(),
          submited: detail.submited,
          hod_approval: detail.hod_approval,
          cr: detail.cr || { cr1: 10, cr2: 10, cr3: 10, cr4: 10, cr5: 10, cr6: 10, cr7: 10, cr8: 10, cr9: 10, cr10: 10 },
          cat1i: cleanCat1i,
          cat1ii: detail.cat1ii || [],
          cat1iii: detail.cat1iii || [],
          cat1iv: detail.cat1iv || [],
          cat1v: detail.cat1v || [],
          cat2: mappedCat2,
          cat3: mappedCat3
        });
        return detail;
      }
    } catch (err: any) {
      setToast({ msg: "Failed to load record details: " + parseError(err), type: 'error' });
    }
  };

  // Admin select trigger
  const handleAdminLoad = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFacultyCode || !selectedSessionId) {
      setToast({ msg: "Please supply both Faculty Computer Code and Academic Session", type: 'error' });
      return;
    }
    setLoading(true);
    await loadOrCreateRecord(selectedFacultyCode, Number(selectedSessionId));
    setLoading(false);
  };

  // Subform Save/Submit back to database
  const handleSaveSubForm = async (updatedFields: Partial<typeof form>) => {
    if (!selectedRecordId) return;
    setSubmitting(true);

    const merged = {
      ...form,
      ...updatedFields,
      faculty_computer_code: Number(form.faculty_computer_code),
      academic_session: Number(form.academic_session)
    };

    // Serialize current state values inside cat1i metadata row
    const nowStr = new Date().toISOString();
    const metaPayload = {
      status: appraisalStatus,
      hod_remarks: hodRemarks,
      submitted_at: submittedAt,
      approved_at: approvedAt,
      last_modified: nowStr
    };
    const metadataRow = {
      sno: -999,
      sas: 'METADATA',
      ccnc: JSON.stringify(metaPayload),
      nsc: 0, nahcof: 0, nahcon: 0
    };
    const mergedCat1i = [...merged.cat1i, metadataRow];

    // Strip out categories headers from cat2 database payload
    const payload = {
      ...merged,
      cat1i: mergedCat1i,
      cat2: merged.cat2.filter(c => {
        const matchingCat = cat2Categories.find(x => x.key === c.sno);
        return matchingCat && !matchingCat.headerOnly;
      }).map(x => ({ sno: String(x.sno), score: String(x.score) })),
      cat3: merged.cat3.map(x => ({ sno: String(x.sno), score: String(x.score) }))
    };

    try {
      const res = await api.put(`/api360/${selectedRecordId}`, payload);
      if (res.data?.success) {
        setToast({ msg: "Progress saved successfully", type: 'success' });
        setForm(prev => ({ ...prev, ...updatedFields }));
        setLastModified(nowStr);
        setActiveSubForm('none');
        await loadRecordDetails(selectedRecordId);
      }
    } catch (e: any) {
      setToast({ msg: "Save failed: " + parseError(e), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  // Submit Actions
  const handleTeacherSubmitAction = async (action: 'draft' | 'submit') => {
    if (!selectedRecordId) return;
    const isSubmittingFinal = action === 'submit';

    if (isSubmittingFinal) {
      if (!form.cat1i || form.cat1i.filter(x => x.sno !== -999).length === 0) {
        setToast({ msg: "Submission failed: Annexure I (Teaching Process) must have at least one course detail entry.", type: 'error' });
        return;
      }
      if (!window.confirm("Are you sure you want to submit?")) {
        return;
      }
    }

    setSubmitting(true);
    const nowStr = new Date().toISOString();

    // HOD submits automatically move to "Forwarded to Principal". Normal teachers move to "Under HOD Review".
    const newStatus = isSubmittingFinal
      ? (role === 'HOD' ? 'Forwarded to Principal' : 'Under HOD Review')
      : 'Draft';
    const newSubmittedAt = isSubmittingFinal ? nowStr : submittedAt;

    const metaPayload = {
      status: newStatus,
      hod_remarks: hodRemarks,
      submitted_at: newSubmittedAt,
      approved_at: approvedAt,
      last_modified: nowStr
    };
    const metadataRow = {
      sno: -999,
      sas: 'METADATA',
      ccnc: JSON.stringify(metaPayload),
      nsc: 0, nahcof: 0, nahcon: 0
    };

    const payload = {
      ...form,
      submited: isSubmittingFinal,
      faculty_computer_code: Number(form.faculty_computer_code),
      academic_session: Number(form.academic_session),
      cat1i: [...form.cat1i, metadataRow],
      cat2: form.cat2.filter(c => {
        const matchingCat = cat2Categories.find(x => x.key === c.sno);
        return matchingCat && !matchingCat.headerOnly;
      }).map(x => ({ sno: String(x.sno), score: String(x.score) })),
      cat3: form.cat3.map(x => ({ sno: String(x.sno), score: String(x.score) }))
    };

    try {
      const res = await api.put(`/api360/${selectedRecordId}`, payload);
      if (res.data?.success) {
        setToast({ msg: isSubmittingFinal ? "Final Appraisal submitted successfully." : "Appraisal progress saved as Draft", type: 'success' });
        setAppraisalStatus(newStatus);
        setSubmittedAt(newSubmittedAt);
        setLastModified(nowStr);
        await loadRecordDetails(selectedRecordId);
      }
    } catch (e: any) {
      setToast({ msg: "Action failed: " + parseError(e), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  // HOD Decision Handling
  const handleHODDecision = async (decision: 'Approved' | 'Rejected' | 'Needs Correction') => {
    if (!selectedRecordId) return;
    if (!window.confirm(`Are you sure you want to mark this appraisal as "${decision}"?`)) return;

    setSubmitting(true);
    const nowStr = new Date().toISOString();

    let newStatus = 'Under HOD Review';
    let isSubmited = true;
    let isApproved = false;

    if (decision === 'Approved') {
      newStatus = 'Forwarded to Principal';
      isSubmited = true;
      isApproved = false; // principal does final approval
    } else if (decision === 'Rejected') {
      newStatus = 'HOD Rejected';
      isSubmited = false;
      isApproved = false;
    } else if (decision === 'Needs Correction') {
      newStatus = 'Draft';
      isSubmited = false;
      isApproved = false;
    }

    const metaPayload = {
      status: newStatus,
      hod_remarks: hodRemarks,
      submitted_at: submittedAt,
      approved_at: approvedAt,
      last_modified: nowStr
    };
    const metadataRow = {
      sno: -999,
      sas: 'METADATA',
      ccnc: JSON.stringify(metaPayload),
      nsc: 0, nahcof: 0, nahcon: 0
    };

    const payload = {
      ...form,
      submited: isSubmited,
      hod_approval: isApproved,
      faculty_computer_code: Number(form.faculty_computer_code),
      academic_session: Number(form.academic_session),
      cat1i: [...form.cat1i, metadataRow],
      cat2: form.cat2.filter(c => {
        const matchingCat = cat2Categories.find(x => x.key === c.sno);
        return matchingCat && !matchingCat.headerOnly;
      }).map(x => ({ sno: String(x.sno), score: String(x.score) })),
      cat3: form.cat3.map(x => ({ sno: String(x.sno), score: String(x.score) }))
    };

    try {
      const res = await api.put(`/api360/${selectedRecordId}`, payload);
      if (res.data?.success) {
        setToast({ msg: `Appraisal status set to ${newStatus} successfully!`, type: 'success' });
        setAppraisalStatus(newStatus as any);
        setLastModified(nowStr);
        navigate('/dashboard/staff/feedback?view=review');
      }
    } catch (e: any) {
      setToast({ msg: "Action failed: " + (e.response?.data?.detail || "Network Error"), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  // Principal Decision Handling
  const handlePrincipalDecision = async (decision: 'Approved' | 'Rejected' | 'Needs Correction') => {
    if (!selectedRecordId) return;
    if (!window.confirm(`Are you sure you want to mark this appraisal as "${decision}"?`)) return;

    setSubmitting(true);
    const nowStr = new Date().toISOString();

    let newStatus = 'Principal Approved';
    let isApproved = false;
    let isSubmitted = true;

    if (decision === 'Approved') {
      newStatus = 'Principal Approved';
      isApproved = true;
      isSubmitted = true;
    } else if (decision === 'Rejected') {
      newStatus = 'Principal Rejected';
      isApproved = false;
      isSubmitted = false;
    } else if (decision === 'Needs Correction') {
      newStatus = 'Draft';
      isApproved = false;
      isSubmitted = false;
    }

    const metaPayload = {
      status: newStatus,
      hod_remarks: hodRemarks, // store principal remarks in same column
      submitted_at: submittedAt,
      approved_at: decision === 'Approved' ? nowStr : approvedAt,
      last_modified: nowStr
    };
    const metadataRow = {
      sno: -999,
      sas: 'METADATA',
      ccnc: JSON.stringify(metaPayload),
      nsc: 0, nahcof: 0, nahcon: 0
    };

    const payload = {
      ...form,
      submited: isSubmitted,
      hod_approval: isApproved,
      faculty_computer_code: Number(form.faculty_computer_code),
      academic_session: Number(form.academic_session),
      cat1i: [...form.cat1i, metadataRow],
      cat2: form.cat2.filter(c => {
        const matchingCat = cat2Categories.find(x => x.key === c.sno);
        return matchingCat && !matchingCat.headerOnly;
      }).map(x => ({ sno: String(x.sno), score: String(x.score) })),
      cat3: form.cat3.map(x => ({ sno: String(x.sno), score: String(x.score) }))
    };

    try {
      const res = await api.put(`/api360/${selectedRecordId}`, payload);
      if (res.data?.success) {
        setToast({ msg: `Appraisal status set to ${newStatus} successfully!`, type: 'success' });
        setAppraisalStatus(newStatus as any);
        if (decision === 'Approved') setApprovedAt(nowStr);
        setLastModified(nowStr);
        navigate('/dashboard/staff/feedback?view=principal');
      }
    } catch (e: any) {
      setToast({ msg: "Action failed: " + (e.response?.data?.detail || "Network Error"), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  // Score calculations
  const calculateTeachingScore = () => {
    if (form.cat1i.length === 0) return 0;
    let totalScore = 0;
    form.cat1i.forEach(row => {
      const scheduled = Number(row.nsc) || 0;
      const held = (Number(row.nahcof) || 0) + (Number(row.nahcon) || 0);
      if (scheduled > 0) {
        totalScore += Math.min(25, (held / scheduled) * 25);
      }
    });
    return Math.min(25, Math.round((totalScore / form.cat1i.length) * 10) / 10);
  };

  const calculateFeedbackScore = () => {
    if (form.cat1ii.length === 0) return 0;
    let totalScore = 0;
    form.cat1ii.forEach(row => { totalScore += Number(row.asf) || 0; });
    return Math.min(25, totalScore);
  };

  const calculateDeptScore = () => Math.min(20, form.cat1iii.length * 5);

  const calculateInstScore = () => {
    let total = 0;
    form.cat1iv.forEach(row => { total += Number(row.pe) || 0; });
    return Math.min(10, total);
  };

  const calculateSocietyScore = () => {
    let total = 0;
    form.cat1v.forEach(row => { total += Number(row.pe) || 0; });
    return Math.min(10, total);
  };

  const calculateAnnexureITotal = () => {
    return Math.round((
      calculateTeachingScore() +
      calculateFeedbackScore() +
      calculateDeptScore() +
      calculateInstScore() +
      calculateSocietyScore()
    ) * 10) / 10;
  };

  const calculateAnnexureIITotal = () => {
    let sum = 0;
    form.cat2.forEach(c => { sum += Number(c.score) || 0; });
    return sum;
  };

  const calculateAnnexureIIITotal = () => {
    let sum = 0;
    form.cat3.forEach(c => { sum += Number(c.score) || 0; });
    return sum;
  };

  // Completion percentage
  const getCompletionPercentage = () => {
    let completedSections = 0;
    if (form.cat1i.length > 0) completedSections += 1;
    if (form.cat1ii.length > 0) completedSections += 1;
    if (form.cat1iii.length > 0) completedSections += 1;
    if (form.cat1iv.length > 0) completedSections += 1;
    if (form.cat1v.length > 0) completedSections += 1;
    if (form.cat2.some(c => Number(c.score) > 0)) completedSections += 1;
    if (form.cat3.some(c => Number(c.score) > 0)) completedSections += 1;

    return Math.round((completedSections / 7) * 100);
  };

  // Toggle accordions
  const toggleAccordion = (key: 'annexure1' | 'annexure2' | 'annexure3') => {
    setAccordions(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // Subform row manipulation
  const addCategoryRow = (category: 'cat1i' | 'cat1ii' | 'cat1iii' | 'cat1iv' | 'cat1v', subFormFields: any) => {
    const list = [...subFormFields];
    let newRow: any = { sno: list.length + 1 };

    const activeSessionId = Number(form.academic_session);
    const selectedSess = sessionsDropdown.find(s => s.id === activeSessionId);
    const defaultSas = selectedSess ? selectedSess.name : '';

    if (category === 'cat1i') {
      newRow = { ...newRow, sas: defaultSas, ccnc: '', nsc: 0, nahcof: 0, nahcon: 0 };
    } else if (category === 'cat1ii') {
      newRow = { ...newRow, sas: defaultSas, cnctp: '', asf: 0 };
    } else if (category === 'cat1iii') {
      newRow = { ...newRow, sas: defaultSas, activity: '', pe: '' };
    } else if (category === 'cat1iv') {
      newRow = { ...newRow, sas: defaultSas, activity: '', pe: 0 };
    } else if (category === 'cat1v') {
      newRow = { ...newRow, sas: defaultSas, activity: '', pe: 0 };
    }

    setForm(prev => ({
      ...prev,
      [category]: [...list, newRow]
    }));
  };

  const removeCategoryRow = (subFormFields: any[], index: number) => {
    const list = [...subFormFields];
    list.splice(index, 1);
    return list.map((item, idx) => ({ ...item, sno: idx + 1 }));
  };

  const handleSubFormFieldChange = (subFormFields: any[], index: number, field: string, value: any) => {
    const list = [...subFormFields];
    list[index] = { ...list[index], [field]: value };
    return list;
  };

  // Status badges
  const getStatusBadge = (statusStr: string) => {
    switch (statusStr) {
      case 'Principal Approved':
      case 'Approved':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200">🟢 Approved</span>;
      case 'Principal Rejected':
      case 'HOD Rejected':
      case 'Rejected':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-red-50 text-red-700 border border-red-200">🔴 Rejected</span>;
      case 'CR Draft':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-amber-50 text-amber-700 border border-amber-200">🟡 CR Draft</span>;
      case 'Submitted to HOD':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-orange-50 text-orange-700 border border-orange-200">🟠 Submitted to HOD</span>;
      case 'Under HOD Review':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-orange-50 text-orange-700 border border-orange-200">🟠 Under HOD Review</span>;
      case 'Forwarded to Principal':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-purple-50 text-purple-700 border border-purple-200">🟣 Forwarded to Principal</span>;
      case 'Confidential Report Submitted':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-teal-50 text-teal-700 border border-teal-200">🟢 Confidential Report Submitted</span>;
      case 'Submitted':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-blue-50 text-blue-700 border border-blue-200">🔵 Submitted</span>;
      default:
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-extrabold bg-amber-50 text-amber-700 border border-amber-200">🟡 Draft</span>;
    }
  };

  // Read-only tables
  const renderCat1iTableReadOnly = (list: any[]) => (
    <table className="w-full text-xs text-left border border-slate-100 rounded-lg overflow-hidden mt-3">
      <thead>
        <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-bold">
          <th className="px-4 py-2 w-16 text-center">S.No</th>
          <th className="px-4 py-2">Semester</th>
          <th className="px-4 py-2">Course Code / Name</th>
          <th className="px-4 py-2 text-center w-28">Scheduled</th>
          <th className="px-4 py-2 text-center w-28">Held (Offline)</th>
          <th className="px-4 py-2 text-center w-28">Held (Online)</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100 font-medium">
        {list.length === 0 ? (
          <tr><td colSpan={6} className="text-center py-4 text-slate-400">No Teaching Process added.</td></tr>
        ) : list.map((r, i) => (
          <tr key={i}>
            <td className="px-4 py-2 text-center">{i + 1}</td>
            <td className="px-4 py-2">{r.sas}</td>
            <td className="px-4 py-2">{r.ccnc}</td>
            <td className="px-4 py-2 text-center">{r.nsc}</td>
            <td className="px-4 py-2 text-center">{r.nahcof}</td>
            <td className="px-4 py-2 text-center">{r.nahcon}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  const renderCat1iiTableReadOnly = (list: any[]) => (
    <table className="w-full text-xs text-left border border-slate-100 rounded-lg overflow-hidden mt-3">
      <thead>
        <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-bold">
          <th className="px-4 py-2 w-16 text-center">S.No</th>
          <th className="px-4 py-2">Semester</th>
          <th className="px-4 py-2">Course Name / Project Details</th>
          <th className="px-4 py-2 text-center w-36">Feedback Score</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100 font-medium">
        {list.length === 0 ? (
          <tr><td colSpan={4} className="text-center py-4 text-slate-400">No Student Feedback added.</td></tr>
        ) : list.map((r, i) => (
          <tr key={i}>
            <td className="px-4 py-2 text-center">{i + 1}</td>
            <td className="px-4 py-2">{r.sas}</td>
            <td className="px-4 py-2">{r.cnctp}</td>
            <td className="px-4 py-2 text-center font-bold text-indigo-600">{r.asf}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  const renderGenericCat1Table = (list: any[]) => (
    <table className="w-full text-xs text-left border border-slate-100 rounded-lg overflow-hidden mt-3">
      <thead>
        <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-bold">
          <th className="px-4 py-2 w-16 text-center">S.No</th>
          <th className="px-4 py-2 w-48">Semester / Session</th>
          <th className="px-4 py-2">Activity Description</th>
          <th className="px-4 py-2 text-center w-36">Score / Extent</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100 font-medium">
        {list.length === 0 ? (
          <tr><td colSpan={4} className="text-center py-4 text-slate-400">No records added yet.</td></tr>
        ) : list.map((r, i) => (
          <tr key={i}>
            <td className="px-4 py-2 text-center">{i + 1}</td>
            <td className="px-4 py-2">{r.sas}</td>
            <td className="px-4 py-2">{r.activity}</td>
            <td className="px-4 py-2 text-center">{r.pe}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  const renderActiveCat2Table = () => {
    const active = form.cat2.filter(c => Number(c.score) > 0);
    return (
      <table className="w-full text-xs text-left border border-slate-100 rounded-lg overflow-hidden mt-3">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-bold">
            <th className="px-4 py-2 w-20 text-center">SNo/Key</th>
            <th className="px-4 py-2">Research Particulars Description</th>
            <th className="px-4 py-2 text-center w-36">Self Assessment</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 font-medium">
          {active.length === 0 ? (
            <tr><td colSpan={3} className="text-center py-4 text-slate-400">No records found.</td></tr>
          ) : active.map((r, i) => {
            const label = cat2Categories.find(c => c.key === r.sno)?.particulars || 'Research Publication';
            return (
              <tr key={i}>
                <td className="px-4 py-2 text-center font-bold text-slate-500">{r.sno}</td>
                <td className="px-4 py-2 text-slate-600">{label}</td>
                <td className="px-4 py-2 text-center font-bold text-emerald-600">{r.score}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  };

  const renderActiveCat3Table = () => {
    const active = form.cat3.filter(c => Number(c.score) > 0);
    return (
      <table className="w-full text-xs text-left border border-slate-100 rounded-lg overflow-hidden mt-3">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-bold">
            <th className="px-4 py-2 w-20 text-center">SNo</th>
            <th className="px-4 py-2">Appraisal Criteria Description</th>
            <th className="px-4 py-2 text-center w-36">Self Assessment</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 font-medium">
          {active.length === 0 ? (
            <tr><td colSpan={3} className="text-center py-4 text-slate-400">No records found.</td></tr>
          ) : active.map((r, i) => {
            const label = cat3Categories.find(c => c.key === r.sno)?.particulars || 'Criteria Record';
            return (
              <tr key={i}>
                <td className="px-4 py-2 text-center font-bold text-slate-500">{r.sno}</td>
                <td className="px-4 py-2 text-slate-600">{label}</td>
                <td className="px-4 py-2 text-center font-bold text-indigo-600">{r.score}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  };

  const getFilteredDeptList = () => {
    return departmentList.filter(item => {
      const metaRow = item.cat1i?.find((x: any) => x.sno === -999);
      let rowStatus = 'Draft';
      if (metaRow && metaRow.ccnc) {
        try {
          rowStatus = JSON.parse(metaRow.ccnc).status || 'Draft';
        } catch (e) { }
      } else {
        if (item.hod_approval) rowStatus = 'Approved';
        else if (item.submited) rowStatus = 'Submitted';
      }
      return rowStatus !== 'Draft' && rowStatus !== 'HOD Rejected';
    });
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">

      {/* Dynamic CSS styles for printable page overlay */}
      <style>{`
        @media print {
          /* Reset parent layout styles that constrain height or overflow */
          html, body, #root, #root > div, main, main > div, .app-container, .main-layout {
            height: auto !important;
            min-height: 0 !important;
            overflow: visible !important;
            position: static !important;
            display: block !important;
            padding: 0 !important;
            margin: 0 !important;
            transform: none !important;
            zoom: normal !important;
            max-height: none !important;
            max-width: none !important;
          }

          /* Hide all screen-only elements */
          body * {
            visibility: hidden !important;
          }

          /* Show the printable area and its children */
          #printable-area, #printable-area * {
            visibility: visible !important;
          }

          /* Printable area settings */
          #printable-area {
            position: static !important;
            width: 100% !important;
            background: white !important;
            color: black !important;
            height: auto !important;
            display: block !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: visible !important;
          }

          #printable-area * {
            overflow: visible !important;
            max-height: none !important;
          }

          .print-hide {
            display: none !important;
          }

          /* Custom page break rules */
          .page-break {
            page-break-before: always !important;
            break-before: page !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            display: block !important;
            clear: both !important;
          }

          /* Tables formatting for print */
          table {
            width: 100% !important;
            border-collapse: collapse !important;
            page-break-inside: auto !important;
            overflow: visible !important;
          }

          tr {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            overflow: visible !important;
          }

          th, td {
            overflow: visible !important;
            white-space: normal !important;
            word-wrap: break-word !important;
            word-break: break-word !important;
          }

          thead {
            display: table-header-group !important;
          }

          tfoot {
            display: table-footer-group !important;
          }

          /* Page size and margins */
          @page {
            size: A4;
            margin: 20mm 15mm 20mm 15mm;
          }
        }
      `}</style>

      {/* ─── PRINT LOGO PANEL (HIDDEN IN SCREEN VIEW) ────────────────────── */}
      <div id="print-header" className="hidden print:flex flex-col items-center text-center pb-6 border-b-2 border-slate-300">
        <h1 className="text-2xl font-bold uppercase tracking-wider text-slate-800">IPS Academy</h1>
        <h2 className="text-sm font-semibold uppercase text-slate-500">Institute of Engineering & Science, Indore (M.P.)</h2>
        <h3 className="text-md font-bold mt-2 text-indigo-700">360 Degree Feedback Scorecard</h3>

        <div className="grid grid-cols-2 gap-x-12 gap-y-1 text-left text-xs mt-4 w-full max-w-3xl border border-slate-200 p-4 rounded-lg bg-slate-50">
          <div><strong>Faculty Name:</strong> {facultyName}</div>
          <div><strong>Computer Code:</strong> {form.faculty_computer_code}</div>
          <div><strong>Department:</strong> {isStaff() ? (user?.department || 'IT') : 'Verified Department'}</div>
          <div><strong>Designation:</strong> {isStaff() ? (user?.role || 'Faculty') : getDesignationName(staffProfile?.details?.designation_id)}</div>
          <div><strong>Academic Session:</strong> {sessionsDropdown.find(s => s.id === Number(form.academic_session))?.name || 'Current'}</div>
          <div><strong>Appraisal Status:</strong> {appraisalStatus}</div>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-32 space-y-4">
          <Loader2 className="w-12 h-12 animate-spin text-indigo-600" />
          <p className="text-slate-500 text-sm font-medium">Loading appraisal details...</p>
        </div>
      ) : activeSubForm !== 'none' ? (

        /* ─── DETAILED SUB-FORM CRUD VIEWS ──────────────────────────── */
        <div className="space-y-6 print:hidden">

          {/* Annexure I - Table A: Teaching Process Subform */}
          {activeSubForm === 'cat1i' && (
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
              <div className="flex justify-between items-center border-b pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Forms</span>
                  <h3 className="text-lg font-bold text-slate-800">Annexure - I (A. Teaching Process)</h3>
                </div>
                <button
                  onClick={() => addCategoryRow('cat1i', form.cat1i)}
                  type="button"
                  className="px-4 py-2 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-xl text-xs font-bold transition-all flex items-center gap-1"
                >
                  <Plus size={14} /> Add Row
                </button>
              </div>

              <div className="overflow-x-auto border border-slate-100 rounded-xl">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100">
                      <th className="px-4 py-3 w-16 text-center">S.No</th>
                      <th className="px-4 py-3 w-40">Semester</th>
                      <th className="px-4 py-3">Course Code / Name</th>
                      <th className="px-4 py-3 w-32">Classes Scheduled</th>
                      <th className="px-4 py-3 w-32">Held (Offline)</th>
                      <th className="px-4 py-3 w-32">Held (Online)</th>
                      <th className="px-4 py-3 text-right w-16">Remove</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {form.cat1i.map((row, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-2 text-center font-bold text-slate-400">#{row.sno}</td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.sas || ''}
                            onChange={(e) => setForm({ ...form, cat1i: handleSubFormFieldChange(form.cat1i, idx, 'sas', e.target.value) })}
                            placeholder="e.g. III Sem"
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.ccnc || ''}
                            onChange={(e) => setForm({ ...form, cat1i: handleSubFormFieldChange(form.cat1i, idx, 'ccnc', e.target.value) })}
                            placeholder="e.g. Neural Networks"
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="number"
                            value={row.nsc || ''}
                            onChange={(e) => setForm({ ...form, cat1i: handleSubFormFieldChange(form.cat1i, idx, 'nsc', Number(e.target.value)) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="number"
                            value={row.nahcof || ''}
                            onChange={(e) => setForm({ ...form, cat1i: handleSubFormFieldChange(form.cat1i, idx, 'nahcof', Number(e.target.value)) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="number"
                            value={row.nahcon || ''}
                            onChange={(e) => setForm({ ...form, cat1i: handleSubFormFieldChange(form.cat1i, idx, 'nahcon', Number(e.target.value)) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => setForm({ ...form, cat1i: removeCategoryRow(form.cat1i, idx) })}
                            className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setActiveSubForm('none')}
                  className="px-5 py-2 border rounded-xl font-semibold text-slate-700 bg-white hover:bg-slate-50 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveSubForm({ cat1i: form.cat1i })}
                  className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-xs transition-all flex items-center gap-1.5"
                >
                  {submitting ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                  Save Teaching Scorecard
                </button>
              </div>
            </div>
          )}

          {/* Annexure I - Table B: Student Feedback Subform */}
          {activeSubForm === 'cat1ii' && (
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
              <div className="flex justify-between items-center border-b pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Forms</span>
                  <h3 className="text-lg font-bold text-slate-800">Annexure - I (B. Student's Feedback)</h3>
                </div>
                <button
                  onClick={() => addCategoryRow('cat1ii', form.cat1ii)}
                  type="button"
                  className="px-4 py-2 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-xl text-xs font-bold transition-all flex items-center gap-1"
                >
                  <Plus size={14} /> Add Row
                </button>
              </div>

              <div className="overflow-x-auto border border-slate-100 rounded-xl">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100">
                      <th className="px-4 py-3 w-16 text-center">S.No</th>
                      <th className="px-4 py-3 w-40">Semester</th>
                      <th className="px-4 py-3">Course Name / Project Details</th>
                      <th className="px-4 py-3 w-48">Classes Held</th>
                      <th className="px-4 py-3 text-right w-16">Remove</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {form.cat1ii.map((row, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-2 text-center font-bold text-slate-400">#{row.sno}</td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.sas || ''}
                            onChange={(e) => setForm({ ...form, cat1ii: handleSubFormFieldChange(form.cat1ii, idx, 'sas', e.target.value) })}
                            placeholder="e.g. V Sem"
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.cnctp || ''}
                            onChange={(e) => setForm({ ...form, cat1ii: handleSubFormFieldChange(form.cat1ii, idx, 'cnctp', e.target.value) })}
                            placeholder="e.g. Major Project Guidance"
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="number"
                            value={row.asf || ''}
                            onChange={(e) => setForm({ ...form, cat1ii: handleSubFormFieldChange(form.cat1ii, idx, 'asf', Number(e.target.value)) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => setForm({ ...form, cat1ii: removeCategoryRow(form.cat1ii, idx) })}
                            className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setActiveSubForm('none')}
                  className="px-5 py-2 border rounded-xl font-semibold text-slate-700 bg-white hover:bg-slate-50 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveSubForm({ cat1ii: form.cat1ii })}
                  className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-xs transition-all flex items-center gap-1.5"
                >
                  {submitting ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                  Save Feedback Scorecard
                </button>
              </div>
            </div>
          )}

          {/* Annexure I - Table C: Departmental Activities Subform */}
          {activeSubForm === 'cat1iii' && (
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
              <div className="flex justify-between items-center border-b pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Forms</span>
                  <h3 className="text-lg font-bold text-slate-800">Annexure - I (C. Departmental Activities)</h3>
                </div>
                <button
                  onClick={() => addCategoryRow('cat1iii', form.cat1iii)}
                  type="button"
                  className="px-4 py-2 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-xl text-xs font-bold transition-all flex items-center gap-1"
                >
                  <Plus size={14} /> Add Row
                </button>
              </div>

              <div className="overflow-x-auto border border-slate-100 rounded-xl">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100">
                      <th className="px-4 py-3 w-16 text-center">S.No</th>
                      <th className="px-4 py-3 w-40">Semester / Session</th>
                      <th className="px-4 py-3">Activity description</th>
                      <th className="px-4 py-3">Evidence reference</th>
                      <th className="px-4 py-3 text-right w-16">Remove</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {form.cat1iii.map((row, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-2 text-center font-bold text-slate-400">#{row.sno}</td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.sas || ''}
                            onChange={(e) => setForm({ ...form, cat1iii: handleSubFormFieldChange(form.cat1iii, idx, 'sas', e.target.value) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.activity || ''}
                            onChange={(e) => setForm({ ...form, cat1iii: handleSubFormFieldChange(form.cat1iii, idx, 'activity', e.target.value) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.pe || ''}
                            onChange={(e) => setForm({ ...form, cat1iii: handleSubFormFieldChange(form.cat1iii, idx, 'pe', e.target.value) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => setForm({ ...form, cat1iii: removeCategoryRow(form.cat1iii, idx) })}
                            className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setActiveSubForm('none')}
                  className="px-5 py-2 border rounded-xl font-semibold text-slate-700 bg-white hover:bg-slate-50 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveSubForm({ cat1iii: form.cat1iii })}
                  className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-xs transition-all flex items-center gap-1.5"
                >
                  {submitting ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                  Save Departmental Scorecard
                </button>
              </div>
            </div>
          )}

          {/* Annexure I - Table D: Institute Activity Subform */}
          {activeSubForm === 'cat1iv' && (
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
              <div className="flex justify-between items-center border-b pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Forms</span>
                  <h3 className="text-lg font-bold text-slate-800">Annexure - I (D. Institute Activity)</h3>
                </div>
                <button
                  onClick={() => addCategoryRow('cat1iv', form.cat1iv)}
                  type="button"
                  className="px-4 py-2 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-xl text-xs font-bold transition-all flex items-center gap-1"
                >
                  <Plus size={14} /> Add Row
                </button>
              </div>

              <div className="overflow-x-auto border border-slate-100 rounded-xl">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100">
                      <th className="px-4 py-3 w-16 text-center">S.No</th>
                      <th className="px-4 py-3 w-40">Semester</th>
                      <th className="px-4 py-3">Duty details</th>
                      <th className="px-4 py-3 w-48">Score / Extent</th>
                      <th className="px-4 py-3 text-right w-16">Remove</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {form.cat1iv.map((row, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-2 text-center font-bold text-slate-400">#{row.sno}</td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.sas || ''}
                            onChange={(e) => setForm({ ...form, cat1iv: handleSubFormFieldChange(form.cat1iv, idx, 'sas', e.target.value) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.activity || ''}
                            onChange={(e) => setForm({ ...form, cat1iv: handleSubFormFieldChange(form.cat1iv, idx, 'activity', e.target.value) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="number"
                            value={row.pe || ''}
                            onChange={(e) => setForm({ ...form, cat1iv: handleSubFormFieldChange(form.cat1iv, idx, 'pe', Number(e.target.value)) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => setForm({ ...form, cat1iv: removeCategoryRow(form.cat1iv, idx) })}
                            className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setActiveSubForm('none')}
                  className="px-5 py-2 border rounded-xl font-semibold text-slate-700 bg-white hover:bg-slate-50 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveSubForm({ cat1iv: form.cat1iv })}
                  className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-xs transition-all flex items-center gap-1.5"
                >
                  {submitting ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                  Save Institute Scorecard
                </button>
              </div>
            </div>
          )}

          {/* Annexure I - Table E: Contribution to Society Subform */}
          {activeSubForm === 'cat1v' && (
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
              <div className="flex justify-between items-center border-b pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Forms</span>
                  <h3 className="text-lg font-bold text-slate-800">Annexure - I (E. Contribution to the Society)</h3>
                </div>
                <button
                  onClick={() => addCategoryRow('cat1v', form.cat1v)}
                  type="button"
                  className="px-4 py-2 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-xl text-xs font-bold transition-all flex items-center gap-1"
                >
                  <Plus size={14} /> Add Row
                </button>
              </div>

              <div className="overflow-x-auto border border-slate-100 rounded-xl">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100">
                      <th className="px-4 py-3 w-16 text-center">S.No</th>
                      <th className="px-4 py-3 w-40">Semester</th>
                      <th className="px-4 py-3">Activity details</th>
                      <th className="px-4 py-3 w-48">Score / Extent</th>
                      <th className="px-4 py-3 text-right w-16">Remove</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {form.cat1v.map((row, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-2 text-center font-bold text-slate-400">#{row.sno}</td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.sas || ''}
                            onChange={(e) => setForm({ ...form, cat1v: handleSubFormFieldChange(form.cat1v, idx, 'sas', e.target.value) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="text"
                            value={row.activity || ''}
                            onChange={(e) => setForm({ ...form, cat1v: handleSubFormFieldChange(form.cat1v, idx, 'activity', e.target.value) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2">
                          <input
                            type="number"
                            value={row.pe || ''}
                            onChange={(e) => setForm({ ...form, cat1v: handleSubFormFieldChange(form.cat1v, idx, 'pe', Number(e.target.value)) })}
                            className="w-full px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="px-4 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => setForm({ ...form, cat1v: removeCategoryRow(form.cat1v, idx) })}
                            className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setActiveSubForm('none')}
                  className="px-5 py-2 border rounded-xl font-semibold text-slate-700 bg-white hover:bg-slate-50 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveSubForm({ cat1v: form.cat1v })}
                  className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-xs transition-all flex items-center gap-1.5"
                >
                  {submitting ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                  Save Society Scorecard
                </button>
              </div>
            </div>
          )}

          {/* Annexure II: Research and Academic Contribution Score Table Form */}
          {activeSubForm === 'cat2' && (
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
              <div>
                <h2 className="text-xl font-bold text-[#E05E26]">Research and Academic contribution</h2>
                <h4 className="text-xs font-semibold text-slate-500 bg-slate-100 px-4 py-2 mt-2 border border-slate-200 rounded">Annexure II</h4>
              </div>

              <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-bold tracking-wider">
                      <th className="px-4 py-3 w-16 text-center">S.No</th>
                      <th className="px-4 py-3">Particulars</th>
                      <th className="px-4 py-3 text-center w-36">Self Assessment</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium">
                    {cat2Categories.map(cat => {
                      const valueObj = form.cat2.find(c => c.sno === cat.key);
                      const currentVal = valueObj ? valueObj.score : '0';
                      return (
                        <tr key={cat.key} className={cat.headerOnly ? 'bg-slate-50/20' : 'hover:bg-slate-50/30'}>
                          <td className="px-4 py-3.5 text-center font-semibold text-slate-500">{cat.sno}</td>
                          <td className="px-4 py-3.5 text-slate-800" style={{ paddingLeft: `${cat.indent * 1.5 + 1}rem` }}>
                            <span className={cat.headerOnly ? 'font-bold text-slate-700' : 'font-medium'}>{cat.particulars}</span>
                          </td>
                          <td className="px-4 py-3.5 text-center">
                            {!cat.headerOnly && (
                              <input
                                type="number"
                                min="0"
                                value={currentVal}
                                onChange={(e) => {
                                  const val = e.target.value === '' ? '0' : String(Math.max(0, Number(e.target.value)));
                                  const updated = form.cat2.map(x => x.sno === cat.key ? { ...x, score: val } : x);
                                  setForm({ ...form, cat2: updated });
                                }}
                                className="w-24 px-3 py-1.5 border border-slate-200 rounded-lg text-center font-semibold focus:outline-none focus:border-indigo-500"
                              />
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Research score augmentation guidelines */}
              <div className="text-[11px] text-slate-700 bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-2 leading-relaxed font-bold">
                <p className="text-slate-800 font-extrabold">The Research score for research papers would be augmented as follows:</p>
                <p className="text-slate-800 font-extrabold">Peer- Reviewed or UGC- listed journals (impact factor to be determined as per Thomsons Reuters list):</p>
                <ul className="list-none space-y-1 pl-2 text-slate-700">
                  <li>i. Paper in refereed journals without impact factor - 05 points</li>
                  <li>ii. Paper with impact factor less than 1- 10 points</li>
                  <li>iii. Paper with impact factor between 1 and 2- 15 points</li>
                  <li>iv. Paper with impact factor between 2 and 5- 20 points</li>
                  <li>v. Paper with impact factor between 5 and 10- 25 points</li>
                  <li>vi. Paper with impact factor greater than 10- 30 points</li>
                </ul>
                <p className="pt-2 font-extrabold text-slate-800">(a) Two authors: 70% of total value of publication for each author.</p>
                <p className="font-extrabold text-slate-800">(b) More than two authors : 70% of total value of publication for the First/ Principal/Corresponding author and 30% of total value of publication for each of the joint auhtors. Joint Projects: Principal Investigator and Co-investogator would get 50% each.</p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveSubForm('none')}
                  className="px-5 py-2.5 border rounded-xl font-bold text-slate-700 bg-white hover:bg-slate-50 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveSubForm({ cat2: form.cat2 })}
                  className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs transition-all flex items-center gap-1.5 shadow-lg shadow-indigo-600/10 active:scale-[0.98]"
                >
                  {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
                  Submit Annexure II
                </button>
              </div>
            </div>
          )}

          {/* Annexure III: Self Assessment Table Form */}
          {activeSubForm === 'cat3' && (
            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-800">Forms</h2>
                <h4 className="text-xs font-semibold text-slate-500 bg-slate-100 px-4 py-2 mt-2 border border-slate-200 rounded">Annexure III</h4>
              </div>

              <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase font-bold tracking-wider">
                      <th className="px-4 py-3 w-16 text-center">S.No</th>
                      <th className="px-4 py-3">Particulars</th>
                      <th className="px-4 py-3 text-center w-36">Self Assessment</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                    {cat3Categories.map(cat => {
                      const valueObj = form.cat3.find(c => c.sno === cat.key);
                      const currentVal = valueObj ? valueObj.score : '0';
                      return (
                        <tr key={cat.key} className="hover:bg-slate-50/30">
                          <td className="px-4 py-3.5 text-center font-semibold text-slate-500">{cat.sno}</td>
                          <td className="px-4 py-3.5 font-medium">{cat.particulars}</td>
                          <td className="px-4 py-3.5 text-center">
                            <input
                              type="number"
                              min="0"
                              value={currentVal}
                              onChange={(e) => {
                                const val = e.target.value === '' ? '0' : String(Math.max(0, Number(e.target.value)));
                                const updated = form.cat3.map(x => x.sno === cat.key ? { ...x, score: val } : x);
                                setForm({ ...form, cat3: updated });
                              }}
                              className="w-24 px-3 py-1.5 border border-slate-200 rounded-lg text-center font-semibold focus:outline-none focus:border-indigo-500"
                            />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveSubForm('none')}
                  className="px-5 py-2.5 border rounded-xl font-bold text-slate-700 bg-white hover:bg-slate-50 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveSubForm({ cat3: form.cat3 })}
                  className="px-6 py-2.5 bg-[#2E689C] hover:bg-[#23517A] text-white font-bold rounded-xl text-xs transition-all flex items-center gap-1.5 shadow-lg shadow-blue-600/10 active:scale-[0.98]"
                >
                  {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
                  Submit Annexure III
                </button>
              </div>
            </div>
          )}

          {/* Interactive HOD Confidential Report (Fill API Credit) */}
          {activeSubForm === 'confidential' && confidentialTargetFaculty && (
            <div className="space-y-6">
              <button
                onClick={() => setActiveSubForm('none')}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all inline-flex items-center gap-1.5 print-hide"
              >
                <ArrowLeft size={14} /> Back to List
              </button>

              <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden p-6 space-y-6 print:border-none print:shadow-none">
                <div className="border-b border-slate-200 pb-4 space-y-2">
                  <h2 className="text-xl font-black text-slate-800 text-center">Confidential Report</h2>
                  <h3 className="text-sm font-extrabold text-indigo-600 text-center uppercase tracking-wider">Fill Api Credit</h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100 mt-4 text-xs font-bold text-slate-700">
                    <div>
                      Faculty Name: <span className="text-slate-900">{staffCache[confidentialTargetFaculty.faculty_computer_code] ? `${staffCache[confidentialTargetFaculty.faculty_computer_code].title || ''} ${staffCache[confidentialTargetFaculty.faculty_computer_code].first_name} ${staffCache[confidentialTargetFaculty.faculty_computer_code].last_name}` : 'Loading...'}</span>
                    </div>
                    <div>
                      Department: <span className="text-slate-900">{user?.department || 'Computer Science'}</span>
                    </div>
                    <div>
                      Designation: <span className="text-slate-900">{confidentialTargetFaculty.designation || (staffCache[confidentialTargetFaculty.faculty_computer_code]?.details as any)?.designation || 'Not assigned'}</span>
                    </div>
                    <div>
                      Academic Session: <span className="text-slate-900">{sessionsDropdown.find(s => s.id === confidentialTargetFaculty.academic_session)?.name || 'Active'}</span>
                    </div>
                    <div>
                      Computer Code: <span className="text-slate-900 font-mono">{confidentialTargetFaculty.faculty_computer_code}</span>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-500 font-bold leading-relaxed pt-2 text-center">
                    The assessment of the faculty against the parameters indicated below is to be done by HOD by assigning an appropriate grade on a scale of 1 to 10. (10 is highest.)
                  </p>
                </div>

                <div className="overflow-x-auto border border-slate-200 rounded-xl bg-white">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
                        <th className="px-4 py-3 w-16 text-center border-r border-slate-200">S.No</th>
                        <th className="px-4 py-3 border-r border-slate-200">Parameter</th>
                        <th className="px-4 py-3 w-48 text-center">Assessment</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 font-medium text-slate-800">
                      {confidentialParameters.map((param, index) => {
                        const isLocked = ['Forwarded to Principal', 'Principal Approved', 'Principal Rejected'].includes(appraisalStatus);
                        return (
                          <tr key={param.key} className="hover:bg-slate-50/50">
                            <td className="px-4 py-3.5 text-center text-slate-500 border-r border-slate-200">{index + 1}</td>
                            <td className="px-4 py-3.5 border-r border-slate-200 font-bold text-slate-700">{param.label}</td>
                            <td className="px-4 py-3.5 text-center">
                              {isLocked ? (
                                <span className="font-extrabold text-sm text-indigo-600">{(confidentialForm as any)[param.key] || 'Not Evaluated'}</span>
                              ) : (
                                <select
                                  value={(confidentialForm as any)[param.key]}
                                  onChange={(e) => {
                                    setConfidentialForm(prev => ({
                                      ...prev,
                                      [param.key]: e.target.value === '' ? '' : Number(e.target.value)
                                    }));
                                  }}
                                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 bg-white font-bold text-center"
                                >
                                  <option value="">-- Score --</option>
                                  {[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map(num => (
                                    <option key={num} value={num}>{num}</option>
                                  ))}
                                </select>
                              )}
                            </td>
                          </tr>
                        );
                      })}

                      <tr className="bg-slate-50 border-t border-slate-300 font-bold text-slate-900">
                        <td colSpan={2} className="px-4 py-4 text-right border-r border-slate-200 uppercase tracking-wider font-extrabold">Total Marks:</td>
                        <td className="px-4 py-4 text-center text-sm font-black text-indigo-600">
                          {(() => {
                            const sum = [
                              confidentialForm.parameter_1, confidentialForm.parameter_2, confidentialForm.parameter_3,
                              confidentialForm.parameter_4, confidentialForm.parameter_5, confidentialForm.parameter_6,
                              confidentialForm.parameter_7
                            ].reduce((acc: number, val) => acc + (val === '' ? 0 : Number(val)), 0);
                            return `${sum}/70`;
                          })()}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div className="space-y-2">
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">HOD Confidential Remarks</label>
                  {['Forwarded to Principal', 'Principal Approved', 'Principal Rejected'].includes(appraisalStatus) ? (
                    <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 italic">
                      "{confidentialForm.remarks || 'No remarks provided.'}"
                    </div>
                  ) : (
                    <textarea
                      rows={3}
                      value={confidentialForm.remarks}
                      onChange={(e) => setConfidentialForm(prev => ({ ...prev, remarks: e.target.value }))}
                      placeholder="Input confidential remarks or appraisal performance details..."
                      className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 bg-white"
                    />
                  )}
                </div>

                <div className="flex flex-wrap items-center justify-end gap-3 pt-6 border-t border-slate-200 print-hide">
                  <button
                    type="button"
                    onClick={() => {
                      setPrintTarget(confidentialTargetFaculty);
                      setPrintType('cr');
                    }}
                    className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl text-xs flex items-center gap-1.5 transition-all shadow-sm"
                  >
                    <Printer size={14} /> Print Confidential Report
                  </button>

                  {!['Forwarded to Principal', 'Principal Approved', 'Principal Rejected'].includes(appraisalStatus) && (
                    <>
                      <button
                        type="button"
                        onClick={() => handleSaveConfidentialAssessment('Draft')}
                        disabled={submitting}
                        className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition-all flex items-center gap-1.5 disabled:opacity-50"
                      >
                        <Save size={14} /> Save Draft
                      </button>

                      <button
                        type="button"
                        onClick={() => handleSaveConfidentialAssessment('Submitted')}
                        disabled={submitting}
                        className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-xs flex items-center gap-1.5 transition-all shadow-md active:scale-[0.98] disabled:opacity-50"
                      >
                        <Send size={14} /> Submit
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

        </div>
      ) : viewMode === 'review' ? (

        /* ─── HOD review department list dashboard ─────────────────── */
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-slate-800">Department Performance Appraisals</h2>
              <p className="text-xs text-slate-400 mt-1">Reviewing submissions for department: <strong className="text-slate-600">{user?.department || 'Assigned Department'}</strong></p>
            </div>
            <div className="flex gap-2">
              {selectedAppraisals.length > 0 && (
                <button
                  onClick={handleToolbarFillCredit}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs flex items-center gap-1.5 transition-all shadow-sm"
                >
                  <FileSpreadsheet size={12} /> Fill Credit
                </button>
              )}
              <button
                onClick={async () => {
                  setLoading(true);
                  await loadHODDashboard();
                  setLoading(false);
                }}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition-all"
              >
                Refresh Submissions
              </button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
                    <th className="px-4 py-3 w-12 text-center border-r border-slate-100">□</th>
                    <th className="px-4 py-3 w-16 text-center border-r border-slate-100">S.No</th>
                    <th className="px-4 py-3 border-r border-slate-100">Faculty Name</th>
                    <th className="px-4 py-3 border-r border-slate-100">Computer Code</th>
                    <th className="px-4 py-3 border-r border-slate-100">Academic Session</th>
                    <th className="px-4 py-3 border-r border-slate-100">Status</th>
                    <th className="px-4 py-3 text-center w-28">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-semibold text-slate-700 bg-white">
                  {departmentList.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-16 text-slate-400 font-normal">
                        No department appraisals forwarded for review.
                      </td>
                    </tr>
                  ) : departmentList.map((item, index) => {
                    const name = item.faculty_name || `Code ${item.faculty_computer_code}`;
                    const sessionName = sessionsDropdown.find(s => s.id === item.academic_session)?.name || item.academic_session;

                    const metaRow = item.cat1i?.find((x: any) => x.sno === -999);
                    let rowStatus = 'Draft';
                    if (metaRow && metaRow.ccnc) {
                      try {
                        rowStatus = JSON.parse(metaRow.ccnc).status || 'Draft';
                      } catch (e) { }
                    } else {
                      if (item.hod_approval) rowStatus = 'Approved';
                      else if (item.submited) rowStatus = 'Submitted';
                    }

                    const isSelectable = rowStatus === 'Under HOD Review' || rowStatus === 'Submitted to HOD' || rowStatus === 'CR Draft' || rowStatus === 'Confidential Report Submitted';

                    return (
                      <tr key={item.api_id} className="hover:bg-slate-50/50">
                        <td className="px-4 py-4 text-center border-r border-slate-100">
                          <input
                            type="checkbox"
                            disabled={!isSelectable}
                            checked={selectedAppraisals.includes(item.api_id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedAppraisals([item.api_id]);
                              } else {
                                setSelectedAppraisals([]);
                              }
                            }}
                            className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 disabled:opacity-50"
                          />
                        </td>
                        <td className="px-4 py-4 text-center text-slate-400 border-r border-slate-100">{index + 1}</td>
                        <td className="px-4 py-4 border-r border-slate-100 text-slate-900 truncate max-w-[180px]" title={name}>{name}</td>
                        <td className="px-4 py-4 border-r border-slate-100 font-mono" title={item.faculty_computer_code}>{item.faculty_computer_code}</td>
                        <td className="px-4 py-4 border-r border-slate-100">{sessionName}</td>
                        <td className="px-4 py-4 border-r border-slate-100">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold tracking-wide uppercase ${
                            rowStatus === 'Forwarded to Principal'
                              ? 'bg-blue-50 text-blue-700 border border-blue-200'
                              : rowStatus === 'Confidential Report Submitted'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : (rowStatus === 'Under HOD Review' || rowStatus === 'Submitted to HOD')
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-slate-50 text-slate-600 border border-slate-200'
                          }`}>
                            {rowStatus}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-center whitespace-nowrap space-x-2">
                          <button
                            onClick={() => {
                              navigate(`/dashboard/staff/feedback?view=review&id=${item.api_id}`);
                            }}
                            className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition-all shadow-md active:scale-95 animate-fade-in"
                          >
                            Review
                          </button>
                          <button
                            onClick={async () => {
                              if (!window.confirm("Are you sure you want to remove this appraisal?")) return;
                              try {
                                const res = await api.delete(`/api360/${item.api_id}`);
                                if (res.data?.success) {
                                  setToast({ msg: "Appraisal removed successfully.", type: 'success' });
                                  await loadHODDashboard();
                                }
                              } catch (e: any) {
                                setToast({ msg: "Failed to remove: " + (e.response?.data?.detail || "Error"), type: 'error' });
                              }
                            }}
                            className="px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg text-xs font-bold transition-all active:scale-95"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      ) : viewMode === 'staff-review' ? (

        /* ─── HOD detailed Staff Review dashboard ─────────────────── */
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-slate-800">Department Performance Appraisals</h2>
              <p className="text-xs text-slate-400 mt-1">Reviewing submissions for department: <strong className="text-slate-600">{user?.department || 'Assigned Department'}</strong></p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={async () => {
                  setLoading(true);
                  await loadHODDashboard();
                  setLoading(false);
                }}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition-all"
              >
                Refresh Submissions
              </button>
            </div>
          </div>

          {/* Accordion named Full Details */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <button
              onClick={() => setIsStaffReviewOpen(!isStaffReviewOpen)}
              className="w-full flex items-center justify-between p-5 bg-slate-50 border-b border-slate-200 text-left transition-colors hover:bg-slate-100/50"
            >
              <span className="font-extrabold text-slate-800 text-sm uppercase tracking-wider flex items-center gap-2">
                <Users size={16} className="text-indigo-600" />
                Full Details
              </span>
              {isStaffReviewOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>

            {isStaffReviewOpen && (
              <div className="p-6 space-y-6 bg-slate-50/20">
                {/* Category : 1 collapsible panel */}
                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                  <button
                    onClick={() => setIsCategory1Open(!isCategory1Open)}
                    className="w-full flex items-center justify-between p-4 bg-slate-50/50 border-b border-slate-200 text-left transition-colors hover:bg-slate-100/30"
                  >
                    <span className="font-bold text-slate-800 text-xs uppercase tracking-wider">Category : 1</span>
                    {isCategory1Open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>

                  {isCategory1Open && (
                    <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
                            <th className="px-4 py-3 w-12 text-center border-r border-slate-100">□</th>
                            <th className="px-4 py-3 w-16 text-center border-r border-slate-100">S.No</th>
                            <th className="px-4 py-3 border-r border-slate-100">Department</th>
                            <th className="px-4 py-3 border-r border-slate-100">Name</th>
                            <th className="px-4 py-3 border-r border-slate-100">Designation</th>
                            <th className="px-4 py-3 text-center border-r border-slate-100 w-44">CR</th>
                            <th className="px-4 py-3 text-center border-r border-slate-100 w-44">API</th>
                            <th className="px-4 py-3 text-center w-28">Summary</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 font-semibold text-slate-700 bg-white">
                          {getFilteredDeptList().length === 0 ? (
                            <tr>
                              <td colSpan={8} className="text-center py-16 text-slate-400 font-normal">
                                No department appraisals forwarded for review.
                              </td>
                            </tr>
                          ) : getFilteredDeptList().map((item, index) => {
                            const name = item.faculty_name || `Code ${item.faculty_computer_code}`;
                            const deptName = item.department || 'Not assigned';
                            const designationName = item.designation || 'Not assigned';
                            const sessionName = sessionsDropdown.find(s => s.id === item.academic_session)?.name || item.academic_session;

                            const metaRow = item.cat1i?.find((x: any) => x.sno === -999);
                            let rowStatus = 'Draft';
                            if (metaRow && metaRow.ccnc) {
                              try {
                                rowStatus = JSON.parse(metaRow.ccnc).status || 'Draft';
                              } catch (e) { }
                            } else {
                              if (item.hod_approval) rowStatus = 'Approved';
                              else if (item.submited) rowStatus = 'Submitted';
                            }

                            const crStatus = item.confidential?.status || 'None';
                            const isSelectable = rowStatus === 'Under HOD Review' || rowStatus === 'Submitted to HOD' || rowStatus === 'CR Draft' || rowStatus === 'Confidential Report Submitted';

                            return (
                              <tr key={item.api_id} className="hover:bg-slate-50/50">
                                <td className="px-4 py-4 text-center border-r border-slate-100">
                                  <input
                                    type="checkbox"
                                    disabled={!isSelectable}
                                    checked={selectedAppraisals.includes(item.api_id)}
                                    onChange={(e) => {
                                      if (e.target.checked) {
                                        setSelectedAppraisals([item.api_id]);
                                      } else {
                                        setSelectedAppraisals([]);
                                      }
                                    }}
                                    className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 disabled:opacity-50"
                                  />
                                </td>
                                <td className="px-4 py-4 text-center text-slate-400 border-r border-slate-100">{index + 1}</td>
                                <td className="px-4 py-4 border-r border-slate-100 truncate max-w-[150px]" title={deptName}>{deptName}</td>
                                <td className="px-4 py-4 border-r border-slate-100 text-slate-900 truncate max-w-[150px]" title={name}>{name}</td>
                                <td className="px-4 py-4 border-r border-slate-100 truncate max-w-[150px]" title={designationName}>{designationName}</td>
                                
                                {/* CR Column */}
                                <td className="px-4 py-4 text-center border-r border-slate-100 space-x-1.5 whitespace-nowrap">
                                  <button
                                    onClick={() => handlePrintCR(item)}
                                    className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[10px] font-extrabold transition-all inline-flex items-center gap-0.5"
                                  >
                                    <Printer size={10} /> Print
                                  </button>
                                  <button
                                    onClick={() => handleOpenConfidentialAssessment(item)}
                                    className={`px-2.5 py-1 text-white rounded text-[10px] font-extrabold transition-all ${
                                      crStatus === 'Submitted' || crStatus === 'Draft'
                                        ? 'bg-red-500 hover:bg-red-600'
                                        : 'bg-blue-600 hover:bg-blue-700'
                                    }`}
                                  >
                                    {crStatus === 'Submitted' || crStatus === 'Draft' ? 'Edit' : 'Fill'}
                                  </button>
                                </td>

                                {/* API Column */}
                                <td className="px-4 py-4 text-center border-r border-slate-100 space-x-1.5 whitespace-nowrap">
                                  <button
                                    onClick={() => handlePrintAPI(item)}
                                    className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[10px] font-extrabold transition-all inline-flex items-center gap-0.5"
                                  >
                                    <Printer size={10} /> Print
                                  </button>
                                  <button
                                    onClick={() => {
                                      navigate(`/dashboard/staff/feedback?view=staff-review&id=${item.api_id}`);
                                    }}
                                    className="px-2.5 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-[10px] font-extrabold transition-all"
                                  >
                                    Edit
                                  </button>
                                </td>

                                {/* Summary Column */}
                                <td className="px-4 py-4 text-center whitespace-nowrap">
                                  <button
                                    onClick={() => handlePrintSummary(item)}
                                    className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[10px] font-extrabold transition-all inline-flex items-center gap-0.5"
                                  >
                                    <Printer size={10} /> Print
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : viewMode === 'principal' ? (

        /* ─── Principal review dashboard ─────────────────── */
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-slate-800">Principal Appraisal review console</h2>
              <p className="text-xs text-slate-400 mt-1">Reviewing forwarded scorecards and HOD submissions</p>
            </div>
            <button
              onClick={async () => {
                setLoading(true);
                await loadPrincipalDashboard();
                setLoading(false);
              }}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition-all"
            >
              Refresh Appraisals
            </button>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase text-[11px] tracking-wider">
                    <th className="px-6 py-3 text-center w-16">S.No</th>
                    <th className="px-6 py-3">Faculty Name</th>
                    <th className="px-6 py-3 w-32">Computer Code</th>
                    <th className="px-6 py-3 w-40">Academic Session</th>
                    <th className="px-6 py-3 w-48 text-center">Status</th>
                    <th className="px-6 py-3 text-right w-44">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-semibold text-slate-700">
                  {principalList.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-16 text-slate-400 font-normal">
                        No HOD scorecards or forwarded faculty scorecards available.
                      </td>
                    </tr>
                  ) : principalList.map((item, index) => {
                    const cache = staffCache[item.faculty_computer_code];
                    const name = cache ? `${cache.title || ''} ${cache.first_name} ${cache.last_name}` : 'Loading profile...';
                    const sessionName = sessionsDropdown.find(s => s.id === item.academic_session)?.name || 'Active';

                    const metaRow = item.cat1i?.find((x: any) => x.sno === -999);
                    let rowStatus = 'Draft';
                    if (metaRow && metaRow.ccnc) {
                      try {
                        rowStatus = JSON.parse(metaRow.ccnc).status || 'Draft';
                      } catch (e) { }
                    } else {
                      if (item.hod_approval) rowStatus = 'Approved';
                      else if (item.submited) rowStatus = 'Submitted';
                    }

                    return (
                      <tr key={item.api_id} className="hover:bg-slate-50/50">
                        <td className="px-6 py-4 text-center text-slate-400">#{index + 1}</td>
                        <td className="px-6 py-4 text-slate-900">{name}</td>
                        <td className="px-6 py-4 font-mono text-xs">{item.faculty_computer_code}</td>
                        <td className="px-6 py-4">{sessionName}</td>
                        <td className="px-6 py-4 text-center">{getStatusBadge(rowStatus)}</td>
                        <td className="px-6 py-4 text-right space-x-1.5">
                          <button
                            onClick={() => {
                              navigate(`/dashboard/staff/feedback?view=principal&id=${item.api_id}`);
                            }}
                            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition-all inline-flex items-center gap-1"
                          >
                            <Eye size={12} /> Review
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (

        /* ─── TEACHER & HOD DETAIL VIEW WORKSPACE ────────────────────── */
        <div className="space-y-6 relative print-hide">

          {/* Back to Review / Principal Dashboards */}
          {!isSelf && (
            <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200 print-hide">
              <span className="text-xs font-bold text-slate-400">You are reviewing a scorecard.</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const viewParam = new URLSearchParams(location.search).get('view');
                    navigate(`/dashboard/staff/feedback?view=${viewParam || 'review'}`);
                  }}
                  className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg text-xs transition-all flex items-center gap-1"
                >
                  <ArrowLeft size={14} /> Back to Review List
                </button>
              </div>
            </div>
          )}

          {/* Admin Evaluation Selector Header (Print Hide) */}
          {isAdmin() && isSelf && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 print-hide">
              <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="text-indigo-600" size={16} />
                Admin Feedback Evaluation Selector
              </h4>
              <form onSubmit={handleAdminLoad} className="flex flex-wrap gap-4 items-end">
                <div className="flex-1 min-w-[200px] space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Faculty Computer Code</label>
                  <input
                    type="text"
                    required
                    placeholder="Enter Computer Code..."
                    value={selectedFacultyCode}
                    onChange={(e) => setSelectedFacultyCode(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                  />
                </div>
                <div className="flex-1 min-w-[200px] space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Academic Session</label>
                  <select
                    required
                    value={selectedSessionId}
                    onChange={(e) => setSelectedSessionId(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 bg-white"
                  >
                    <option value="">-- Select Session --</option>
                    {sessionsDropdown.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition-all active:scale-[0.98]"
                >
                  Load Evaluation
                </button>
              </form>
            </div>
          )}

          {selectedRecordId ? (
            <div className="space-y-6">

              {/* PRINT METADATA PANEL IN PORTAL PREVIEW */}
              <div className="flex justify-between items-center bg-white p-5 rounded-xl border border-slate-200 shadow-sm print:border-none print:shadow-none">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center font-mono font-bold text-slate-700 text-lg print-hide">
                    {facultyName ? facultyName[0] : 'F'}
                  </div>
                  <div>
                    <h2 className="text-md font-extrabold text-slate-800">{facultyName || 'Loading Faculty...'}</h2>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Computer Code: <strong className="text-slate-600">{form.faculty_computer_code}</strong> | Department: <strong className="text-slate-600">{isStaff() ? (user?.department || 'IT') : 'Verified Department'}</strong>
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Academic Session: <strong className="text-slate-600">{sessionsDropdown.find(s => s.id === Number(form.academic_session))?.name || 'Active'}</strong>
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1.5">
                  <div className="flex items-center gap-2">
                    {/* Status badge removed as per request */}
                  </div>
                  {lastModified && (
                    <span className="text-[10px] text-slate-400 font-semibold">Last Modified: {new Date(lastModified).toLocaleString()}</span>
                  )}
                </div>
              </div>

              {/* CARD 1: ANNEXURE I Accordion */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden print:border-none print:shadow-none">
                <button
                  onClick={() => toggleAccordion('annexure1')}
                  className="w-full px-6 py-4 flex items-center justify-between bg-slate-50/75 hover:bg-slate-50 transition-colors text-left border-b border-slate-100 print-hide"
                >
                  <div>
                    <h3 className="font-extrabold text-slate-800 text-md">Annexure I – Teaching Process & Performance</h3>
                    <p className="text-xs text-slate-400 mt-0.5">Section A to E details</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs bg-indigo-50 text-indigo-700 font-extrabold px-2.5 py-1 rounded-md">Score: {calculateAnnexureITotal()}/100</span>
                    {accordions.annexure1 ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                  </div>
                </button>

                {/* Print Title Header */}
                <div className="hidden print:block border-b-2 border-slate-200 pb-2 mb-4 mt-6">
                  <h3 className="text-md font-bold text-slate-800">Annexure I – Teaching Process & Performance</h3>
                  <span className="text-xs text-slate-500">Calculated Annexure Total Score: <strong>{calculateAnnexureITotal()}/100</strong></span>
                </div>

                {accordions.annexure1 && (
                  <div className="p-6 space-y-6">

                    {/* A. Teaching Process */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider">A. Teaching Process (Maximum 25 Marks)</h4>
                        <span className="text-xs font-bold text-indigo-600">Score: {calculateTeachingScore()}/25</span>
                      </div>
                      {renderCat1iTableReadOnly(form.cat1i)}
                      {(!form.hod_approval && (isSelf || role === 'HOD')) && (
                        <button
                          type="button"
                          onClick={() => setActiveSubForm('cat1i')}
                          className="px-4 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 print-hide"
                        >
                          <Plus size={12} /> Add Teaching Process
                        </button>
                      )}
                    </div>

                    {/* B. Student Feedback */}
                    <div className="space-y-2 pt-4 border-t border-slate-100">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider">B. Student Feedback (Maximum 25 Marks)</h4>
                        <span className="text-xs font-bold text-indigo-600">Score: {calculateFeedbackScore()}/25</span>
                      </div>
                      {renderCat1iiTableReadOnly(form.cat1ii)}
                      {(!form.hod_approval && (isSelf || role === 'HOD')) && (
                        <button
                          type="button"
                          onClick={() => setActiveSubForm('cat1ii')}
                          className="px-4 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 print-hide"
                        >
                          <Plus size={12} /> Add Student Feedback
                        </button>
                      )}
                    </div>

                    {/* C. Departmental Activities */}
                    <div className="space-y-2 pt-4 border-t border-slate-100">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider">C. Departmental Activities (Maximum 20 Marks)</h4>
                        <span className="text-xs font-bold text-indigo-600">Score: {calculateDeptScore()}/20</span>
                      </div>
                      {renderGenericCat1Table(form.cat1iii)}
                      {(!form.hod_approval && (isSelf || role === 'HOD')) && (
                        <button
                          type="button"
                          onClick={() => setActiveSubForm('cat1iii')}
                          className="px-4 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 print-hide"
                        >
                          <Plus size={12} /> Add Departmental Activities
                        </button>
                      )}
                    </div>

                    {/* D. Institute Activities */}
                    <div className="space-y-2 pt-4 border-t border-slate-100">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider">D. Institute Activities (Maximum 10 Marks)</h4>
                        <span className="text-xs font-bold text-indigo-600">Score: {calculateInstScore()}/10</span>
                      </div>
                      {renderGenericCat1Table(form.cat1iv)}
                      {(!form.hod_approval && (isSelf || role === 'HOD')) && (
                        <button
                          type="button"
                          onClick={() => setActiveSubForm('cat1iv')}
                          className="px-4 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 print-hide"
                        >
                          <Plus size={12} /> Add Institute Activities
                        </button>
                      )}
                    </div>

                    {/* E. Contribution to Society */}
                    <div className="space-y-2 pt-4 border-t border-slate-100">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider">E. Contribution to Society (Maximum 10 Marks)</h4>
                        <span className="text-xs font-bold text-indigo-600">Score: {calculateSocietyScore()}/10</span>
                      </div>
                      {renderGenericCat1Table(form.cat1v)}
                      {(!form.hod_approval && (isSelf || role === 'HOD')) && (
                        <button
                          type="button"
                          onClick={() => setActiveSubForm('cat1v')}
                          className="px-4 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 print-hide"
                        >
                          <Plus size={12} /> Add Society Contribution
                        </button>
                      )}
                    </div>

                  </div>
                )}
              </div>

              {/* CARD 2: ANNEXURE II Accordion */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden print:border-none print:shadow-none">
                <button
                  onClick={() => toggleAccordion('annexure2')}
                  className="w-full px-6 py-4 flex items-center justify-between bg-slate-50/75 hover:bg-slate-50 transition-colors text-left border-b border-slate-100 print-hide"
                >
                  <div>
                    <h3 className="font-extrabold text-slate-800 text-md">Annexure II – Research & Academic Contribution</h3>
                    <p className="text-xs text-slate-400 mt-0.5">Publications and academic writing details</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs bg-emerald-50 text-emerald-700 font-extrabold px-2.5 py-1 rounded-md">Score: {calculateAnnexureIITotal()}</span>
                    {accordions.annexure2 ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                  </div>
                </button>

                {/* Print Title Header */}
                <div className="hidden print:block border-b-2 border-slate-200 pb-2 mb-4 mt-6">
                  <h3 className="text-md font-bold text-slate-800">Annexure II – Research & Academic Contribution</h3>
                  <span className="text-xs text-slate-500">Calculated Annexure Score: <strong>{calculateAnnexureIITotal()}</strong></span>
                </div>

                {accordions.annexure2 && (
                  <div className="p-6 space-y-4">
                    {renderActiveCat2Table()}
                    {(!form.hod_approval && (isSelf || role === 'HOD')) && (
                      <button
                        type="button"
                        onClick={() => setActiveSubForm('cat2')}
                        className="px-4 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 print-hide"
                      >
                        <Plus size={12} /> Add Record
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* CARD 3: ANNEXURE III Accordion */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden print:border-none print:shadow-none">
                <button
                  onClick={() => toggleAccordion('annexure3')}
                  className="w-full px-6 py-4 flex items-center justify-between bg-slate-50/75 hover:bg-slate-50 transition-colors text-left border-b border-slate-100 print-hide"
                >
                  <div>
                    <h3 className="font-extrabold text-slate-800 text-md">Annexure III – Self Assessment</h3>
                    <p className="text-xs text-slate-400 mt-0.5">PhD/PG guidance, course certifications and sponsored projects</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs bg-indigo-50 text-indigo-700 font-extrabold px-2.5 py-1 rounded-md">Score: {calculateAnnexureIIITotal()}</span>
                    {accordions.annexure3 ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                  </div>
                </button>

                {/* Print Title Header */}
                <div className="hidden print:block border-b-2 border-slate-200 pb-2 mb-4 mt-6">
                  <h3 className="text-md font-bold text-slate-800">Annexure III – Self Assessment of Research & Academic Contribution</h3>
                  <span className="text-xs text-slate-500">Calculated Annexure Score: <strong>{calculateAnnexureIIITotal()}</strong></span>
                </div>

                {accordions.annexure3 && (
                  <div className="p-6 space-y-4">
                    {renderActiveCat3Table()}
                    {(!form.hod_approval && (isSelf || role === 'HOD')) && (
                      <button
                        type="button"
                        onClick={() => setActiveSubForm('cat3')}
                        className="px-4 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 print-hide"
                      >
                        <Plus size={12} /> Add Record
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Summary Page Card */}
              <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 space-y-4">
                <div className="border-b-2 border-slate-200 pb-2">
                  <h3 className="text-md font-extrabold text-slate-800">Feedback Summary Report</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Consolidated appraisal outcomes and performance overview</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Completion Percentage</span>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-200 h-2.5 rounded-full overflow-hidden">
                        <div className="bg-indigo-600 h-full rounded-full transition-all duration-500" style={{ width: `${getCompletionPercentage()}%` }} />
                      </div>
                      <span className="text-sm font-extrabold text-slate-700">{getCompletionPercentage()}%</span>
                    </div>
                  </div>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Annexure I score</span>
                    <p className="text-lg font-black text-indigo-600">{calculateAnnexureITotal()}/100</p>
                  </div>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Annexure II Research Score</span>
                    <p className="text-lg font-black text-emerald-600">{calculateAnnexureIITotal()} pts</p>
                  </div>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-1">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Annexure III Score</span>
                    <p className="text-lg font-black text-slate-700">{calculateAnnexureIIITotal()} pts</p>
                  </div>
                </div>

                {hodRemarks && (
                  <div className="bg-indigo-50/50 p-4 rounded-xl border border-indigo-100/50 space-y-1.5 mt-2">
                    <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider flex items-center gap-1">
                      <Info size={12} /> HOD / Reviewer Remarks
                    </span>
                    <p className="text-xs text-slate-700 font-semibold italic">"{hodRemarks}"</p>
                    {approvedAt && (
                      <span className="text-[9px] text-slate-400 block font-bold mt-1">Processed on: {new Date(approvedAt).toLocaleString()}</span>
                    )}
                  </div>
                )}
              </div>



              {/* HOD Review Action Panel */}
              {role === 'HOD' && !isSelf && (
                <div className="bg-white border border-slate-200 rounded-xl shadow-md p-6 space-y-4 print-hide">
                  <div className="border-b pb-2">
                    <h3 className="font-extrabold text-slate-800 text-sm flex items-center gap-1.5">
                      <ShieldCheck className="text-indigo-600" size={16} />
                      Appraisal HOD review actions
                    </h3>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">HOD remarks & correction directives</label>
                    <textarea
                      rows={3}
                      value={hodRemarks}
                      onChange={(e) => setHodRemarks(e.target.value)}
                      placeholder="Input remarks, feedback, or correction suggestions..."
                      className="w-full px-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                    />
                  </div>
                  <div className="flex flex-wrap items-center gap-2 pt-2">

                    <button
                      onClick={() => handleHODDecision('Needs Correction')}
                      disabled={submitting}
                      className="px-5 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1 disabled:opacity-50"
                    >
                      <AlertOctagon size={14} /> Return for Correction
                    </button>
                    <button
                      onClick={() => handleHODDecision('Rejected')}
                      disabled={submitting}
                      className="px-5 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1 disabled:opacity-50"
                    >
                      <X size={14} /> Reject Appraisal
                    </button>
                  </div>
                </div>
              )}

              {/* Principal / Admin Review Action Panel */}
              {(role === 'Principal' || isAdmin()) && !isSelf && (
                <div className="bg-white border border-slate-200 rounded-xl shadow-md p-6 space-y-4 print-hide">
                  <div className="border-b pb-2">
                    <h3 className="font-extrabold text-slate-800 text-sm flex items-center gap-1.5">
                      <ShieldCheck className="text-indigo-600" size={16} />
                      Appraisal Principal Review Actions
                    </h3>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Principal Remarks</label>
                    <textarea
                      rows={3}
                      value={hodRemarks}
                      onChange={(e) => setHodRemarks(e.target.value)}
                      placeholder="Input Principal remarks & final evaluation details..."
                      className="w-full px-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                    />
                  </div>
                  <div className="flex flex-wrap items-center gap-2 pt-2">
                    <button
                      onClick={() => handlePrincipalDecision('Approved')}
                      disabled={submitting}
                      className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1 disabled:opacity-50"
                    >
                      <CheckCircle2 size={14} /> Final Approve
                    </button>
                    <button
                      onClick={() => handlePrincipalDecision('Needs Correction')}
                      disabled={submitting}
                      className="px-5 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1 disabled:opacity-50"
                    >
                      <AlertOctagon size={14} /> Return for Correction
                    </button>
                    <button
                      onClick={() => handlePrincipalDecision('Rejected')}
                      disabled={submitting}
                      className="px-5 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1 disabled:opacity-50"
                    >
                      <X size={14} /> Reject
                    </button>
                  </div>
                </div>
              )}

              {/* Bottom Footer Actions Panel */}
              <div className="flex flex-wrap items-center justify-end gap-3 pt-6 border-t border-slate-200 print-hide">
                <button
                  onClick={async () => {
                    if (!selectedRecordId) return;
                    setLoading(true);
                    try {
                      const freshDetail = await loadRecordDetails(selectedRecordId);
                      if (freshDetail) {
                        setPrintTarget(freshDetail);
                        setPrintType('api');
                      }
                    } catch (e) {
                      setToast({ msg: "Loading details failed", type: 'error' });
                    } finally {
                      setLoading(false);
                    }
                  }}
                  className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl text-sm flex items-center gap-1.5 transition-all"
                >
                  <Printer size={16} /> Print Appraisal Report
                </button>

                {(!form.hod_approval && (isSelf || role === 'HOD')) && (
                  <>
                    <button
                      onClick={() => handleTeacherSubmitAction('draft')}
                      disabled={submitting}
                      className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <Save size={16} /> Save Draft
                    </button>
                    {role !== 'HOD' && (
                      <button
                        onClick={() => handleTeacherSubmitAction('submit')}
                        disabled={submitting}
                        className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm flex items-center gap-1.5 transition-all shadow-lg shadow-indigo-600/10 active:scale-[0.98] disabled:opacity-50"
                      >
                        Submit Final Appraisal <ArrowRight size={16} />
                      </button>
                    )}
                  </>
                )}
              </div>

            </div>
          ) : (
            <div className="bg-white p-16 text-center max-w-md mx-auto rounded-2xl border border-slate-200 shadow-sm print-hide">
              <BookOpen className="w-16 h-16 text-slate-300 mx-auto mb-4 animate-pulse" />
              <h3 className="font-extrabold text-slate-800 text-lg">Evaluation Workspace Empty</h3>
              <p className="text-slate-500 text-sm mt-1">Please enter a Faculty Computer Code and select an Academic Session above to load or initialize their scorecard.</p>
            </div>
          )}

        </div>
      )}

      {/* ─── PRINTABLE REPORT AREA (HIDDEN IN SCREEN VIEW) ────────────────── */}
      {printType !== 'none' && printTarget && (
        <div id="printable-area" className="hidden print:block font-serif text-black p-8 space-y-8 bg-white">
          {/* Print CR */}
          {printType === 'cr' && (
            <div className="space-y-6">
              <div className="text-center pb-4 border-b border-black">
                <h1 className="text-2xl font-bold uppercase">IPS Academy</h1>
                <h2 className="text-sm font-semibold uppercase">Institute of Engineering & Science, Indore (M.P.)</h2>
                <h3 className="text-md font-bold mt-2 underline">Confidential Report (HOD API Assessment)</h3>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs font-bold border border-black p-4 rounded bg-white">
                <div>Faculty Name: {staffCache[printTarget.faculty_computer_code]?.staff ? `${staffCache[printTarget.faculty_computer_code].staff.title || ''} ${staffCache[printTarget.faculty_computer_code].staff.first_name} ${staffCache[printTarget.faculty_computer_code].staff.last_name}` : (printTarget.faculty_name || 'N/A')}</div>
                <div>Computer Code: {printTarget.faculty_computer_code}</div>
                <div>Department: {staffCache[printTarget.faculty_computer_code]?.details?.dept_id ? getDepartmentName(staffCache[printTarget.faculty_computer_code].details.dept_id) : (printTarget.department || 'N/A')}</div>
                <div>Academic Session: {sessionsDropdown.find(s => s.id === printTarget.academic_session)?.name || 'N/A'}</div>
              </div>

              <table className="w-full text-left text-xs border-collapse border border-black mt-4">
                <thead>
                  <tr className="bg-slate-50 border-b border-black text-black font-bold uppercase">
                    <th className="px-4 py-2 w-16 text-center border-r border-black">S.No</th>
                    <th className="px-4 py-2 border-r border-black">Parameter</th>
                    <th className="px-4 py-2 w-28 text-center">Score (1-10)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-black">
                  {confidentialParameters.map((param, idx) => (
                    <tr key={param.key}>
                      <td className="px-4 py-2.5 text-center border-r border-black">{idx + 1}</td>
                      <td className="px-4 py-2.5 border-r border-black font-semibold">{param.label}</td>
                      <td className="px-4 py-2.5 text-center font-bold">
                        {printTarget.confidential?.status === 'Submitted'
                          ? (printTarget.confidential?.[param.key] ?? 'N/A')
                          : 'N/A'}
                      </td>
                    </tr>
                  ))}
                  <tr className="border-t border-black font-bold">
                    <td colSpan={2} className="px-4 py-3 text-right border-r border-black uppercase font-bold">Total Marks:</td>
                    <td className="px-4 py-3 text-center text-sm font-bold">
                      {printTarget.confidential?.status === 'Submitted'
                        ? `${printTarget.confidential?.total_marks ?? 0}/70`
                        : '0/70'}
                    </td>
                  </tr>
                </tbody>
              </table>

              {printTarget.confidential?.status === 'Submitted' && printTarget.confidential?.remarks && (
                <div className="space-y-1 border border-black p-4 rounded mt-4">
                  <span className="text-[10px] font-bold uppercase tracking-wider block">Confidential Remarks by HOD:</span>
                  <p className="text-xs italic">"{printTarget.confidential.remarks}"</p>
                </div>
              )}

              <div className="pt-16 flex justify-between text-xs font-bold">
                <div className="text-center">
                  <div className="border-t border-black w-44 pt-2">Faculty Member Signature</div>
                </div>
                <div className="text-center">
                  <div className="border-t border-black w-44 pt-2">Head of Department (HOD)</div>
                </div>
              </div>
            </div>
          )}

          {/* Print API (Annexure I + Annexure II + Annexure III + CR + Final Summary Combined) */}
          {printType === 'api' && (
            <div className="space-y-12">
              {/* Part A: Annexure I */}
              <div className="space-y-6">
                <div className="text-center pb-4 border-b border-black">
                  <h1 className="text-2xl font-bold uppercase">IPS Academy</h1>
                  <h2 className="text-sm font-semibold uppercase">Institute of Engineering & Science, Indore (M.P.)</h2>
                  <h3 className="text-lg font-black mt-2 underline">Combined Self Appraisal & Confidential Report</h3>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs font-bold border border-black p-4 rounded bg-white">
                  <div>Faculty Name: {printTarget.faculty_name || 'N/A'}</div>
                  <div>Computer Code: {printTarget.faculty_computer_code}</div>
                  <div>Department: {printTarget.department || 'N/A'}</div>
                  <div>Academic Session: {sessionsDropdown.find(s => s.id === printTarget.academic_session)?.name || 'N/A'}</div>
                </div>

                <div className="space-y-4">
                  <h4 className="text-sm font-extrabold border-b pb-1 uppercase">Part A: Annexure I (Category-I) Details</h4>
                  
                  {/* Category-I (i) Teaching-learning, lectures, tutorials, practicals */}
                  <div className="space-y-2 mt-4">
                    <h5 className="text-[11px] font-extrabold uppercase text-slate-800">Section I: Teaching Process</h5>
                    <table className="w-full text-left text-[10px] border-collapse border border-black">
                      <thead>
                        <tr className="bg-slate-50 border-b border-black text-black font-bold">
                          <th className="px-3 py-1.5 w-12 text-center border-r border-black">S.No</th>
                          <th className="px-3 py-1.5 border-r border-black">Semester</th>
                          <th className="px-3 py-1.5 border-r border-black">Course Code / Name</th>
                          <th className="px-3 py-1.5 text-center w-24 border-r border-black">Scheduled</th>
                          <th className="px-3 py-1.5 text-center w-24 border-r border-black">Held (Offline)</th>
                          <th className="px-3 py-1.5 text-center w-24">Held (Online)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-black">
                        {(() => {
                          const cat1i = (printTarget.cat1i || []).filter((x: any) => x.sno !== -999);
                          return cat1i.length === 0 ? (
                            <tr><td colSpan={6} className="text-center py-2 text-slate-500">No Teaching Process added.</td></tr>
                          ) : cat1i.map((x: any, idx: number) => (
                            <tr key={idx}>
                              <td className="px-3 py-1.5 text-center border-r border-black">{idx + 1}</td>
                              <td className="px-3 py-1.5 border-r border-black">{x.sas || 'N/A'}</td>
                              <td className="px-3 py-1.5 border-r border-black">{x.ccnc || 'N/A'}</td>
                              <td className="px-3 py-1.5 text-center border-r border-black">{x.nsc || 0}</td>
                              <td className="px-3 py-1.5 text-center border-r border-black">{x.nahcof || 0}</td>
                              <td className="px-3 py-1.5 text-center">{x.nahcon || 0}</td>
                            </tr>
                          ));
                        })()}
                      </tbody>
                    </table>
                  </div>

                  {/* Category-I (ii) Student Feedback */}
                  <div className="space-y-2 mt-4">
                    <h5 className="text-[11px] font-extrabold uppercase text-slate-800">Section II: Student Feedback</h5>
                    <table className="w-full text-left text-[10px] border-collapse border border-black">
                      <thead>
                        <tr className="bg-slate-50 border-b border-black text-black font-bold">
                          <th className="px-3 py-1.5 w-12 text-center border-r border-black">S.No</th>
                          <th className="px-3 py-1.5 border-r border-black">Semester</th>
                          <th className="px-3 py-1.5 border-r border-black">Course Name / Project Details</th>
                          <th className="px-3 py-1.5 text-center w-28">Feedback Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-black">
                        {(!printTarget.cat1ii || printTarget.cat1ii.length === 0) ? (
                          <tr><td colSpan={4} className="text-center py-2 text-slate-500">No Student Feedback added.</td></tr>
                        ) : printTarget.cat1ii.map((x: any, idx: number) => (
                          <tr key={idx}>
                            <td className="px-3 py-1.5 text-center border-r border-black">{idx + 1}</td>
                            <td className="px-3 py-1.5 border-r border-black">{x.sas || 'N/A'}</td>
                            <td className="px-3 py-1.5 border-r border-black">{x.cnctp || 'N/A'}</td>
                            <td className="px-3 py-1.5 text-center font-bold">{x.asf || 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Category-I (iii) Participatory and Innovative teaching-learning methodologies */}
                  <div className="space-y-2 mt-4">
                    <h5 className="text-[11px] font-extrabold uppercase text-slate-800">Section III: Participatory & Innovative Teaching Methodologies</h5>
                    <table className="w-full text-left text-[10px] border-collapse border border-black">
                      <thead>
                        <tr className="bg-slate-50 border-b border-black text-black font-bold">
                          <th className="px-3 py-1.5 w-12 text-center border-r border-black">S.No</th>
                          <th className="px-3 py-1.5 border-r border-black">Semester / Session</th>
                          <th className="px-3 py-1.5 border-r border-black">Activity Description</th>
                          <th className="px-3 py-1.5 text-center w-28">Score / Extent</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-black">
                        {(!printTarget.cat1iii || printTarget.cat1iii.length === 0) ? (
                          <tr><td colSpan={4} className="text-center py-2 text-slate-500">No records added.</td></tr>
                        ) : printTarget.cat1iii.map((x: any, idx: number) => (
                          <tr key={idx}>
                            <td className="px-3 py-1.5 text-center border-r border-black">{idx + 1}</td>
                            <td className="px-3 py-1.5 border-r border-black">{x.sas || 'N/A'}</td>
                            <td className="px-3 py-1.5 border-r border-black">{x.activity || 'N/A'}</td>
                            <td className="px-3 py-1.5 text-center">{x.pe || 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Category-I (iv) Examination Duties */}
                  <div className="space-y-2 mt-4">
                    <h5 className="text-[11px] font-extrabold uppercase text-slate-800">Section IV: Examination Duties</h5>
                    <table className="w-full text-left text-[10px] border-collapse border border-black">
                      <thead>
                        <tr className="bg-slate-50 border-b border-black text-black font-bold">
                          <th className="px-3 py-1.5 w-12 text-center border-r border-black">S.No</th>
                          <th className="px-3 py-1.5 border-r border-black">Semester / Session</th>
                          <th className="px-3 py-1.5 border-r border-black">Activity Description</th>
                          <th className="px-3 py-1.5 text-center w-28">Score / Extent</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-black">
                        {(!printTarget.cat1iv || printTarget.cat1iv.length === 0) ? (
                          <tr><td colSpan={4} className="text-center py-2 text-slate-500">No records added.</td></tr>
                        ) : printTarget.cat1iv.map((x: any, idx: number) => (
                          <tr key={idx}>
                            <td className="px-3 py-1.5 text-center border-r border-black">{idx + 1}</td>
                            <td className="px-3 py-1.5 border-r border-black">{x.sas || 'N/A'}</td>
                            <td className="px-3 py-1.5 border-r border-black">{x.activity || 'N/A'}</td>
                            <td className="px-3 py-1.5 text-center">{x.pe || 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Category-I (v) Co-curricular, extension and professional development */}
                  <div className="space-y-2 mt-4">
                    <h5 className="text-[11px] font-extrabold uppercase text-slate-800">Section V: Co-curricular, Extension & Professional Development</h5>
                    <table className="w-full text-left text-[10px] border-collapse border border-black">
                      <thead>
                        <tr className="bg-slate-50 border-b border-black text-black font-bold">
                          <th className="px-3 py-1.5 w-12 text-center border-r border-black">S.No</th>
                          <th className="px-3 py-1.5 border-r border-black">Semester / Session</th>
                          <th className="px-3 py-1.5 border-r border-black">Activity Description</th>
                          <th className="px-3 py-1.5 text-center w-28">Score / Extent</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-black">
                        {(!printTarget.cat1v || printTarget.cat1v.length === 0) ? (
                          <tr><td colSpan={4} className="text-center py-2 text-slate-500">No records added.</td></tr>
                        ) : printTarget.cat1v.map((x: any, idx: number) => (
                          <tr key={idx}>
                            <td className="px-3 py-1.5 text-center border-r border-black">{idx + 1}</td>
                            <td className="px-3 py-1.5 border-r border-black">{x.sas || 'N/A'}</td>
                            <td className="px-3 py-1.5 border-r border-black">{x.activity || 'N/A'}</td>
                            <td className="px-3 py-1.5 text-center">{x.pe || 0}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="font-extrabold text-[11px] text-right mt-4 pt-2 border-t border-black uppercase">
                    Annexure I Total Marks: {calculatePrintAnnexureITotal(printTarget)}/100
                  </div>
                </div>
              </div>

              {/* Part B: Annexure II */}
              <div className="page-break pt-8 space-y-6">
                <h4 className="text-sm font-extrabold border-b pb-1 uppercase">Part B: Annexure II (Research Contribution)</h4>
                <table className="w-full text-left text-xs border-collapse border border-black">
                  <thead>
                    <tr className="bg-slate-50 border-b border-black text-black font-bold">
                      <th className="px-4 py-2 w-16 text-center border-r border-black">S.No</th>
                      <th className="px-4 py-2 border-r border-black">Particulars</th>
                      <th className="px-4 py-2 text-center w-28">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-black">
                    {cat2Categories.filter(c => !c.headerOnly).map((cat, idx) => {
                      const valueObj = (printTarget.cat2 || []).find((c: any) => String(c.sno) === String(cat.key));
                      const currentVal = valueObj ? valueObj.score : '0';
                      return (
                        <tr key={cat.key}>
                          <td className="px-4 py-2 text-center border-r border-black">{idx + 1}</td>
                          <td className="px-4 py-2 border-r border-black">{cat.particulars}</td>
                          <td className="px-4 py-2 text-center">{currentVal}</td>
                        </tr>
                      );
                    })}
                    <tr className="font-bold border-t border-black">
                      <td colSpan={2} className="px-4 py-2 text-right border-r border-black">Annexure II Total Points:</td>
                      <td className="px-4 py-2 text-center">{calculatePrintAnnexureIITotal(printTarget)} pts</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Part C: Annexure III */}
              <div className="page-break pt-8 space-y-6">
                <h4 className="text-sm font-extrabold border-b pb-1 uppercase">Part C: Annexure III (Self Assessment)</h4>
                <table className="w-full text-left text-xs border-collapse border border-black">
                  <thead>
                    <tr className="bg-slate-50 border-b border-black text-black font-bold">
                      <th className="px-4 py-2 w-16 text-center border-r border-black">S.No</th>
                      <th className="px-4 py-2 border-r border-black">Particulars</th>
                      <th className="px-4 py-2 text-center w-28">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-black">
                    {cat3Categories.map((cat, idx) => {
                      const valueObj = (printTarget.cat3 || []).find((c: any) => String(c.sno) === String(cat.key));
                      const currentVal = valueObj ? valueObj.score : '0';
                      return (
                        <tr key={cat.key}>
                          <td className="px-4 py-2 text-center border-r border-black">{idx + 1}</td>
                          <td className="px-4 py-2 border-r border-black">{cat.particulars}</td>
                          <td className="px-4 py-2 text-center">{currentVal}</td>
                        </tr>
                      );
                    })}
                    <tr className="font-bold border-t border-black">
                      <td colSpan={2} className="px-4 py-2 text-right border-r border-black">Annexure III Total Points:</td>
                      <td className="px-4 py-2 text-center">{calculatePrintAnnexureIIITotal(printTarget)} pts</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Part D: CR */}
              <div className="page-break pt-8 space-y-6">
                <h4 className="text-sm font-extrabold border-b pb-1 uppercase">Part D: Confidential Report (CR)</h4>
                <table className="w-full text-left text-xs border-collapse border border-black">
                  <thead>
                    <tr className="bg-slate-50 border-b border-black text-black font-bold">
                      <th className="px-4 py-2 w-16 text-center border-r border-black">S.No</th>
                      <th className="px-4 py-2 border-r border-black">Parameter</th>
                      <th className="px-4 py-2 w-28 text-center">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-black">
                    {confidentialParameters.map((param, idx) => (
                      <tr key={param.key}>
                        <td className="px-4 py-2 text-center border-r border-black">{idx + 1}</td>
                        <td className="px-4 py-2 border-r border-black">{param.label}</td>
                        <td className="px-4 py-2 text-center">{printTarget.confidential?.[param.key] ?? 'N/A'}</td>
                      </tr>
                    ))}
                    <tr className="font-bold border-t border-black">
                      <td colSpan={2} className="px-4 py-2 text-right border-r border-black">Total CR Marks:</td>
                      <td className="px-4 py-2 text-center">{printTarget.confidential?.total_marks ?? 0}/70</td>
                    </tr>
                  </tbody>
                </table>
                {printTarget.confidential?.remarks && (
                  <div className="border border-black p-4 rounded text-xs italic bg-white">
                    <strong>HOD Remarks:</strong> "{printTarget.confidential.remarks}"
                  </div>
                )}
              </div>

              {/* Part E: Summary Sheet */}
              <div className="page-break pt-8 space-y-6 text-black">
                <div className="text-center space-y-1">
                  <h1 className="text-2xl font-black tracking-wide uppercase">IPS Academy</h1>
                  <h2 className="text-sm font-extrabold uppercase">Institute of Engineering & Science</h2>
                  <h3 className="text-sm font-bold tracking-widest underline uppercase mt-2">Self Appraisal Summary Sheet</h3>
                </div>

                <table className="w-full text-xs font-bold border-collapse border border-black mt-6">
                  <tbody>
                    <tr className="border-b border-black">
                      <td className="px-4 py-3 bg-slate-50 w-44 border-r border-black">Department :</td>
                      <td className="px-4 py-3">{printTarget.department || 'N/A'}</td>
                    </tr>
                    <tr className="border-b border-black">
                      <td className="px-4 py-3 bg-slate-50 border-r border-black">Name :</td>
                      <td className="px-4 py-3 uppercase">{printTarget.faculty_name || 'N/A'}</td>
                    </tr>
                    <tr className="border-b border-black">
                      <td className="px-4 py-3 bg-slate-50 border-r border-black">Date of Birth :</td>
                      <td className="px-4 py-3">{staffCache[printTarget.faculty_computer_code]?.staff?.date_of_birth ? new Date(staffCache[printTarget.faculty_computer_code].staff.date_of_birth).toLocaleDateString('en-GB') : 'N/A'}</td>
                    </tr>
                    <tr className="border-b border-black">
                      <td className="px-4 py-3 bg-slate-50 border-r border-black">Computer Code :</td>
                      <td className="px-4 py-3 font-mono">{printTarget.faculty_computer_code}</td>
                    </tr>
                    <tr className="border-b border-black">
                      <td className="px-4 py-3 bg-slate-50 border-r border-black">Designation :</td>
                      <td className="px-4 py-3 uppercase">{printTarget.designation || 'N/A'}</td>
                    </tr>
                    <tr className="border-b border-black">
                      <td className="px-4 py-3 bg-slate-50 border-r border-black">Highest Qualification :</td>
                      <td className="px-4 py-3 uppercase">{staffCache[printTarget.faculty_computer_code]?.details?.qualification || 'Not specified'}</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 bg-slate-50 border-r border-black">Total Experience at IPSA :</td>
                      <td className="px-4 py-3">{staffCache[printTarget.faculty_computer_code]?.staff?.date_join ? calculateExperience(staffCache[printTarget.faculty_computer_code].staff.date_join) : 'N/A'}</td>
                    </tr>
                  </tbody>
                </table>

                <div className="text-center font-bold text-xs py-2">
                  For Office Use Only
                </div>

                <div className="border border-black p-4 rounded space-y-3 text-xs font-bold bg-white">
                  <div className="flex justify-between border-b pb-2">
                    <span>G. Overall 360° feedback score on a 100 point scale =</span>
                    <span>{calculatePrintAnnexureITotal(printTarget)}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span>Overall 360° feedback score on a 10 point scale =</span>
                    <span>{(calculatePrintAnnexureITotal(printTarget) / 10).toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span>API Score from annexure II =</span>
                    <span>{calculatePrintAnnexureIITotal(printTarget)}</span>
                  </div>
                  {printTarget.confidential?.status === 'Submitted' && (
                    <div className="flex justify-between border-b pb-2">
                      <span>CR Score (Confidential marks out of 70) =</span>
                      <span>{printTarget.confidential.total_marks}</span>
                    </div>
                  )}
                  <div className="flex justify-between pt-1 text-sm font-black text-indigo-700">
                    <span>Overall Final Score =</span>
                    <span>{(
                      Number((calculatePrintAnnexureITotal(printTarget) / 10).toFixed(1)) +
                      Number(calculatePrintAnnexureIITotal(printTarget)) +
                      (printTarget.confidential?.status === 'Submitted' ? Number(printTarget.confidential.total_marks) : 0)
                    ).toFixed(1)}</span>
                  </div>
                </div>

                <div className="pt-4 text-xs font-bold">
                  <div className="flex items-center gap-1">
                    <span>Recommended for award of increment :</span>
                    <span className="underline uppercase tracking-wider text-sm font-black">
                      {(() => {
                        const finalScore = Number((calculatePrintAnnexureITotal(printTarget) / 10).toFixed(1)) +
                          Number(calculatePrintAnnexureIITotal(printTarget)) +
                          (printTarget.confidential?.status === 'Submitted' ? Number(printTarget.confidential.total_marks) : 0);
                        return finalScore >= 60 ? 'Yes' : 'No';
                      })()}
                    </span>
                  </div>
                </div>

                <div className="pt-16 space-y-12">
                  <div className="space-y-4">
                    <div className="text-xs font-bold">Name & Signature of Committee members at Institute level</div>
                    <div className="grid grid-cols-2 gap-y-6 gap-x-12 text-xs font-bold">
                      <div>(i) ___________________________</div>
                      <div>(ii) ___________________________</div>
                      <div>(iii) ___________________________</div>
                      <div>(iv) ___________________________</div>
                    </div>
                  </div>

                  <div className="pt-8 text-xs font-bold">
                    <div>Principal</div>
                    <div>IPS Academy, IES</div>
                  </div>
                </div>
              </div>
            </div>
          )}
          {/* Print Summary Sheet */}
          { printType === 'summary' && (
            <div className="space-y-6 text-black">
              <div className="text-center space-y-1">
                <h1 className="text-2xl font-black tracking-wide uppercase">IPS Academy</h1>
                <h2 className="text-sm font-extrabold uppercase">Institute of Engineering & Science</h2>
                <h3 className="text-sm font-bold tracking-widest underline uppercase mt-2">Self Appraisal Summary Sheet</h3>
              </div>

              <table className="w-full text-xs font-bold border-collapse border border-black mt-6">
                <tbody>
                  <tr className="border-b border-black">
                    <td className="px-4 py-3 bg-slate-50 w-44 border-r border-black">Department :</td>
                    <td className="px-4 py-3">{printTarget.department || 'N/A'}</td>
                  </tr>
                  <tr className="border-b border-black">
                    <td className="px-4 py-3 bg-slate-50 border-r border-black">Name :</td>
                    <td className="px-4 py-3 uppercase">{printTarget.faculty_name || 'N/A'}</td>
                  </tr>
                  <tr className="border-b border-black">
                    <td className="px-4 py-3 bg-slate-50 border-r border-black">Date of Birth :</td>
                    <td className="px-4 py-3">{staffCache[printTarget.faculty_computer_code]?.staff?.date_of_birth ? new Date(staffCache[printTarget.faculty_computer_code].staff.date_of_birth).toLocaleDateString('en-GB') : 'N/A'}</td>
                  </tr>
                  <tr className="border-b border-black">
                    <td className="px-4 py-3 bg-slate-50 border-r border-black">Computer Code :</td>
                    <td className="px-4 py-3 font-mono">{printTarget.faculty_computer_code}</td>
                  </tr>
                  <tr className="border-b border-black">
                    <td className="px-4 py-3 bg-slate-50 border-r border-black">Designation :</td>
                    <td className="px-4 py-3 uppercase">{printTarget.designation || 'N/A'}</td>
                  </tr>
                  <tr className="border-b border-black">
                    <td className="px-4 py-3 bg-slate-50 border-r border-black">Highest Qualification :</td>
                    <td className="px-4 py-3 uppercase">{staffCache[printTarget.faculty_computer_code]?.details?.qualification || 'Not specified'}</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 bg-slate-50 border-r border-black">Total Experience at IPSA :</td>
                    <td className="px-4 py-3">{staffCache[printTarget.faculty_computer_code]?.staff?.date_join ? calculateExperience(staffCache[printTarget.faculty_computer_code].staff.date_join) : 'N/A'}</td>
                  </tr>
                </tbody>
              </table>

              <div className="text-center font-bold text-xs py-2">
                For Office Use Only
              </div>

              <div className="border border-black p-4 rounded space-y-3 text-xs font-bold bg-white">
                <div className="flex justify-between border-b pb-2">
                  <span>G. Overall 360° feedback score on a 100 point scale =</span>
                  <span>{calculatePrintAnnexureITotal(printTarget)}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span>Overall 360° feedback score on a 10 point scale =</span>
                  <span>{(calculatePrintAnnexureITotal(printTarget) / 10).toFixed(1)}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span>API Score from annexure II =</span>
                  <span>{calculatePrintAnnexureIITotal(printTarget)}</span>
                </div>
                {printTarget.confidential?.status === 'Submitted' && (
                  <div className="flex justify-between border-b pb-2">
                    <span>CR Score (Confidential marks out of 70) =</span>
                    <span>{printTarget.confidential.total_marks}</span>
                  </div>
                )}
                <div className="flex justify-between pt-1 text-sm font-black text-indigo-700">
                  <span>Overall Final Score =</span>
                  <span>{(
                    Number((calculatePrintAnnexureITotal(printTarget) / 10).toFixed(1)) +
                    Number(calculatePrintAnnexureIITotal(printTarget)) +
                    (printTarget.confidential?.status === 'Submitted' ? Number(printTarget.confidential.total_marks) : 0)
                  ).toFixed(1)}</span>
                </div>
              </div>

              <div className="pt-4 text-xs font-bold">
                Recommended for award of increment : Yes / No
              </div>

              <div className="pt-16 space-y-12">
                <div className="space-y-4">
                  <div className="text-xs font-bold">Name & Signature of Committee members at Institute level</div>
                  <div className="text-xs font-bold space-y-4 pt-2">
                    <div>(i)</div>
                    <div>(ii)</div>
                    <div>(iii)</div>
                    <div>(iv)</div>
                  </div>
                </div>

                <div className="pt-12 text-xs font-bold">
                  <div>Principal</div>
                  <div>IPS Academy, IES</div>
                </div>
              </div>
            </div>
          )}
      </div>
    )}

      {/* Global Toast Notification */}
      {toast && <Toast message={toast.msg} type={toast.type} onClose={() => setToast(null)} />}

    </div>
  );
}
