import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookImage, Layers, Image as ImageIcon, Play, Hash, Check, PenTool } from 'lucide-react';
import { Card } from '../../components/ui/Card';

type Mode = 'session' | 'single';
type Difficulty = 'Easy' | 'Normal' | 'Hard' | 'Impossible' | 'Tryhard';

const DIFFICULTIES: { key: Difficulty; label: string; sub: string; tries: number; active: string }[] = [
  { key: 'Easy', label: 'Facile', sub: '6 essais', tries: 6, active: 'border-green-500 bg-green-500/10 text-green-600 dark:text-green-400' },
  { key: 'Normal', label: 'Normal', sub: '4 essais', tries: 4, active: 'border-yellow-500 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400' },
  { key: 'Hard', label: 'Difficile', sub: '3 essais', tries: 3, active: 'border-orange-500 bg-orange-500/10 text-orange-600 dark:text-orange-400' },
  { key: 'Impossible', label: 'Impossible', sub: '2 essais', tries: 2, active: 'border-red-600 bg-red-600/10 text-red-600 dark:text-red-400' },
  { key: 'Tryhard', label: 'Tryhard', sub: 'Distorsions', tries: 3, active: 'border-fuchsia-500 bg-fuchsia-500/10 text-fuchsia-500' },
];

const LENGTHS = [5, 10, 20, 50];

type Origin = '' | 'ja' | 'fr';
const ORIGINS: { key: Origin; label: string; sub: string }[] = [
  { key: '', label: 'Auto', sub: 'Toutes origines' },
  { key: 'ja', label: '🇯🇵 Japon', sub: 'Couvertures JP' },
  { key: 'fr', label: '🇫🇷 France', sub: 'Éditions FR' },
];

