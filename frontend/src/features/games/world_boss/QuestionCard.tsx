import React from 'react';
import type { BossQuestion, BossVerdict } from './useWorldBossRun';

interface Props {
  question: BossQuestion;
  verdict: BossVerdict | null;
  onPick: (index: number) => void;
}

type OptionState = 'open' | 'correct' | 'wrong-picked' | 'wrong-other';

const stateOf = (
  index: number,
  verdict: BossVerdict | null,
  picked: number | null,
): OptionState => {
  if (!verdict) return 'open';
  if (index === verdict.correct_index) return 'correct';
  if (index === picked) return 'wrong-picked';
  return 'wrong-other';
};

export const QuestionCard: React.FC<Props> = ({ question, verdict, onPick }) => {
  const locked = verdict !== null;
  const [picked, setPicked] = React.useState<number | null>(null);
  const [prevQuestion, setPrevQuestion] = React.useState(question);

  // A new question means the previous pick no longer applies to anything on
  // screen — clear it. Adjusted during render (same pattern TimerRing uses:
  // react.dev/learn/you-might-not-need-an-effect), not in an effect body, so
  // it lands before paint and keeps the no-setState-in-effect lint clean.
  if (question !== prevQuestion) {
    setPrevQuestion(question);
    setPicked(null);
  }

  const handlePick = (index: number) => {
    setPicked(index);
    onPick(index);
  };

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
          const state = stateOf(index, verdict, picked);
          return (
            <button
              key={option}
              type="button"
              data-state={state}
              disabled={locked}
              onClick={() => handlePick(index)}
              className={`rounded-2xl border-2 px-5 py-4 text-left font-bold transition-all ${
                state === 'correct'
                  ? 'border-emerald-500 bg-emerald-500/15 text-emerald-300'
                  : state === 'wrong-picked'
                    ? 'border-red-500 bg-red-500/15 text-red-300'
                    : state === 'wrong-other'
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
