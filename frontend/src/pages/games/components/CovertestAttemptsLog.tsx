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
      <h4 className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] mb-2">
        {t('games.covertest.attempts_log', 'Journal des tentatives')}
      </h4>
      {guesses.length === 0 && (
        <p className="text-center py-6 opacity-20 italic text-sm">
          {t('games.covertest.no_attempts', 'Aucune tentative pour le moment.')}
        </p>
      )}
      {guesses.map((g, i) => (
        <div
          key={i}
          className={`flex items-center gap-3 p-3 rounded-2xl border-l-4 ${
            g.is_correct ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'
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
            <span className="w-9 h-12 rounded-lg bg-black/10 dark:bg-white/10 shrink-0" />
          )}
          <span className="font-bold flex-grow truncate">{g.title}</span>
          <span
            className={`shrink-0 grid place-items-center w-7 h-7 rounded-full ${
              g.is_correct ? 'bg-green-500' : 'bg-red-500'
            } text-white`}
          >
            {g.is_correct ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
          </span>
        </div>
      ))}
    </div>
  );
};
