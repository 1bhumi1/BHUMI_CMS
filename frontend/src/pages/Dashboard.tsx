import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { removeTokens } from '../lib/auth';
import { Loader2 } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch /me to determine role if we don't trust JWT payload alone
    api.get('/auth/me')
      .then(response => {
        const user = response.data?.data;
        if (user) {
          if (user.student_id) {
            navigate('/dashboard/student', { replace: true });
          } else if (user.staff_id) {
            navigate('/dashboard/staff', { replace: true });
          } else {
            // Unhandled role
            navigate('/dashboard/staff', { replace: true });
          }
        }
      })
      .catch(() => {
        removeTokens();
        navigate('/login', { replace: true });
      })
      .finally(() => {
        setLoading(false);
      });
  }, [navigate]);

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return null;
}
