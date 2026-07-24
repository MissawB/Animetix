import React from 'react';
import { useTranslation } from 'react-i18next';
import { Trophy } from 'lucide-react';

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
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-2xl mx-auto px-6 py-20">
        <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 md:p-10 text-center">
          <Trophy className="w-14 h-14 text-[#FDB913] mx-auto mb-4" />
          <h1 className="font-manga text-4xl font-black italic uppercase text-[#F4F1E8]">
            {t('games.covertest.session_over_title', 'Session terminée')}
          </h1>
          <p className="font-manga mt-6 text-6xl font-black italic text-[#FDB913]">{totalScore}</p>
          <p className="text-xs font-black uppercase tracking-widest text-[#8F94A5] mt-1">
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
                  r.won ? 'bg-[#FDB913]/15 text-[#FDB913]' : 'bg-[#E8442B]/15 text-[#E8442B]'
                }`}
              >
                {r.score}
              </div>
            ))}
          </div>
          <div className="flex gap-3 justify-center mt-10">
            <button
              onClick={onNewSession}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-[#E8442B] hover:bg-[#c93a24] text-[#F4F1E8] font-manga font-black italic uppercase tracking-wide transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
            >
              {t('games.covertest.new_session', 'NOUVELLE SESSION')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
