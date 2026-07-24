import React, { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { HelpCircle, Loader2, RotateCcw, Trophy, X, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import {
  quizWhoService,
  type QuizWhoCandidate,
  type QuizWhoQuestion,
} from '../../features/games/services/quizWhoService';
import { useToastStore } from '../../store/toastStore';

const QuiEstCePage: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navState = location.state as { mediaType?: string; difficulty?: string } | null;
  const mediaType = navState?.mediaType;
  const difficulty = navState?.difficulty;
  const addToast = useToastStore((s) => s.addToast);

  const [board, setBoard] = useState<QuizWhoCandidate[]>([]);
  const [questions, setQuestions] = useState<QuizWhoQuestion[]>([]);
  const [eliminated, setEliminated] = useState<Set<string>>(new Set());
  const [lastAnswer, setLastAnswer] = useState<{ label: string; answer: string } | null>(null);
  const [askedCount, setAskedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [won, setWon] = useState(false);
  const [secretTitle, setSecretTitle] = useState<string | null>(null);

  const start = useCallback(async () => {
    setLoading(true);
    setEliminated(new Set());
    setLastAnswer(null);
    setAskedCount(0);
    setWon(false);
    setSecretTitle(null);
    try {
      const data = await quizWhoService.start(mediaType, difficulty);
      setBoard(data.board);
      setQuestions(data.questions);
    } catch {
      addToast(
        t('games.qui_est_ce.toast_start_failed', 'Impossible de démarrer la partie. Réessaie.'),
        'error',
      );
    } finally {
      setLoading(false);
    }
  }, [mediaType, difficulty, addToast, t]);

  useEffect(() => {
    // Fetch the board on mount (and when the universe changes).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    start();
  }, [start]);

  const remaining = board.filter((c) => !eliminated.has(c.id));

  const ask = async (q: QuizWhoQuestion) => {
    if (busy || won) return;
    setBusy(true);
    try {
      const res = await quizWhoService.ask(q.attr);
      setEliminated((prev) => {
        const next = new Set(prev);
        res.eliminated.forEach((id) => next.add(id));
        return next;
      });
      setLastAnswer({ label: q.label, answer: res.answer });
      setAskedCount(res.asked_count);
      setQuestions((prev) => prev.filter((x) => x.attr !== q.attr));
    } catch {
      addToast(
        t('games.qui_est_ce.toast_question_failed', 'Question impossible. Réessaie.'),
        'error',
      );
    } finally {
      setBusy(false);
    }
  };

  const guess = async (candidate: QuizWhoCandidate) => {
    if (busy || won || eliminated.has(candidate.id)) return;
    setBusy(true);
    try {
      const res = await quizWhoService.guess(candidate.id);
      if (res.correct) {
        setWon(true);
        setSecretTitle(res.secret_title || candidate.title);
      } else {
        setEliminated((prev) => new Set(prev).add(candidate.id));
        addToast(
          t('games.qui_est_ce.toast_wrong_guess', {
            defaultValue: "Ce n'est pas {{title}} !",
            title: candidate.title,
          }),
          'error',
        );
      }
    } catch {
      addToast(
        t('games.qui_est_ce.toast_guess_failed', 'Tentative impossible. Réessaie.'),
        'error',
      );
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0C10] text-center py-24 text-[#F4F1E8] font-black uppercase tracking-[0.3em] animate-pulse">
        {t('games.qui_est_ce.loading_board', 'Mise en place du plateau…')}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <span className="explore-stamp -rotate-2" aria-hidden>
              顔
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              {t('games.qui_est_ce.badge', 'Qui est-ce ?')}
            </span>
          </div>
          <h1 className="text-5xl md:text-6xl font-black italic font-manga tracking-tighter uppercase text-[#F4F1E8] leading-none">
            {t('games.qui_est_ce.title_part1', 'QUI')}{' '}
            <span className="text-[#E8442B]">{t('games.qui_est_ce.title_part2', 'EST-CE ?')}</span>
          </h1>
          <p className="mt-3 text-sm font-medium text-[#8F94A5]">
            {t(
              'games.qui_est_ce.subtitle',
              'Pose des questions pour éliminer les portraits, puis clique sur le bon.',
            )}
          </p>
        </header>

        {won ? (
          <div className="max-w-xl mx-auto text-center rounded-2xl border border-[#FDB913]/40 bg-[#FDB913]/5 p-10">
            <Trophy className="w-16 h-16 text-[#FDB913] mx-auto mb-5 animate-bounce" />
            <h2 className="text-3xl font-black italic font-manga uppercase mb-2 text-[#F4F1E8]">
              {t('games.qui_est_ce.win_title', 'Trouvé !')}
            </h2>
            <p className="text-lg mb-1 text-[#8F94A5]">
              {t('games.qui_est_ce.win_it_was', "C'était bien")}{' '}
              <span className="font-black text-[#FDB913]">{secretTitle}</span>.
            </p>
            <p className="text-xs font-bold uppercase tracking-widest text-[#8F94A5] mb-8">
              {t('games.qui_est_ce.questions_asked', {
                defaultValue: '{{count}} question{{plural}} posée{{plural}}',
                count: askedCount,
                plural: askedCount > 1 ? 's' : '',
              })}
            </p>
            <button
              onClick={start}
              className="inline-flex items-center gap-2 bg-[#E8442B] hover:bg-[#c93a24] text-[#F4F1E8] font-manga font-black italic uppercase tracking-widest px-8 py-4 rounded-xl transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
            >
              <RotateCcw className="w-5 h-5" /> {t('games.qui_est_ce.replay', 'Rejouer')}
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Board */}
            <div className="lg:col-span-8">
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 sm:gap-4">
                {board.map((c) => {
                  const out = eliminated.has(c.id);
                  return (
                    <button
                      key={c.id}
                      onClick={() => guess(c)}
                      disabled={out || busy}
                      title={
                        out
                          ? c.title
                          : t('games.qui_est_ce.guess_title', {
                              defaultValue: 'Deviner : {{title}}',
                              title: c.title,
                            })
                      }
                      className={`group relative aspect-[3/4] rounded-2xl overflow-hidden border-2 transition-all ${
                        out
                          ? 'border-transparent opacity-30 grayscale'
                          : 'border-[#F4F1E8]/10 hover:border-[#FDB913] hover:scale-[1.03] cursor-pointer'
                      }`}
                    >
                      {c.image ? (
                        <img
                          src={c.image}
                          alt={c.title}
                          loading="lazy"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full grid place-items-center bg-[#0F1016] text-[#8F94A5] text-xs">
                          {c.title}
                        </div>
                      )}
                      {out && (
                        <span className="absolute inset-0 grid place-items-center bg-[#0B0C10]/60">
                          <X className="w-10 h-10 text-[#E8442B]" strokeWidth={3} />
                        </span>
                      )}
                      <span className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 to-transparent p-2 pt-6">
                        <span className="block text-[10px] font-black uppercase tracking-wide text-white truncate text-left">
                          {c.title}
                        </span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Question panel */}
            <div className="lg:col-span-4 space-y-5 lg:sticky lg:top-24">
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-4 flex items-center justify-between">
                <span className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
                  {t('games.qui_est_ce.remaining', 'Restants')}
                </span>
                <span className="text-2xl font-black tabular-nums text-[#FDB913]">
                  {remaining.length}
                </span>
              </div>

              {lastAnswer && (
                <div
                  className={`rounded-2xl border p-4 ${
                    lastAnswer.answer === 'OUI'
                      ? 'border-[#FDB913]/40 bg-[#FDB913]/10'
                      : 'border-[#E8442B]/40 bg-[#E8442B]/10'
                  }`}
                >
                  <p className="text-[11px] font-bold text-[#8F94A5] mb-1">{lastAnswer.label}</p>
                  <p
                    className={`flex items-center gap-2 font-black italic uppercase ${lastAnswer.answer === 'OUI' ? 'text-[#FDB913]' : 'text-[#E8442B]'}`}
                  >
                    {lastAnswer.answer === 'OUI' ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <X className="w-5 h-5" />
                    )}
                    {lastAnswer.answer}
                  </p>
                </div>
              )}

              <div>
                <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-3 flex items-center gap-2">
                  <HelpCircle className="w-4 h-4" />{' '}
                  {t('games.qui_est_ce.ask_question', 'Pose une question')}
                </h3>
                <div className="space-y-2 max-h-[55vh] overflow-y-auto pr-1 custom-scrollbar">
                  {questions.length === 0 ? (
                    <p className="text-xs font-bold text-[#8F94A5] py-6 text-center">
                      {t(
                        'games.qui_est_ce.no_more_questions',
                        'Plus de questions — clique sur un portrait pour deviner !',
                      )}
                    </p>
                  ) : (
                    questions.map((q) => (
                      <button
                        key={q.attr}
                        onClick={() => ask(q)}
                        disabled={busy}
                        className="w-full text-left rounded-xl border border-[#F4F1E8]/10 hover:border-[#FDB913] hover:bg-[#FDB913]/5 px-4 py-3 text-sm font-bold text-[#F4F1E8] transition-colors disabled:opacity-50"
                      >
                        {q.label}
                      </button>
                    ))
                  )}
                </div>
              </div>

              <button
                onClick={start}
                disabled={busy}
                className="w-full flex items-center justify-center gap-2 text-xs font-black uppercase tracking-widest border border-[#F4F1E8]/10 text-[#8F94A5] hover:text-[#F4F1E8] hover:border-[#FDB913] py-3 rounded-xl transition-colors"
              >
                {busy ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RotateCcw className="w-4 h-4" />
                )}
                {t('games.qui_est_ce.new_game', 'Nouvelle partie')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuiEstCePage;
