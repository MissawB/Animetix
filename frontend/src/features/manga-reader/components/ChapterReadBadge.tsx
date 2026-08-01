import React from 'react';
import { Check, Circle } from 'lucide-react';
import type { ChapterProgress } from '../progress/progressService';

interface Props {
  progress?: ChapterProgress;
  onToggleRead: (next: boolean) => void;
  disabled?: boolean;
}

/** Pastille lu/non-lu + avancement, partagé par la popup Tachidesk et la fiche
 *  œuvre pour que les deux écrans ne puissent pas diverger. */
export const ChapterReadBadge: React.FC<Props> = ({ progress, onToggleRead, disabled }) => {
  const isRead = progress?.is_read ?? false;
  const pageCount = progress?.page_count ?? 0;
  const lastPage = progress?.last_page_read ?? 0;
  // page_count = 0 : les pages ne sont pas encore synchronisées, un dénominateur
  // serait faux — on n'affiche que l'état lu/non-lu.
  const showCounter = !isRead && pageCount > 0 && lastPage > 0;

  return (
    <div className="flex items-center gap-2">
      {showCounter && (
        <span className="text-[9px] font-bold tabular-nums text-[#FDB913]">
          {lastPage + 1}/{pageCount}
        </span>
      )}
      <button
        type="button"
        disabled={disabled}
        onClick={() => onToggleRead(!isRead)}
        aria-label={isRead ? 'Marquer comme non lu' : 'Marquer comme lu'}
        title={isRead ? 'Marquer comme non lu' : 'Marquer comme lu'}
        className={`rounded-full border p-1 transition-colors disabled:opacity-40 ${
          isRead
            ? 'border-[#FDB913]/40 bg-[#FDB913]/15 text-[#FDB913]'
            : 'border-[#F4F1E8]/15 text-[#8F94A5] hover:text-[#F4F1E8]'
        }`}
      >
        {isRead ? <Check className="h-3 w-3" /> : <Circle className="h-3 w-3" />}
      </button>
    </div>
  );
};
