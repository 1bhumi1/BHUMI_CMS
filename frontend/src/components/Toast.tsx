import React, { useEffect } from 'react';
import { X, Check, AlertCircle } from 'lucide-react';

interface ToastProps {
  message: string;
  type: 'success' | 'error';
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ message, type, onClose }) => {
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

export default Toast;
