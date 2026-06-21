import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface ErrorPanelProps {
  error: string;
  onDismiss: () => void;
}

const ErrorPanelComponent: React.FC<ErrorPanelProps> = ({ error, onDismiss }) => {
  return (
    <div className="mx-8 mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-red-400 text-sm">
      <AlertCircle className="w-5 h-5 flex-shrink-0" />
      <div>{error}</div>
      <button onClick={onDismiss} aria-label="×" className="ml-auto text-red-400 hover:text-white">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export const ErrorPanel = React.memo(ErrorPanelComponent);
