import React from 'react';
import type { BossQuestion, BossVerdict } from './useWorldBossRun';

interface Props {
  question: BossQuestion;
  verdict: BossVerdict | null;
  onPick: (index: number) => void;
}

const stateOf = (index: number, verdict: BossVerdict | null) => {
  if (!verdict) return 'open';
  if (index === verdict.correct_index) return 'correct';
  return 'wrong';
};

export const QuestionCard: React.FC<Props> = ({ question, verdict, onPick }) => {
  const locked = verdict !== null;

  return (
    <div className="space-y-6">
      {question.image && (
        <img
          src={question.image}
          alt=""
          className="mx-auto h-56 w-auto rounded-2xl border-2 border-white/10 object-cover"
        />
      )}

      <p className="text-center text-2xl font-bold leading-snug text-white">{question.prompt}</p>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {question.options.map((option, index) => {
          const state = stateOf(index, verdict);
          return (
            <button
              key={option}
              type="button"
              data-state={state}
              disabled={locked}
              onClick={() => onPick(index)}
              className={`rounded-2xl border-2 px-5 py-4 text-left font-bold transition-all ${
                state === 'correct'
                  ? 'border-emerald-500 bg-emerald-500/15 text-emerald-300'
                  : state === 'wrong'
                    ? 'border-white/5 text-gray-600'
                    : 'border-gray-800 bg-black hover:border-amber-400 hover:text-amber-300'
              }`}
            >
              {option}
            </button>
          );
        })}
      </div>
    </div>
  );
};
