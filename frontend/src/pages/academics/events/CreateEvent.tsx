import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navigate, useNavigate } from 'react-router-dom';
import { api } from '../../../lib/api';
import { useAuth } from '../../../lib/AuthContext';
import { Calendar, Loader2, Save, ArrowLeft, AlertCircle } from 'lucide-react';

const eventFormSchema = z.object({
  academic_session_id: z.coerce.number().min(1, 'Academic Session is required'),
  department_id: z.coerce.number().nullable().optional(),
  program_id: z.coerce.number().nullable().optional(),
  semester: z.coerce.number().nullable().optional(),
  title: z.string().min(1, 'Event Title is required').max(255, 'Cannot exceed 255 characters'),
  event_type: z.string().min(1, 'Event Type is required'),
  description: z.string().min(1, 'Description is required'),
  start_date: z.string().min(1, 'Start Date is required'),
  end_date: z.string().min(1, 'End Date is required'),
  venue: z.string().min(1, 'Venue is required').max(255),
  max_seats: z.coerce.number().min(1, 'Seats must be at least 1'),
  registration_deadline: z.string().min(1, 'Registration deadline is required'),
  poster_url: z.string().url('Must be a valid URL').or(z.literal('')).optional().nullable(),
  audience: z.string().min(1, 'Audience selection is required'),
  registration_required: z.coerce.number().default(1),
  fee_required: z.coerce.number().default(0),
  fee_amount: z.coerce.number().default(0.00),
  status: z.string().default('Draft')
});

type EventFormValues = z.infer<typeof eventFormSchema>;

const defaultValues: EventFormValues = {
  academic_session_id: 0,
  department_id: null,
  program_id: null,
  semester: null,
  title: '',
  event_type: '',
  description: '',
  start_date: '',
  end_date: '',
  venue: '',
  max_seats: 100,
  registration_deadline: '',
  poster_url: '',
  audience: 'Students',
  registration_required: 1,
  fee_required: 0,
  fee_amount: 0,
  status: 'Draft'
};

const EVENT_TYPES = [
  'Workshop', 'Seminar', 'Webinar', 'Guest Lecture',
  'Industrial Visit', 'Hackathon', 'Bootcamp', 'Training Program'
];