const CovertestLobbyPage: React.FC = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('session');
  const [difficulty, setDifficulty] = useState<Difficulty>('Normal');
  const [length, setLength] = useState(10);
  const [guessVolume, setGuessVolume] = useState(false);
  const [guessAuthor, setGuessAuthor] = useState(false);
  const [origin, setOrigin] = useState<Origin>('');

  const launch = () =>
    navigate('/covertest/play/', {
      state: { mode, difficulty, length: mode === 'session' ? length : 1, guessVolume, guessAuthor, origin: origin || undefined },
    });

  return (
    <div className="max-w-3xl mx-auto px-6 py-16">
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-yellow-400/15 border border-yellow-400/30 text-yellow-600 dark:text-yellow-400 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
          <BookImage className="w-3.5 h-3.5" /> Cover Quest
        </div>
        <h1 className="text-5xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
          DEVINE <span className="text-yellow-400">LE MANGA</span>
        </h1>
        <p className="mt-4 text-base font-medium text-gray-500 dark:text-white/50">
          Une couverture floutée se précise à chaque essai. Reconnais-la avant la fin.
        </p>
      </div>

      <Card padding="lg" className="space-y-10">
        {/* Mode */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">Mode de jeu</p>
          <div className="grid grid-cols-2 gap-4">
            {([
              { key: 'session' as Mode, icon: Layers, title: 'Session', sub: 'Enchaîne plusieurs couvertures' },
              { key: 'single' as Mode, icon: ImageIcon, title: 'Une couverture', sub: 'Une seule manche' },
            ]).map(({ key, icon: Icon, title, sub }) => (
              <button
                key={key}
                onClick={() => setMode(key)}
                aria-pressed={mode === key}
                className={`flex flex-col items-center gap-3 p-6 rounded-3xl border-2 transition-all ${
                  mode === key ? 'border-yellow-400 bg-yellow-400/10 shadow-lg' : 'border-black/5 dark:border-white/10 hover:border-yellow-400/50'
                }`}
              >
                <Icon className={`w-9 h-9 ${mode === key ? 'text-yellow-500' : 'text-gray-400'}`} />
                <span className="manga-font text-lg text-black dark:text-white">{title}</span>
                <span className="text-[11px] font-bold uppercase tracking-widest text-gray-400 text-center">{sub}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Session length */}
        {mode === 'session' && (
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">Durée de la session</p>
            <div className="grid grid-cols-4 gap-2">
              {LENGTHS.map((n) => (
                <button
                  key={n}
                  onClick={() => setLength(n)}
                  aria-pressed={length === n}
                  className={`py-3 rounded-2xl border-2 font-black italic text-sm transition-all ${
                    length === n
                      ? 'border-yellow-400 bg-yellow-400 text-black shadow-md'
                      : 'border-black/5 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-yellow-400/50'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Difficulté */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-1">Difficulté</p>
          <p className="text-[11px] text-gray-400 mb-4">Nombre d'essais et vitesse de révélation. <span className="text-fuchsia-500 font-bold">Tryhard</span> ajoute des distorsions aléatoires (bruit, N&amp;B, couleurs inversées…) en plus du flou.</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {DIFFICULTIES.map((d) => (
              <button
                key={d.key}
                onClick={() => setDifficulty(d.key)}
                aria-pressed={difficulty === d.key}
                className={`flex flex-col items-center gap-1 py-4 rounded-2xl border-2 transition-all ${
                  difficulty === d.key ? d.active : 'border-black/5 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-yellow-400/50'
                }`}
              >
                <span className="font-black italic uppercase tracking-wide text-sm">{d.label}</span>
                <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">{d.sub}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Origine des couvertures */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-1">Origine des couvertures</p>
          <p className="text-[11px] text-gray-400 mb-4">Choisis l'édition à deviner. <span className="font-bold">Auto</span> pioche parmi toutes les origines disponibles.</p>
          <div className="grid grid-cols-3 gap-3">
            {ORIGINS.map((o) => (
              <button
                key={o.key || 'auto'}
                onClick={() => setOrigin(o.key)}
                aria-pressed={origin === o.key}
                className={`flex flex-col items-center gap-1 py-4 rounded-2xl border-2 transition-all ${
                  origin === o.key ? 'border-yellow-400 bg-yellow-400/10 text-yellow-600 dark:text-yellow-400' : 'border-black/5 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-yellow-400/50'
                }`}
              >
                <span className="font-black italic uppercase tracking-wide text-sm">{o.label}</span>
                <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">{o.sub}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Objectifs bonus */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-1">Objectifs bonus</p>
          <p className="text-[11px] text-gray-400 mb-4">Une fois le manga trouvé, gagne des points en plus.</p>
          <div className="space-y-3">
            {([
              { on: guessVolume, set: setGuessVolume, icon: Hash, title: 'Deviner le tome', sub: 'Le numéro de volume de la couverture · +30 pts' },
              { on: guessAuthor, set: setGuessAuthor, icon: PenTool, title: 'Deviner le mangaka', sub: "L'auteur de l'œuvre · +30 pts" },
            ]).map(({ on, set, icon: Icon, title, sub }) => (
              <button
                key={title}
                type="button"
                onClick={() => set((v) => !v)}
                role="switch"
                aria-checked={on}
                className={`w-full flex items-center gap-3 p-4 rounded-2xl border-2 text-left transition-all ${
                  on ? 'border-yellow-400 bg-yellow-400/10' : 'border-black/5 dark:border-white/10 hover:border-yellow-400/50'
                }`}
              >
                <Icon className={`w-5 h-5 shrink-0 ${on ? 'text-yellow-500' : 'text-gray-400'}`} />
                <div className="flex-grow">
                  <p className="font-black text-sm leading-tight">{title}</p>
                  <p className="text-[11px] font-medium opacity-50">{sub}</p>
                </div>
                <span className={`shrink-0 w-11 h-6 rounded-full p-0.5 transition-colors ${on ? 'bg-yellow-400' : 'bg-black/15 dark:bg-white/15'}`}>
                  <span className={`grid place-items-center w-5 h-5 rounded-full bg-white shadow transition-transform ${on ? 'translate-x-5' : 'translate-x-0'}`}>
                    {on && <Check className="w-3 h-3 text-yellow-500" />}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Launch */}
        <button
          onClick={launch}
          className="w-full flex items-center justify-center gap-3 bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font tracking-widest text-lg py-5 rounded-2xl border-2 border-black/10 shadow-xl hover:scale-[1.02] active:scale-95 transition-all"
        >
          <Play className="w-6 h-6 fill-current" />
          {mode === 'session' ? `Lancer la session (${length})` : 'Lancer Cover Quest'}
        </button>
      </Card>
    </div>
  );
};

export default CovertestLobbyPage;
