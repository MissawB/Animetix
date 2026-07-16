import React from 'react';
import { useTranslation } from 'react-i18next';

export interface BlindtestBonusRecapProps {
  bonusArtistOn: boolean;
  bonusSeqOn: boolean;
  artistCorrect: boolean;
  seqCorrect: boolean;
  artists?: string[];
  sequence?: number | string;
  type: 'OP' | 'ED';
}

export const BlindtestBonusRecap: React.FC<BlindtestBonusRecapProps> = ({
  bonusArtistOn,
  bonusSeqOn,
  artistCorrect,
  seqCorrect,
  artists,
  sequence,
  type,
}) => {
  const { t } = useTranslation();
  return (
    <div className="mt-3 space-y-1 text-sm font-black uppercase tracking-wide">
      {bonusArtistOn && (
        <p className={artistCorrect ? 'text-green-500' : 'text-red-400'}>
          {artistCorrect
            ? t('games.blindtest.game.bonus_singer_ok', 'Chanteur ✓ +25')
            : t('games.blindtest.game.bonus_singer_ko', {
                defaultValue: 'Chanteur : {{artists}}',
                artists: (artists ?? []).join(', '),
              })}
        </p>
      )}
      {bonusSeqOn && (
        <p className={seqCorrect ? 'text-green-500' : 'text-red-400'}>
          {seqCorrect
            ? t('games.blindtest.game.bonus_number_ok', 'Numéro ✓ +25')
            : t('games.blindtest.game.bonus_number_ko', {
                defaultValue: "C'était {{type}} n°{{sequence}}",
                type,
                sequence,
              })}
        </p>
      )}
    </div>
  );
};
