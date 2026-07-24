import React from 'react';
import { useTranslation } from 'react-i18next';
import { Check, X } from 'lucide-react';

interface GuessLogItem {
  title: string;
  is_correct: boolean;
  image?: string | null;
}

interface CovertestAttemptsLogProps {
  guesses: GuessLogItem[];
}

export const CovertestAttemptsLog: React.FC<CovertestAttemptsLogProps> = ({ guesses }) => {
  const { t } = useTranslation();

  return (
    <div className="mt-10 space-y-3">
      <h4 className="text-[10px] font-black text-[#8F94A5]/60 uppercase tracking-[0.2em] mb-2">
        {t('games.covertest.attempts_log', 'Journal des tentatives')}
      </h4>
      {guesses.length === 0 && (
        <p className="text-center py-6 text-[#8F94A5]/50 italic text-sm">
          {t('games.covertest.no_attempts', 'Aucune tentative pour le moment.')}
        </p>
      )}
      {guesses.map((g, i) => (
        <div
          key={i}
          className={`flex items-center gap-3 p-3 rounded-2xl border-l-4 bg-[#0F1016] ${
            g.is_correct ? 'border-[#FDB913]' : 'border-[#E8442B]'
          }`}
        >
          {g.image ? (
            <img
              src={g.image}
              alt=""
              className="w-9 h-12 object-cover rounded-lg shrink-0"
              loading="lazy"
            />
          ) : (
            <span className="w-9 h-12 rounded-lg bg-[#F4F1E8]/10 shrink-0" />
          )}
          <span className="font-bold flex-grow truncate text-[#F4F1E8]">{g.title}</span>
          <span
            className={`shrink-0 grid place-items-center w-7 h-7 rounded-full ${
              g.is_correct ? 'bg-[#FDB913] text-[#0B0C10]' : 'bg-[#E8442B] text-[#F4F1E8]'
            }`}
          >
            {g.is_correct ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
          </span>
        </div>
      ))}
    </div>
  );
};
