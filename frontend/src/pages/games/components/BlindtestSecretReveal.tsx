import React from 'react';
import { useTranslation } from 'react-i18next';

export interface BlindtestSecretRevealProps {
  title?: string;
  image?: string | null;
}

export const BlindtestSecretReveal: React.FC<BlindtestSecretRevealProps> = ({ title, image }) => {
  const { t } = useTranslation();
  return (
    <div className="mt-3 flex flex-col items-center gap-3">
      {image && (
        <img
          src={image}
          alt={title ?? t('games.blindtest.game.secret_poster_alt', "Affiche de l'animé")}
          className="w-32 rounded-2xl shadow-xl border border-[#F4F1E8]/10 object-cover"
          loading="lazy"
          decoding="async"
        />
      )}
      <p className="text-lg font-bold text-[#F4F1E8]">
        {t('games.blindtest.game.it_was', "C'était :")}{' '}
        <span className="text-[#FDB913]">{title}</span>
      </p>
    </div>
  );
};
