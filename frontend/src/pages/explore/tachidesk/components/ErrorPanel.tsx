import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface ErrorPanelProps {
  error: string;
  onDismiss: () => void;
}

const ErrorPanelComponent: React.FC<ErrorPanelProps> = ({ error, onDismiss }) => {
  return (
    <div className="mx-6 mt-6 flex items-center gap-3 rounded-2xl border border-[#E8442B]/30 bg-[#E8442B]/[0.08] p-4 text-sm font-semibold text-[#E8442B] sm:mx-8">
      <AlertCircle className="h-5 w-5 flex-shrink-0" />
      <div className="flex-1">{error}</div>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Fermer"
        className="text-[#E8442B]/70 transition-colors hover:text-[#F4F1E8]"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

export const ErrorPanel = React.memo(ErrorPanelComponent);
