import React from 'react';
import { useTranslation } from 'react-i18next';
import { Trophy } from 'lucide-react';
import { Card } from '../../../components/ui/Card';

interface CovertestSessionSummaryProps {
  sessionLength: number;
  results: { score: number; won: boolean; secret?: string }[];
  totalScore: number;
  onNewSession: () => void;
}

export const CovertestSessionSummary: React.FC<CovertestSessionSummaryProps> = ({
  sessionLength,
  results,
  totalScore,
  onNewSession,
}) => {
  const { t } = useTranslation();
  const maxScore = sessionLength * 100;
  const wins = results.filter((r) => r.won).length;

  return (
    <div className="max-w-2xl mx-auto px-6 py-20">
      <Card padding="lg" className="text-center">
        <Trophy className="w-14 h-14 text-yellow-400 mx-auto mb-4" />
        <h1 className="text-4xl font-black italic manga-font uppercase text-black dark:text-white">
          {t('games.covertest.session_over_title', 'Session terminée')}
        </h1>
        <p className="mt-6 text-6xl font-black manga-font text-yellow-500">{totalScore}</p>
        <p className="text-xs font-black uppercase tracking-widest text-gray-400 mt-1">
          {t('games.covertest.session_score_summary', {
            defaultValue: 'sur {{maxScore}} points · {{wins}}/{{total}} trouvés',
            maxScore,
            wins,
            total: sessionLength,
          })}
        </p>
        <div className="mt-8 grid grid-cols-5 sm:grid-cols-10 gap-1.5">
          {results.map((r, i) => (
            <div
              key={i}
              title={
                t('games.covertest.round_tooltip', {
                  defaultValue: 'Manche {{num}}: {{score}} pts',
                  num: i + 1,
                  score: r.score,
                }) + (r.secret ? ` — ${r.secret}` : '')
              }
              className={`h-8 rounded-md grid place-items-center text-[10px] font-black ${
                r.won
                  ? 'bg-green-500/20 text-green-600 dark:text-green-400'
                  : 'bg-red-500/15 text-red-500'
              }`}
            >
              {r.score}
            </div>
          ))}
        </div>
        <div className="flex gap-3 justify-center mt-10">
          <button
            onClick={onNewSession}
            className="px-8 py-3.5 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font tracking-wide shadow-xl transition-all hover:scale-105 active:scale-95"
          >
            {t('games.covertest.new_session', 'NOUVELLE SESSION')}
          </button>
        </div>
      </Card>
    </div>
  );
};
