import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, X, Trophy, Frown, HelpCircle, Check, Hourglass, Copy } from 'lucide-react';
import {
  quizWhoDuelService,
  type QWDuelState,
} from '../../features/games/services/quizWhoDuelService';
import { useToastStore } from '../../store/toastStore';

const QuizWhoDuelArenaPage: React.FC = () => {
  const { roomCode = '' } = useParams();
  const navigate = useNavigate();
  const addToast = useToastStore((s) => s.addToast);
  const [st, setSt] = useState<QWDuelState | null>(null);
  const [busy, setBusy] = useState(false);
  const finishedRef = useRef(false);

  const refresh = useCallback(async () => {
    try {
      const data = await quizWhoDuelService.state(roomCode);
      setSt(data);
      finishedRef.current = data.finished;
    } catch {
      /* keep last state on a transient poll failure */
    }
  }, [roomCode]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    const id = setInterval(() => {
      if (!finishedRef.current) refresh();
    }, 1500);
    return () => clearInterval(id);
  }, [refresh]);

  const eliminated = new Set(st?.your_eliminated || []);

  const ask = async (attr: string) => {
    if (busy || !st?.your_turn) return;
    setBusy(true);
    try {
      await quizWhoDuelService.ask(roomCode, attr);
      await refresh();
    } catch {
      addToast('Action impossible.', 'error');
    } finally {
      setBusy(false);
    }
  };

  const guess = async (id: string) => {
    if (busy || !st?.your_turn || eliminated.has(id)) return;
    setBusy(true);
    try {
      const res = await quizWhoDuelService.guess(roomCode, id);
      if (!res.correct) addToast("Raté ! Au tour de l'adversaire.", 'error');
      await refresh();
    } catch {
      addToast('Tentative impossible.', 'error');
    } finally {
      setBusy(false);
    }
  };

  if (!st) {
    return (
      <div className="text-center py-24 text-black dark:text-white font-black uppercase tracking-[0.3em] animate-pulse">
        Connexion à la salle…
      </div>
    );
  }

  const byId = Object.fromEntries(st.board.map((b) => [b.id, b]));
  const remaining = st.board.filter((b) => !eliminated.has(b.id)).length;

  // End screen
  if (st.finished) {
    return (
      <div className="max-w-xl mx-auto px-6 py-20 text-center">
        {st.you_won ? (
          <>
            <Trophy className="w-20 h-20 text-yellow-400 mx-auto mb-6 animate-bounce" />
            <h1 className="text-4xl font-black italic uppercase mb-2 text-black dark:text-white">Victoire !</h1>
            <p className="text-gray-500 dark:text-white/60">Tu as démasqué le perso adverse en premier.</p>
          </>
        ) : (
          <>
            <Frown className="w-20 h-20 text-gray-400 mx-auto mb-6" />
            <h1 className="text-4xl font-black italic uppercase mb-2 text-black dark:text-white">Perdu…</h1>
            <p className="text-gray-500 dark:text-white/60">L'adversaire a trouvé ton perso avant toi.</p>
          </>
        )}
        <button
          onClick={() => navigate('/game/quiz-who/lobby/')}
          className="mt-8 inline-flex items-center gap-2 bg-yellow-400 text-black font-black italic uppercase tracking-widest px-8 py-4 rounded-2xl hover:scale-105 transition-all"
        >
          Rejouer
        </button>
      </div>
    );
  }

  // Waiting for opponent
  if (!st.opponent_joined) {
    return (
      <div className="max-w-md mx-auto px-6 py-24 text-center">
        <Hourglass className="w-14 h-14 text-yellow-400 mx-auto mb-6 animate-pulse" />
        <h1 className="text-2xl font-black italic uppercase mb-3 text-black dark:text-white">En attente d'un adversaire</h1>
        <p className="text-gray-500 dark:text-white/60 mb-6">Partage ce code à un ami :</p>
        <button
          onClick={() => {
            navigator.clipboard?.writeText(roomCode);
            addToast('Code copié !', 'success');
          }}
          className="inline-flex items-center gap-3 text-4xl font-black tracking-[0.4em] text-black dark:text-white bg-black/5 dark:bg-white/10 px-8 py-4 rounded-2xl"
        >
          {roomCode} <Copy className="w-5 h-5 opacity-50" />
        </button>
      </div>
    );
  }

  const mySecret = byId[st.your_secret_id];

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <header className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-gray-400">Salle {st.room_code}</p>
          <h1 className="text-3xl font-black italic manga-font uppercase text-black dark:text-white">Qui est-ce ? Duel</h1>
        </div>
        <div
          className={`px-5 py-2.5 rounded-2xl font-black uppercase tracking-widest text-sm ${
            st.your_turn ? 'bg-green-500/15 text-green-500' : 'bg-black/5 dark:bg-white/10 text-gray-500'
          }`}
        >
          {st.your_turn ? 'À toi de jouer' : "Tour de l'adversaire…"}
        </div>
      </header>

      {/* Your secret */}
      {mySecret && (
        <div className="flex items-center gap-4 rounded-2xl border-2 border-yellow-400/40 bg-yellow-400/5 p-3 mb-6 max-w-sm">
          {mySecret.image && <img src={mySecret.image} alt="" className="w-12 h-16 object-cover rounded-lg" />}
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-yellow-500">Ton perso (à protéger)</p>
            <p className="font-black text-black dark:text-white">{mySecret.title}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Board (the opponent's secret to find) */}
        <div className="lg:col-span-8">
          <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
            {st.board.map((c) => {
              const out = eliminated.has(c.id);
              return (
                <button
                  key={c.id}
                  onClick={() => guess(c.id)}
                  disabled={out || busy || !st.your_turn}
                  title={st.your_turn ? `Deviner : ${c.title}` : c.title}
                  className={`group relative aspect-[3/4] rounded-2xl overflow-hidden border-2 transition-all ${
                    out
                      ? 'border-transparent opacity-30 grayscale'
                      : st.your_turn
                        ? 'border-black/5 dark:border-white/10 hover:border-yellow-400 hover:scale-[1.03] cursor-pointer'
                        : 'border-black/5 dark:border-white/10'
                  }`}
                >
                  {c.image ? (
                    <img src={c.image} alt={c.title} loading="lazy" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full grid place-items-center bg-black/40 text-gray-500 text-xs">{c.title}</div>
                  )}
                  {out && (
                    <span className="absolute inset-0 grid place-items-center bg-black/40">
                      <X className="w-10 h-10 text-red-500" strokeWidth={3} />
                    </span>
                  )}
                  <span className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 to-transparent p-2 pt-6">
                    <span className="block text-[10px] font-black uppercase text-white truncate text-left">{c.title}</span>
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Side panel */}
        <div className="lg:col-span-4 space-y-5 lg:sticky lg:top-24">
          <div className="rounded-2xl border-2 border-black/5 dark:border-white/10 bg-surface-card p-4 flex items-center justify-between">
            <span className="text-xs font-black uppercase tracking-widest text-gray-400">Restants</span>
            <span className="text-2xl font-black tabular-nums text-yellow-500">{remaining}</span>
          </div>

          {st.last_answer && (
            <div
              className={`rounded-2xl border-2 p-4 ${
                st.last_answer.answer === 'OUI'
                  ? 'border-green-500/40 bg-green-500/10'
                  : st.last_answer.answer === 'NON'
                    ? 'border-red-500/40 bg-red-500/10'
                    : 'border-white/20 bg-black/5 dark:bg-white/5'
              }`}
            >
              <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-1">
                {st.last_answer.by === st.your_player ? 'Toi' : 'Adversaire'}
              </p>
              <p className="text-[11px] font-bold opacity-70 mb-1">{st.last_answer.label}</p>
              <p className="flex items-center gap-2 font-black italic uppercase text-sm">
                {st.last_answer.answer === 'OUI' && <Check className="w-4 h-4 text-green-500" />}
                {st.last_answer.answer === 'NON' && <X className="w-4 h-4 text-red-500" />}
                {st.last_answer.answer}
              </p>
            </div>
          )}

          {st.your_turn ? (
            <div>
              <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-400 mb-3 flex items-center gap-2">
                <HelpCircle className="w-4 h-4" /> Pose une question
              </h3>
              <div className="space-y-2 max-h-[50vh] overflow-y-auto pr-1 custom-scrollbar">
                {st.questions.map((q) => (
                  <button
                    key={q.attr}
                    onClick={() => ask(q.attr)}
                    disabled={busy}
                    className="w-full text-left rounded-xl border-2 border-black/5 dark:border-white/10 hover:border-yellow-400 hover:bg-yellow-400/5 px-4 py-3 text-sm font-bold text-black dark:text-white transition-all disabled:opacity-50"
                  >
                    {q.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border-2 border-black/5 dark:border-white/10 p-6 text-center">
              {busy ? (
                <Loader2 className="w-6 h-6 animate-spin mx-auto text-gray-400" />
              ) : (
                <p className="text-xs font-bold uppercase tracking-widest text-gray-400">
                  L'adversaire réfléchit…
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuizWhoDuelArenaPage;
