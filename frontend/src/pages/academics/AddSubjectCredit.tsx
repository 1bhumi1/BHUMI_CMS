import React, { useState, useEffect } from 'react';
import { useAuth } from '../../lib/AuthContext';
import { Navigate } from 'react-router-dom';
import { 
  Award, RotateCcw, Save, Calendar, BookOpen, Layers, Info, AlertCircle 
} from 'lucide-react';
import Toast from '../../components/Toast';
import { api } from '../../lib/api';
import { useAcademicSession } from '../../lib/AcademicSessionContext';

// Define the Subject structure coming from backend
type SubjectCreditItem = {
  college_sub_code: string;
  subject_name: string;
  type: string;
  totalCredit: number;
  endSem: number;
  mst: number;
  assignment: number;
  labwork_sessional: number;
};

type CreditConfig = {
  totalCredit: number | '';
  endSem: number | '';
  mst: number | '';
  assignment: number | '';
  labwork_sessional: number | '';
};

type SemesterConfigs = Record<string, CreditConfig>;

const AddSubjectCredit = () => {
  const { role } = useAuth();
  const { currentSession } = useAcademicSession();

  // Route Guard: Only HOD can access
  if (role !== 'HOD') {
    return <Navigate to="/unauthorized" replace />;
  }

  // Local state variables
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [selectedSemester, setSelectedSemester] = useState<string>('');
  const [subjectsList, setSubjectsList] = useState<SubjectCreditItem[]>([]);
  const [configs, setConfigs] = useState<SemesterConfigs>({});
  const [loading, setLoading] = useState(false);
  const [dbSessions, setDbSessions] = useState<{ id: number; name: string }[]>([]);

  // Resolve global session string to database session ID
  const matchSessionToDBId = (sessionStr: string, sessionsList: { id: number; name: string }[]) => {
    if (!sessionStr) return null;
    const match = sessionStr.match(/^(\d{4})-(\d{4})/);
    if (!match) return null;
    const startYear = match[1];
    const endYearShort = match[2].slice(2);
    const targetName = `${startYear}-${endYearShort}`;
    const found = sessionsList.find(s => s.name === targetName);
    return found ? found.id : null;
  };

  // Clear selected semester when academic session changes
  useEffect(() => {
    setSelectedSemester('');
  }, [currentSession]);

  // Load database sessions on mount
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await api.get('/academic-sessions/dropdown');
        setDbSessions(res.data?.data?.sessions || []);
      } catch (e) {
        console.error('Failed to load academic sessions:', e);
      }
    };
    fetchSessions();
  }, []);

  const getAvailableSemesters = (session: string) => {
    if (!session) return [];
    if (session.includes('Jan-Jun') || session.includes('Jan-June')) {
      return ['2', '4', '6', '8'];
    }
    if (session.includes('July-Dec')) {
      return ['1', '3', '5', '7'];
    }
    return ['1', '2', '3', '4', '5', '6', '7', '8'];
  };

  const availableSemesters = getAvailableSemesters(currentSession);

  // Fetch subject configs from backend database
  const fetchConfigs = async () => {
    if (!selectedSemester || dbSessions.length === 0) {
      setSubjectsList([]);
      setConfigs({});
      return;
    }
    setLoading(true);
    try {
      const sessionId = matchSessionToDBId(currentSession, dbSessions);
      if (!sessionId) {
        setToast({ message: 'Invalid academic session.', type: 'error' });
        setLoading(false);
        return;
      }

      const res = await api.get('/academic/subject-credits', {
        params: {
          semester: Number(selectedSemester),
          academic_session: sessionId
        }
      });

      const list: SubjectCreditItem[] = res.data?.data || [];
      setSubjectsList(list);

      const initialConfigs: SemesterConfigs = {};
      list.forEach(item => {
        const itemType = item.type.toLowerCase();
        const hasTheory = itemType.includes('theory') || itemType.includes('tutorial') || itemType.includes('project') || itemType.includes('seminar');
        const hasPractical = itemType.includes('practical');
        
        if (hasTheory) {
          initialConfigs[item.college_sub_code + '_Theory'] = {
            totalCredit: item.totalCredit,
            endSem: item.endSem,
            mst: item.mst,
            assignment: item.assignment,
            labwork_sessional: ''
          };
        }
        if (hasPractical) {
          initialConfigs[item.college_sub_code + '_Practical'] = {
            totalCredit: item.totalCredit,
            endSem: item.endSem,
            mst: '',
            assignment: '',
            labwork_sessional: item.labwork_sessional
          };
        }
      });
      setConfigs(initialConfigs);
    } catch (e) {
      console.error('Failed to load credit configurations:', e);
      setToast({ message: 'Failed to load configurations from database', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, [selectedSemester, currentSession, dbSessions]);

  // Helper function to calculate total credits dynamically
  const calculateTotal = (config: CreditConfig, type: 'Theory' | 'Practical'): number | '' => {
    const endSem = config.endSem !== '' ? Number(config.endSem) : 0;
    if (type === 'Theory') {
      const mst = config.mst !== '' ? Number(config.mst) : 0;
      const assignment = config.assignment !== '' ? Number(config.assignment) : 0;
      return endSem + mst + assignment;
    } else {
      const labwork = config.labwork_sessional !== '' ? Number(config.labwork_sessional) : 0;
      return endSem + labwork;
    }
  };

  // Handle configuration changes with validation checks
  const handleConfigChange = (
    collegeSubCode: string, 
    field: keyof CreditConfig, 
    value: string, 
    type: 'Theory' | 'Practical'
  ) => {
    const configKey = collegeSubCode + '_' + type;
    if (value === '') {
      setConfigs(prev => {
        const current = prev[configKey] || { totalCredit: '', endSem: '', mst: '', assignment: '', labwork_sessional: '' };
        const updated = { ...current, [field]: '' };
        updated.totalCredit = calculateTotal(updated, type);
        return {
          ...prev,
          [configKey]: updated
        };
      });
      return;
    }

    const num = Number(value);
    // Validation: prevent negative numbers or invalid numeric characters
    if (isNaN(num) || num < 0) return;

    // Apply upper bounds
    let max = 100;
    if (type === 'Theory') {
      if (field === 'mst' || field === 'assignment') {
        max = 30;
      }
    } else {
      if (field === 'labwork_sessional') {
        max = 100;
      }
    }

    if (num > max) {
      setToast({ message: `Max limit exceeded! Maximum allowed for this field is ${max}.`, type: 'error' });
      return;
    }

    setConfigs(prev => {
      const current = prev[configKey] || { totalCredit: '', endSem: '', mst: '', assignment: '', labwork_sessional: '' };
      const updated = { ...current, [field]: num };
      updated.totalCredit = calculateTotal(updated, type);
      return {
        ...prev,
        [configKey]: updated
      };
    });
  };

  const theorySubjects = subjectsList.filter(s => {
    const t = s.type.toLowerCase();
    return t.includes('theory') || t.includes('tutorial') || t.includes('project') || t.includes('seminar');
  });
  
  const practicalSubjects = subjectsList.filter(s => {
    const t = s.type.toLowerCase();
    return t.includes('practical');
  });

  // Action handlers
  const handleReset = () => {
    fetchConfigs();
    setToast({ message: 'Configuration reset successfully', type: 'success' });
  };

  const handleSave = async () => {
    let isValid = true;
    const saveList: any[] = [];

    for (const sub of subjectsList) {
      const subType = sub.type.toLowerCase();
      const hasTheory = subType.includes('theory') || subType.includes('tutorial') || subType.includes('project') || subType.includes('seminar');
      const hasPractical = subType.includes('practical');

      if (hasTheory) {
        const cfg = configs[sub.college_sub_code + '_Theory'];
        if (!cfg || cfg.totalCredit === '' || cfg.endSem === '' || cfg.mst === '' || cfg.assignment === '') {
          isValid = false;
          break;
        }

        // Validation: Total Credits = End Sem + MST + Assignment
        const sum = Number(cfg.endSem) + Number(cfg.mst) + Number(cfg.assignment);
        if (Number(cfg.totalCredit) !== sum) {
          setToast({
            message: `Validation failed: Total Credits (${cfg.totalCredit}) must equal End Sem (${cfg.endSem}) + MST (${cfg.mst}) + Assignment (${cfg.assignment}) for subject ${sub.subject_name} (Theory).`,
            type: 'error'
          });
          return;
        }

        saveList.push({
          college_sub_code: sub.college_sub_code,
          totalCredit: Number(cfg.totalCredit),
          endSem: Number(cfg.endSem),
          mst: Number(cfg.mst),
          assignment: Number(cfg.assignment),
          labwork_sessional: 0,
          type: 'Theory'
        });
      }

      if (hasPractical) {
        const cfg = configs[sub.college_sub_code + '_Practical'];
        if (!cfg || cfg.totalCredit === '' || cfg.endSem === '' || cfg.labwork_sessional === '') {
          isValid = false;
          break;
        }

        // Validation: Total Credits = End Sem + Lab Work / Sessional
        const sum = Number(cfg.endSem) + Number(cfg.labwork_sessional);
        if (Number(cfg.totalCredit) !== sum) {
          setToast({
            message: `Validation failed: Total Credits (${cfg.totalCredit}) must equal End Sem (${cfg.endSem}) + Lab Work / Sessional (${cfg.labwork_sessional}) for subject ${sub.subject_name} (Practical).`,
            type: 'error'
          });
          return;
        }

        saveList.push({
          college_sub_code: sub.college_sub_code,
          totalCredit: Number(cfg.totalCredit),
          endSem: Number(cfg.endSem),
          mst: 0,
          assignment: 0,
          labwork_sessional: Number(cfg.labwork_sessional),
          type: 'Practical'
        });
      }
    }

    if (!isValid) {
      setToast({ message: 'Please fill in all credit and marks configuration values.', type: 'error' });
      return;
    }

    try {
      const sessionId = matchSessionToDBId(currentSession, dbSessions);
      if (!sessionId) return;

      await api.post('/academic/subject-credits/bulk', {
        semester: Number(selectedSemester),
        academic_session: sessionId,
        configs: saveList
      });

      setToast({ message: 'Subject credits and schema configuration saved successfully', type: 'success' });
      fetchConfigs();
    } catch (e: any) {
      console.error('Failed to save bulk credits:', e);
      setToast({ message: e.response?.data?.detail || 'Error saving credit configurations to database', type: 'error' });
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-50/50">
      <div className="p-8 max-w-7xl mx-auto space-y-8 font-sans">
        {/* Top Header Section */}
        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2.5">
              <Award className="text-blue-600 w-7 h-7" /> Configure Subject Credits
            </h1>
            <p className="text-sm text-slate-500 mt-1">Configure credit structure and marks weighting schemas for active subjects</p>
          </div>
          <div className="flex items-center gap-2.5 px-4 py-2 bg-white border border-slate-200 rounded-2xl shadow-sm text-xs font-bold text-slate-600">
            <Calendar size={14} className="text-slate-500" />
            <span>Active Session: <strong className="text-blue-600">{currentSession}</strong></span>
          </div>
        </div>

        {/* Card 1: Semester Selection */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                <Layers size={18} />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">Select Semester *</label>
                <p className="text-xxs text-slate-400 mt-0.5">Semesters filtered by selected academic session</p>
              </div>
            </div>
            <div className="flex-1 max-w-xs">
              <select
                value={selectedSemester}
                onChange={(e) => setSelectedSemester(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 focus:border-blue-500 rounded-2xl text-sm font-semibold text-slate-700 focus:outline-none focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all cursor-pointer"
              >
                <option value="">Choose a Semester</option>
                {availableSemesters.map(sem => (
                  <option key={sem} value={sem}>Semester {sem}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Conditional Configuration Tables */}
        {loading ? (
          <div className="p-8 text-center text-slate-400 font-medium">Loading configurations from database...</div>
        ) : !selectedSemester ? (
          /* Empty State: No Semester Selected */
          <div className="flex flex-col items-center justify-center py-16 bg-white border border-dashed border-slate-300 rounded-3xl text-center p-6 shadow-sm">
            <div className="w-14 h-14 bg-slate-100 rounded-full flex items-center justify-center text-slate-400 mb-4">
              <Info size={28} />
            </div>
            <h3 className="text-base font-bold text-slate-700">Configure Semester Credits</h3>
            <p className="text-sm text-slate-400 max-w-sm mt-1.5 leading-relaxed">
              Please select a semester from the dropdown above to load and configure subject credits.
            </p>
          </div>
        ) : subjectsList.length === 0 ? (
          /* Empty State: No Subjects Found */
          <div className="flex flex-col items-center justify-center py-16 bg-white border border-slate-200 rounded-3xl text-center p-6 shadow-sm">
            <div className="w-14 h-14 bg-amber-50 text-amber-500 rounded-full flex items-center justify-center mb-4">
              <AlertCircle size={28} />
            </div>
            <h3 className="text-base font-bold text-slate-700">No Subjects Found</h3>
            <p className="text-sm text-slate-400 max-w-sm mt-1.5 leading-relaxed">
              No subjects exist for Semester {selectedSemester} in the selected academic session. Please add subjects first.
            </p>
          </div>
        ) : (
          <div className="space-y-8 animate-fadeIn">
            {/* Card 2: Theory Subjects */}
            {theorySubjects.length > 0 && (
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-200 bg-slate-50/50 flex items-center gap-3">
                  <div className="w-2.5 h-2.5 bg-blue-600 rounded-full"></div>
                  <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
                    <BookOpen size={18} className="text-slate-500" /> Theory Subjects Configuration
                  </h2>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-xxs font-bold text-slate-500 uppercase tracking-wider bg-slate-50/30 sticky top-0 z-10">
                        <th className="px-6 py-4 w-16 text-center">S.No</th>
                        <th className="px-6 py-4 w-36">Subject Code</th>
                        <th className="px-6 py-4 min-w-[200px]">Subject Name</th>
                        <th className="px-6 py-4 w-28 text-center">Total Credits</th>
                        <th className="px-6 py-4 w-28 text-center">End Sem Marks</th>
                        <th className="px-6 py-4 w-28 text-center">MST Marks</th>
                        <th className="px-6 py-4 w-32 text-center">Quiz / Assignment</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-sm">
                      {theorySubjects.map((sub, idx) => {
                        const config = configs[sub.college_sub_code + '_Theory'] || { totalCredit: '', endSem: '', mst: '', assignment: '', labwork_sessional: '' };
                        return (
                          <tr key={sub.college_sub_code} className="hover:bg-slate-50/40 transition-colors">
                            <td className="px-6 py-4 text-center font-bold text-slate-400">{idx + 1}</td>
                            <td className="px-6 py-4 font-bold text-blue-600">{sub.college_sub_code}</td>
                            <td className="px-6 py-4 font-semibold text-slate-800">{sub.subject_name}</td>
                            <td className="px-6 py-4">
                              <input
                                type="number"
                                min={0}
                                max={200}
                                value={config.totalCredit}
                                readOnly
                                className="w-16 mx-auto block text-center px-2 py-1.5 border border-slate-200 rounded-xl font-bold text-slate-700 bg-slate-100/70 cursor-not-allowed focus:outline-none text-xs"
                              />
                            </td>
                            <td className="px-6 py-4">
                              <input
                                type="number"
                                min={0}
                                max={100}
                                value={config.endSem}
                                onChange={(e) => handleConfigChange(sub.college_sub_code, 'endSem', e.target.value, 'Theory')}
                                className="w-20 mx-auto block text-center px-2 py-1.5 border border-slate-200 focus:border-blue-500 rounded-xl font-bold text-slate-700 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-500/10 transition-all text-xs"
                              />
                            </td>
                            <td className="px-6 py-4">
                              <input
                                type="number"
                                min={0}
                                max={30}
                                value={config.mst}
                                onChange={(e) => handleConfigChange(sub.college_sub_code, 'mst', e.target.value, 'Theory')}
                                className="w-18 mx-auto block text-center px-2 py-1.5 border border-slate-200 focus:border-blue-500 rounded-xl font-bold text-slate-700 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-500/10 transition-all text-xs"
                              />
                            </td>
                            <td className="px-6 py-4">
                              <input
                                type="number"
                                min={0}
                                max={30}
                                value={config.assignment}
                                onChange={(e) => handleConfigChange(sub.college_sub_code, 'assignment', e.target.value, 'Theory')}
                                className="w-18 mx-auto block text-center px-2 py-1.5 border border-slate-200 focus:border-blue-500 rounded-xl font-bold text-slate-700 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-500/10 transition-all text-xs"
                              />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Card 3: Practical Subjects */}
            {practicalSubjects.length > 0 && (
              <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden animate-fadeIn">
                <div className="p-6 border-b border-slate-200 bg-slate-50/50 flex items-center gap-3">
                  <div className="w-2.5 h-2.5 bg-emerald-600 rounded-full"></div>
                  <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
                    <BookOpen size={18} className="text-slate-500" /> Practical Subjects Configuration
                  </h2>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-xxs font-bold text-slate-500 uppercase tracking-wider bg-slate-50/30 sticky top-0 z-10">
                        <th className="px-6 py-4 w-16 text-center">S.No</th>
                        <th className="px-6 py-4 w-36">Subject Code</th>
                        <th className="px-6 py-4 min-w-[200px]">Subject Name</th>
                        <th className="px-6 py-4 w-28 text-center">Total Credits</th>
                        <th className="px-6 py-4 w-28 text-center">End Sem Marks</th>
                        <th className="px-6 py-4 w-36 text-center">Lab Work / Sessional</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-sm">
                      {practicalSubjects.map((sub, idx) => {
                        const config = configs[sub.college_sub_code + '_Practical'] || { totalCredit: '', endSem: '', mst: '', assignment: '', labwork_sessional: '' };
                        return (
                          <tr key={sub.college_sub_code} className="hover:bg-slate-50/40 transition-colors">
                            <td className="px-6 py-4 text-center font-bold text-slate-400">{idx + 1}</td>
                            <td className="px-6 py-4 font-bold text-emerald-600">{sub.college_sub_code}</td>
                            <td className="px-6 py-4 font-semibold text-slate-800">{sub.subject_name}</td>
                            <td className="px-6 py-4">
                              <input
                                type="number"
                                min={0}
                                max={200}
                                value={config.totalCredit}
                                readOnly
                                className="w-16 mx-auto block text-center px-2 py-1.5 border border-slate-200 rounded-xl font-bold text-slate-700 bg-slate-100/70 cursor-not-allowed focus:outline-none text-xs"
                              />
                            </td>
                            <td className="px-6 py-4">
                              <input
                                type="number"
                                min={0}
                                max={100}
                                value={config.endSem}
                                onChange={(e) => handleConfigChange(sub.college_sub_code, 'endSem', e.target.value, 'Practical')}
                                className="w-20 mx-auto block text-center px-2 py-1.5 border border-slate-200 focus:border-blue-500 rounded-xl font-bold text-slate-700 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-500/10 transition-all text-xs"
                              />
                            </td>
                            <td className="px-6 py-4">
                              <input
                                type="number"
                                min={0}
                                max={100}
                                value={config.labwork_sessional}
                                onChange={(e) => handleConfigChange(sub.college_sub_code, 'labwork_sessional', e.target.value, 'Practical')}
                                className="w-20 mx-auto block text-center px-2 py-1.5 border border-emerald-500 focus:border-emerald-500 rounded-xl font-bold text-slate-700 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-4 focus:ring-emerald-500/10 transition-all text-xs"
                              />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Bottom Actions Row */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
              <button
                type="button"
                onClick={handleReset}
                className="flex items-center gap-2 px-5 py-2.5 border border-slate-200 text-slate-700 hover:bg-slate-100 rounded-2xl text-xs font-bold transition-all duration-200 active:scale-98"
              >
                <RotateCcw size={14} /> Reset
              </button>
              <button
                type="button"
                onClick={handleSave}
                className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl text-xs font-bold shadow-md shadow-blue-500/20 transition-all duration-200 active:scale-98"
              >
                <Save size={14} /> Save Credits
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AddSubjectCredit;
