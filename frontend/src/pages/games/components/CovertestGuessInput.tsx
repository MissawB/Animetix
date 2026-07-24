import React from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronRight, Send } from 'lucide-react';

interface Suggestion {
  title: string;
  via?: string;
}

interface CovertestGuessInputProps {
  guess: string;
  onChange: (val: string) => void;
  submit: (value?: string) => void;
  suggestions: Suggestion[];
  showSug: boolean;
  setShowSug: (show: boolean) => void;
  guessValid: boolean;
  isGuessing: boolean;
  maxAttempts: number;
  attemptsUsed: number;
}

export const CovertestGuessInput: React.FC<CovertestGuessInputProps> = ({
  guess,
  onChange,
  submit,
  suggestions,
  showSug,
  setShowSug,
  guessValid,
  isGuessing,
  maxAttempts,
  attemptsUsed,
}) => {
  const { t } = useTranslation();

  return (
    <div className="space-y-5">
      <div className="relative">
        <input
          type="text"
          value={guess}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              submit();
            }
          }}
          onFocus={() => {
            if (suggestions.length) setShowSug(true);
          }}
          onBlur={() => setTimeout(() => setShowSug(false), 150)}
          placeholder={t('games.covertest.guess_placeholder', 'Quel manga est-ce ?')}
          aria-label={t('games.covertest.guess_aria', 'Titre du manga')}
          autoComplete="off"
          disabled={isGuessing}
          className="w-full p-4 rounded-2xl bg-black/[0.03] dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold transition-all placeholder:opacity-30 disabled:opacity-50"
        />
        {showSug && suggestions.length > 0 && (
          <ul className="absolute z-30 left-0 right-0 mt-2 bg-white dark:bg-[#0f0f1a] rounded-2xl border border-black/10 dark:border-white/10 shadow-2xl overflow-hidden max-h-72 overflow-y-auto">
            {suggestions.map((s) => (
              <li key={s.title}>
                <button
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    submit(s.title);
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-yellow-400/10 font-bold text-sm transition-colors flex items-center gap-2"
                >
                  <ChevronRight className="w-3.5 h-3.5 opacity-40 shrink-0" />
                  <span className="truncate">{s.title}</span>
                  {s.via && (
                    <span className="ml-auto shrink-0 max-w-[45%] truncate text-[10px] font-bold italic opacity-50">
                      {s.via}
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <button
        onClick={() => submit()}
        disabled={!guessValid || isGuessing}
        title={
          guess.trim() && !guessValid
            ? t('games.covertest.pick_from_list', 'Choisis un manga de la liste')
            : undefined
        }
        className="w-full py-4 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font tracking-wide shadow-xl transition-all hover:scale-[1.01] active:scale-95 disabled:opacity-40 disabled:hover:scale-100 flex items-center justify-center gap-2"
      >
        <Send className="w-5 h-5" />{' '}
        {isGuessing
          ? t('games.covertest.checking', 'VÉRIFICATION…')
          : t('games.covertest.guess_btn', 'DEVINER')}
      </button>
      <p className="text-center text-[10px] font-black uppercase tracking-widest opacity-30">
        {t('games.covertest.attempts_remaining', {
          defaultValue:
            '{{count}} essai{{plural}} restant{{plural}} · le flou diminue à chaque essai',
          count: maxAttempts - attemptsUsed,
          plural: maxAttempts - attemptsUsed > 1 ? 's' : '',
        })}
      </p>
    </div>
  );
};
