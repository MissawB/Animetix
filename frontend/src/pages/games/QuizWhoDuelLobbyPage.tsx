import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ScanFace, Users, Clapperboard, BookOpen, Loader2, Plus, LogIn } from 'lucide-react';
import { quizWhoDuelService } from '../../features/games/services/quizWhoDuelService';
import { useToastStore } from '../../store/toastStore';

type Universe = 'Anime' | 'Manga' | 'Character';
type Difficulty = 'Easy' | 'Normal' | 'Hard' | 'Impossible';

const UNIVERSES: { key: Universe; label: string; icon: React.ElementType }[] = [
  { key: 'Anime', label: 'Anime', icon: Clapperboard },
  { key: 'Manga', label: 'Manga', icon: BookOpen },
  { key: 'Character', label: 'Personnages', icon: Users },
];
const DIFFS: Difficulty[] = ['Easy', 'Normal', 'Hard', 'Impossible'];
const DIFF_LABEL: Record<Difficulty, string> = {
  Easy: 'Facile',
  Normal: 'Normal',
  Hard: 'Difficile',
  Impossible: 'Impossible',
};

const QuizWhoDuelLobbyPage: React.FC = () => {
  const navigate = useNavigate();
  const addToast = useToastStore((s) => s.addToast);
  const [universe, setUniverse] = useState<Universe>('Anime');
  const [difficulty, setDifficulty] = useState<Difficulty>('Normal');
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);

  const create = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const room = await quizWhoDuelService.create(universe, difficulty);
      navigate(`/game/quiz-who/arena/${room.room_code}/`);
    } catch {
      addToast('Impossible de créer la salle.', 'error');
      setBusy(false);
    }
  };

  const join = async () => {
    if (busy || !code.trim()) return;
    setBusy(true);
    try {
      const room = await quizWhoDuelService.join(code.trim().toUpperCase());
      navigate(`/game/quiz-who/arena/${room.room_code}/`);
    } catch {
      addToast('Salle introuvable ou complète.', 'error');
      setBusy(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-6 py-14">
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-yellow-400/10 border border-yellow-400/30 text-yellow-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
          <Users className="w-3.5 h-3.5" /> Entre amis · 2 joueurs
        </div>
        <h1 className="text-5xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
          QUI EST-CE <span className="text-yellow-400">DUEL</span>
        </h1>
        <p className="mt-4 text-base font-medium text-gray-500 dark:text-white/50">
          Chacun son perso secret. À tour de rôle, démasquez l'autre en premier.
        </p>
      </div>

      <div className="rounded-[2.5rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-7 md:p-9 space-y-9 shadow-token-card">
        {/* Create */}
        <div className="space-y-5">
          <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-400 flex items-center gap-2">
            <Plus className="w-4 h-4" /> Créer une salle
          </h2>
          <div className="grid grid-cols-3 gap-3">
            {UNIVERSES.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setUniverse(key)}
                aria-pressed={universe === key}
                className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${
                  universe === key ? 'border-yellow-400 bg-yellow-400/10' : 'border-black/5 dark:border-white/10 hover:border-yellow-400/50'
                }`}
              >
                <Icon className={`w-7 h-7 ${universe === key ? 'text-yellow-500' : 'text-gray-400'}`} />
                <span className="text-xs font-black uppercase tracking-wide text-black dark:text-white">{label}</span>
              </button>
            ))}
          </div>
          <div className="grid grid-cols-4 gap-2">
            {DIFFS.map((d) => (
              <button
                key={d}
                onClick={() => setDifficulty(d)}
                aria-pressed={difficulty === d}
                className={`py-2.5 rounded-xl border-2 text-[11px] font-black uppercase tracking-wide transition-all ${
                  difficulty === d ? 'border-yellow-400 bg-yellow-400/10 text-yellow-600 dark:text-yellow-400' : 'border-black/5 dark:border-white/10 text-gray-500 hover:border-yellow-400/40'
                }`}
              >
                {DIFF_LABEL[d]}
              </button>
            ))}
          </div>
          <button
            onClick={create}
            disabled={busy}
            className="w-full flex items-center justify-center gap-2 bg-yellow-400 text-black font-black italic uppercase tracking-widest py-4 rounded-2xl hover:scale-[1.01] active:scale-95 transition-all disabled:opacity-60"
          >
            {busy ? <Loader2 className="w-5 h-5 animate-spin" /> : <ScanFace className="w-5 h-5" />}
            Créer & inviter
          </button>
        </div>

        <div className="flex items-center gap-3 text-gray-400">
          <div className="flex-grow h-px bg-black/10 dark:bg-white/10" />
          <span className="text-[10px] font-black uppercase tracking-widest">ou</span>
          <div className="flex-grow h-px bg-black/10 dark:bg-white/10" />
        </div>

        {/* Join */}
        <div className="space-y-4">
          <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-400 flex items-center gap-2">
            <LogIn className="w-4 h-4" /> Rejoindre avec un code
          </h2>
          <div className="flex gap-3">
            <input
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="CODE"
              aria-label="Code de la salle"
              maxLength={5}
              className="flex-grow rounded-2xl border-2 border-black/10 dark:border-white/10 bg-transparent px-5 py-4 text-center text-2xl font-black tracking-[0.4em] uppercase text-black dark:text-white outline-none focus:border-yellow-400"
            />
            <button
              onClick={join}
              disabled={busy || !code.trim()}
              className="px-6 rounded-2xl bg-black dark:bg-white text-white dark:text-black font-black uppercase tracking-widest disabled:opacity-50"
            >
              Go
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuizWhoDuelLobbyPage;
