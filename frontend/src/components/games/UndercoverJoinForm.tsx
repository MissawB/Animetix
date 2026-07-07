import React from 'react';
import { useTranslation } from 'react-i18next';

interface UndercoverJoinFormProps {
  name: string;
  setName: (v: string) => void;
  submitName: () => void;
  meName?: string;
}

export const UndercoverJoinForm: React.FC<UndercoverJoinFormProps> = ({
  name,
  setName,
  submitName,
  meName,
}) => {
  const { t } = useTranslation();

  return (
    <div>
      <p className="text-[11px] font-black uppercase tracking-[0.25em] text-yellow-400/70 mb-2">
        {t('games.undercover.room.codename_label', 'Nom de code')} {meName ? `· ${meName}` : ''}
      </p>
      <div className="flex gap-3">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submitName();
          }}
          placeholder={t('games.undercover.room.codename_placeholder', "Choisis un pseudo d'agent…")}
          maxLength={15}
          aria-label={t('games.undercover.room.codename_label', 'Nom de code')}
          className="flex-grow p-3.5 rounded-2xl bg-white/[0.04] border-2 border-white/10 focus:border-yellow-400 outline-none font-bold text-white placeholder:text-white/25 transition-colors"
        />
        <button
          onClick={submitName}
          className="px-6 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic uppercase tracking-wide transition-colors"
        >
          {t('common.validate', 'Valider')}
        </button>
      </div>
    </div>
  );
};
