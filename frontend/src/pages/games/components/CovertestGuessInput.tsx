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
          className="w-full p-4 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none font-bold text-[#F4F1E8] transition-colors placeholder:text-[#8F94A5]/60 disabled:opacity-50"
        />
        {showSug && suggestions.length > 0 && (
          <ul className="absolute z-30 left-0 right-0 mt-2 bg-[#0F1016] rounded-xl border border-[#F4F1E8]/10 shadow-2xl overflow-hidden max-h-72 overflow-y-auto">
            {suggestions.map((s) => (
              <li key={s.title}>
                <button
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    submit(s.title);
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-[#FDB913]/10 font-bold text-sm text-[#F4F1E8] transition-colors flex items-center gap-2"
                >
                  <ChevronRight className="w-3.5 h-3.5 text-[#8F94A5] shrink-0" />
                  <span className="truncate">{s.title}</span>
                  {s.via && (
                    <span className="ml-auto shrink-0 max-w-[45%] truncate text-[10px] font-bold italic text-[#8F94A5]">
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
        className="w-full py-4 rounded-xl bg-[#E8442B] hover:bg-[#c93a24] text-[#F4F1E8] font-manga font-black italic uppercase tracking-wide transition-colors disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] flex items-center justify-center gap-2"
      >
        <Send className="w-5 h-5" />{' '}
        {isGuessing
          ? t('games.covertest.checking', 'VÉRIFICATION…')
          : t('games.covertest.guess_btn', 'DEVINER')}
      </button>
      <p className="text-center text-[10px] font-black uppercase tracking-widest text-[#8F94A5]/60">
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
