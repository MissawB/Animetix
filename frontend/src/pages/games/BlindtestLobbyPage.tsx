import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Disc3, Music2, Play } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { Card } from '../../components/ui/Card';

type Format = 'OP' | 'ED';
type Difficulty = 'Easy' | 'Normal' | 'Hard' | 'Impossible';

const FORMATS: { key: Format; title: string; sub: string }[] = [
  { key: 'OP', title: 'Opening', sub: 'Génériques de début' },
  { key: 'ED', title: 'Ending', sub: 'Génériques de fin' },
];

const DIFFICULTIES: { key: Difficulty; label: string; ring: string; active: string }[] = [
  { key: 'Easy', label: 'Facile', ring: 'hover:border-green-400/60', active: 'border-green-500 bg-green-500/10 text-green-600 dark:text-green-400' },
  { key: 'Normal', label: 'Normal', ring: 'hover:border-blue-400/60', active: 'border-blue-500 bg-blue-500/10 text-blue-600 dark:text-blue-400' },
  { key: 'Hard', label: 'Difficile', ring: 'hover:border-orange-400/60', active: 'border-orange-500 bg-orange-500/10 text-orange-600 dark:text-orange-400' },
  { key: 'Impossible', label: 'Impossible', ring: 'hover:border-red-500/60', active: 'border-red-600 bg-red-600/10 text-red-600 dark:text-red-400' },
];

const BlindtestLobbyPage: React.FC = () => {
  const navigate = useNavigate();
  const { difficulty, setDifficulty } = useUIStore();
  const [format, setFormat] = useState<Format>('OP');

  const activeDiff: Difficulty = difficulty === 'Custom' ? 'Normal' : difficulty;

  const launch = () => navigate('/blindtest/play/', { state: { type: format, difficulty: activeDiff } });

  return (
    <div className="max-w-3xl mx-auto px-6 py-16">
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-yellow-400/15 border border-yellow-400/30 text-yellow-600 dark:text-yellow-400 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
          <Music2 className="w-3.5 h-3.5" /> Blind Test
        </div>
        <h1 className="text-5xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
          DEVINE <span className="text-yellow-400">L'ANIMÉ</span>
        </h1>
        <p className="mt-4 text-base font-medium text-gray-500 dark:text-white/50">
          Configure ta partie, puis lance le disque.
        </p>
      </div>

      <Card padding="lg" className="space-y-10">
        {/* Format */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">Format</p>
          <div className="grid grid-cols-2 gap-4">
            {FORMATS.map((f) => (
              <button
                key={f.key}
                onClick={() => setFormat(f.key)}
                aria-pressed={format === f.key}
                className={`group relative flex flex-col items-center gap-3 p-6 rounded-3xl border-2 transition-all ${
                  format === f.key
                    ? 'border-yellow-400 bg-yellow-400/10 shadow-lg'
                    : 'border-black/5 dark:border-white/10 hover:border-yellow-400/50'
                }`}
              >
                <Disc3
                  className={`w-10 h-10 transition-transform group-hover:rotate-180 duration-700 ${
                    format === f.key ? 'text-yellow-500' : 'text-gray-400'
                  }`}
                />
                <span className="manga-font text-xl text-black dark:text-white">{f.title}</span>
                <span className="text-[11px] font-bold uppercase tracking-widest text-gray-400">{f.sub}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Difficulté */}
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-4">Difficulté</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {DIFFICULTIES.map((d) => (
              <button
                key={d.key}
                onClick={() => setDifficulty(d.key)}
                aria-pressed={activeDiff === d.key}
                className={`py-3 rounded-2xl border-2 font-black italic uppercase tracking-widest text-xs transition-all ${
                  activeDiff === d.key
                    ? d.active
                    : `border-black/5 dark:border-white/10 text-gray-500 dark:text-gray-400 ${d.ring}`
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Launch */}
        <button
          onClick={launch}
          className="w-full flex items-center justify-center gap-3 bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font tracking-widest text-lg py-5 rounded-2xl border-2 border-black/10 shadow-xl hover:scale-[1.02] active:scale-95 transition-all"
        >
          <Play className="w-6 h-6 fill-current" /> Lancer le Blind Test
        </button>
      </Card>
    </div>
  );
};

export default BlindtestLobbyPage;