export default function CreateEvent() {
  const { role } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  if (role !== 'HOD') {
    return <Navigate to="/unauthorized" replace />;
  }

  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting }
  } = useForm<EventFormValues>({
    resolver: zodResolver(eventFormSchema),
    defaultValues
  });

  const watchedFeeRequired = watch('fee_required');
  const watchedRegRequired = watch('registration_required');

  // Load dropdown lists
  const { data: sessions = [] } = useQuery({
    queryKey: ['academic-sessions-all'],
    queryFn: async () => {
      const res = await api.get('/academic/academic-sessions');
      return res.data?.data || [];
    }
  });

  const { data: departments = [] } = useQuery({
    queryKey: ['departments-all'],
    queryFn: async () => {
      const res = await api.get('/academic/departments');
      return res.data?.data || [];
    }
  });

  const { data: programs = [] } = useQuery({
    queryKey: ['programs-all'],
    queryFn: async () => {
      const res = await api.get('/academic/programs');
      return res.data?.data || [];
    }
  });

  const createMutation = useMutation({
    mutationFn: async (values: EventFormValues) => {
      const formatted = {
        ...values,
        department_id: values.department_id || null,
        program_id: values.program_id || null,
        semester: values.semester || null,
        poster_url: values.poster_url || null,
        fee_amount: values.fee_required == 1 ? values.fee_amount : 0.00
      };
      const res = await api.post('/events/', formatted);
      return res.data;
    },
    onSuccess: () => {
      setToast({ message: 'Event successfully created in Draft!', type: 'success' });
      queryClient.invalidateQueries({ queryKey: ['events-list'] });
      setTimeout(() => {
        navigate('/dashboard/staff/academics/event-management/manage');
      }, 1500);
    },
    onError: (err: any) => {
      const errMsg = err.response?.data?.detail || 'Failed to create event.';
      setToast({ message: errMsg, type: 'error' });
    }
  });

  const onSubmit = (values: EventFormValues) => {
    createMutation.mutate(values);
  };

  const onInvalid = (formErrors: any) => {
    console.log('Form validation errors:', formErrors);
    setToast({ message: 'Please fill in all required fields highlighted in red.', type: 'error' });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/dashboard/staff/academics/event-management/manage')}
            className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Calendar className="text-blue-600" /> Create New Event
            </h1>
            <p className="text-sm text-slate-500">Plan and publish academic workshops, webinars, or hackathons</p>
          </div>
        </div>
      </div>

      {toast && (
        <div className={`p-4 rounded-lg flex items-center gap-3 border ${
          toast.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <AlertCircle size={20} />
          <p className="text-sm font-medium">{toast.message}</p>
          <button onClick={() => setToast(null)} className="ml-auto text-xs font-bold uppercase hover:underline">Dismiss</button>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit, onInvalid)} className="bg-white rounded-xl shadow-md border border-slate-200 p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Academic Session */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Academic Session *</label>
            <select
              {...register('academic_session_id')}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.academic_session_id ? 'border-red-500' : 'border-slate-300'
              }`}
            >
              <option value="">Select Session</option>
              {sessions.map((s: any) => (
                <option key={s.id} value={s.id}>{s.session_name}</option>
              ))}
            </select>
            {errors.academic_session_id && <p className="text-xs text-red-500 mt-1">{errors.academic_session_id.message}</p>}
          </div>

          {/* Event Type */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Event Type *</label>
            <select
              {...register('event_type')}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.event_type ? 'border-red-500' : 'border-slate-300'
              }`}
            >
              <option value="">Select Event Type</option>
              {EVENT_TYPES.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            {errors.event_type && <p className="text-xs text-red-500 mt-1">{errors.event_type.message}</p>}
          </div>

          {/* Department */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Department (Optional)</label>
            <select
              {...register('department_id')}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Departments</option>
              {departments.map((d: any) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          {/* Program */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Program (Optional)</label>
            <select
              {...register('program_id')}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Programs</option>
              {programs.map((p: any) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* Semester */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Semester (Optional)</label>
            <select
              {...register('semester')}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Semesters</option>
              {[1, 2, 3, 4, 5, 6, 7, 8].map(s => (
                <option key={s} value={s}>Semester {s}</option>
              ))}
            </select>
          </div>

          {/* Event Title */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Event Title *</label>
            <input
              type="text"
              {...register('title')}
              placeholder="e.g. AI-ML Bootcamp"
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.title ? 'border-red-500' : 'border-slate-300'
              }`}
            />
            {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title.message}</p>}
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Start Date & Time *</label>
            <input
              type="datetime-local"
              {...register('start_date')}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.start_date ? 'border-red-500' : 'border-slate-300'
              }`}
            />
            {errors.start_date && <p className="text-xs text-red-500 mt-1">{errors.start_date.message}</p>}
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">End Date & Time *</label>
            <input
              type="datetime-local"
              {...register('end_date')}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.end_date ? 'border-red-500' : 'border-slate-300'
              }`}
            />
            {errors.end_date && <p className="text-xs text-red-500 mt-1">{errors.end_date.message}</p>}
          </div>

          {/* Venue */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Venue *</label>
            <input
              type="text"
              {...register('venue')}
              placeholder="Seminar Hall 1 / Zoom Link"
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.venue ? 'border-red-500' : 'border-slate-300'
              }`}
            />
            {errors.venue && <p className="text-xs text-red-500 mt-1">{errors.venue.message}</p>}
          </div>

          {/* Max Seats */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Maximum Seats *</label>
            <input
              type="number"
              {...register('max_seats')}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.max_seats ? 'border-red-500' : 'border-slate-300'
              }`}
            />
            {errors.max_seats && <p className="text-xs text-red-500 mt-1">{errors.max_seats.message}</p>}
          </div>

          {/* Registration Deadline */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Registration Deadline *</label>
            <input
              type="datetime-local"
              {...register('registration_deadline')}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.registration_deadline ? 'border-red-500' : 'border-slate-300'
              }`}
            />
            {errors.registration_deadline && <p className="text-xs text-red-500 mt-1">{errors.registration_deadline.message}</p>}
          </div>

          {/* Poster URL */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Poster Image URL (Optional)</label>
            <input
              type="text"
              {...register('poster_url')}
              placeholder="https://example.com/poster.jpg"
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.poster_url ? 'border-red-500' : 'border-slate-300'
              }`}
            />
            {errors.poster_url && <p className="text-xs text-red-500 mt-1">{errors.poster_url.message}</p>}
          </div>

          {/* Audience */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Target Audience *</label>
            <select
              {...register('audience')}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.audience ? 'border-red-500' : 'border-slate-300'
              }`}
            >
              <option value="Students">Students Only</option>
              <option value="Faculty">Faculty Only</option>
              <option value="Both">Both Students and Faculty</option>
            </select>
            {errors.audience && <p className="text-xs text-red-500 mt-1">{errors.audience.message}</p>}
          </div>

          {/* Registration Required */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Registration Required?</label>
            <div className="flex gap-4 mt-2">
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input type="radio" value={1} {...register('registration_required')} /> Yes
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input type="radio" value={0} {...register('registration_required')} /> No
              </label>
            </div>
          </div>

          {/* Fee Required */}
          {Number(watchedRegRequired) === 1 && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Fee Required?</label>
              <div className="flex gap-4 mt-2">
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input type="radio" value={1} {...register('fee_required')} /> Yes
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input type="radio" value={0} {...register('fee_required')} /> No
                </label>
              </div>
            </div>
          )}

          {/* Fee Amount */}
          {Number(watchedRegRequired) === 1 && Number(watchedFeeRequired) === 1 && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Fee Amount (INR) *</label>
              <input
                type="number"
                step="0.01"
                {...register('fee_amount')}
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.fee_amount ? 'border-red-500' : 'border-slate-300'
                }`}
              />
              {errors.fee_amount && <p className="text-xs text-red-500 mt-1">{errors.fee_amount.message}</p>}
            </div>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Event Description *</label>
          <textarea
            rows={4}
            {...register('description')}
            placeholder="Outline the schedule, speakers, topics covered, and prerequisites..."
            className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.description ? 'border-red-500' : 'border-slate-300'
            }`}
          />
          {errors.description && <p className="text-xs text-red-500 mt-1">{errors.description.message}</p>}
        </div>

        {/* Submit */}
        <div className="pt-4 border-t border-slate-100 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/dashboard/staff/academics/event-management/manage')}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg text-sm transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white font-semibold rounded-lg text-sm shadow transition flex items-center gap-2"
          >
            {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />} Save Event (Draft)
          </button>
        </div>
      </form>
    </div>
  );
}
