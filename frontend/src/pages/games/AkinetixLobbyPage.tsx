import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Brain, Play, Clapperboard, BookOpen, Users, Bot, MessageCircleQuestion, Sparkles,
} from 'lucide-react';

type Universe = 'Anime' | 'Manga' | 'Character';
type Mode = 'classique' | 'animinator';

const MODES: {
  key: Mode;
  label: string;
  sub: string;
  desc: string;
  icon: React.ElementType;
  route: string;
}[] = [
  {
    key: 'classique',
    label: 'Akinetix Classique',
    sub: "L'IA devine",
    desc: "L'IA te pose des questions (oui / non / probablement…) et tente de deviner à quoi tu penses.",
    icon: Brain,
    route: '/akinetix/play/',
  },
  {
    key: 'animinator',
    label: 'Animinator',
    sub: 'Tu interroges le génie',
    desc: 'Le génie a une œuvre en tête : pose-lui tes questions librement pour la démasquer.',
    icon: Bot,
    route: '/animinator/',
  },
];

const UNIVERSES: { key: Universe; label: string; sub: string; icon: React.ElementType }[] = [
  { key: 'Anime', label: 'Anime', sub: 'Séries animées', icon: Clapperboard },
  { key: 'Manga', label: 'Manga', sub: 'Œuvres papier', icon: BookOpen },
  { key: 'Character', label: 'Personnages', sub: 'Héros & figures', icon: Users },
];

const Section: React.FC<{ step: number; title: string; children: React.ReactNode }> = ({
  step,
  title,
  children,
}) => (
  <div>
    <div className="flex items-baseline gap-3 mb-4">
      <span className="shrink-0 w-6 h-6 rounded-lg bg-blue-500/10 text-blue-500 grid place-items-center font-black text-xs">
        {step}
      </span>
      <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-400 dark:text-gray-500">
        {title}
      </h2>
    </div>
    {children}
  </div>
);

const AkinetixLobbyPage: React.FC = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('classique');
  const [universe, setUniverse] = useState<Universe>('Anime');

  const launch = () => {
    const target = MODES.find((m) => m.key === mode);
    if (target) navigate(target.route, { state: { mediaType: universe } });
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-14">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
          <MessageCircleQuestion className="w-3.5 h-3.5" /> Lecture de pensées
        </div>
        <h1 className="text-5xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
          AKI<span className="text-blue-500">NETIX</span>
        </h1>
        <p className="mt-4 text-base font-medium text-gray-500 dark:text-white/50">
          Choisis ton mode et ton univers, puis laisse la magie opérer.
        </p>
      </div>

      <div className="rounded-[2.5rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-7 md:p-9 shadow-token-card space-y-10">
        {/* Mode */}
        <Section step={1} title="Mode de jeu">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {MODES.map(({ key, label, sub, desc, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setMode(key)}
                aria-pressed={mode === key}
                className={`flex flex-col items-start gap-3 p-5 rounded-3xl border-2 text-left transition-all ${
                  mode === key
                    ? 'border-blue-500 bg-blue-500/10 shadow-lg'
                    : 'border-black/5 dark:border-white/10 hover:border-blue-500/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-8 h-8 ${mode === key ? 'text-blue-500' : 'text-gray-400'}`} />
                  <div>
                    <span className="block manga-font text-lg text-black dark:text-white leading-none">
                      {label}
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                      {sub}
                    </span>
                  </div>
                </div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 leading-relaxed">
                  {desc}
                </p>
              </button>
            ))}
          </div>
        </Section>

        {/* Univers */}
        <Section step={2} title="Univers">
          <div className="grid grid-cols-3 gap-3 sm:gap-4">
            {UNIVERSES.map(({ key, label, sub, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setUniverse(key)}
                aria-pressed={universe === key}
                className={`flex flex-col items-center gap-3 p-5 sm:p-6 rounded-3xl border-2 transition-all ${
                  universe === key
                    ? 'border-blue-500 bg-blue-500/10 shadow-lg'
                    : 'border-black/5 dark:border-white/10 hover:border-blue-500/50'
                }`}
              >
                <Icon className={`w-8 h-8 sm:w-9 sm:h-9 ${universe === key ? 'text-blue-500' : 'text-gray-400'}`} />
                <span className="manga-font text-base sm:text-lg text-black dark:text-white text-center leading-none">
                  {label}
                </span>
                <span className="text-[10px] sm:text-[11px] font-bold uppercase tracking-widest text-gray-400 text-center">
                  {sub}
                </span>
              </button>
            ))}
          </div>
        </Section>

        {/* Launch */}
        <button
          onClick={launch}
          className="w-full flex items-center justify-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-black italic manga-font tracking-widest text-lg py-5 rounded-2xl shadow-xl shadow-blue-600/20 hover:scale-[1.01] active:scale-95 transition-all"
        >
          <Play className="w-6 h-6 fill-current" /> Lancer la partie
        </button>
        <p className="-mt-4 text-center text-[11px] font-bold uppercase tracking-widest text-gray-400 flex items-center justify-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-500" />
          {MODES.find((m) => m.key === mode)?.label} · {UNIVERSES.find((u) => u.key === universe)?.label}
        </p>
      </div>
    </div>
  );
};

export default AkinetixLobbyPage;
