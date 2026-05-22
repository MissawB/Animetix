import React from 'react';
import { useToastStore } from '../../store/toastStore';
import { X } from 'lucide-react';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-center justify-between p-4 rounded-xl shadow-2xl min-w-[300px] text-white font-bold transition-all animate-slide-in-right ${
            toast.type === 'error' ? 'bg-red-500' :
            toast.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
          }`}
        >
          <span>{toast.message}</span>
          <button onClick={() => removeToast(toast.id)} className="ml-4 opacity-50 hover:opacity-100 transition-opacity">
            <X className="w-5 h-5" />
          </button>
        </div>
      ))}
    </div>
  );
};
