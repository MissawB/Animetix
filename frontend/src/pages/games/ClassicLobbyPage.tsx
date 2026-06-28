import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Target, Play, Clapperboard, BookOpen, Users, Globe, Tags, ScrollText,
  Calendar, Shapes, Hash, CaseSensitive, ArrowUp, ArrowDown, Check, Sparkles, Loader2,
  Trophy, SlidersHorizontal, Skull,
} from 'lucide-react';
import { classicGameService } from '../../features/games/services/classicService';
import { useToastStore } from '../../store/toastStore';
import type { ClassicHintKey } from '../../types';

type Universe = 'Anime' | 'Manga' | 'Character';
type Difficulty = 'Easy' | 'Normal' | 'Hard' | 'Impossible';
type HintMode = 'classic' | 'custom' | 'tryhard';

// Preset for the "Classique" mode (in revealing order).
const CLASSIC_PRESET: ClassicHintKey[] = ['year', 'studio', 'tags', 'desc'];

const HINT_MODES: { key: HintMode; label: string; sub: string; icon: React.ElementType }[] = [
  { key: 'classic', label: 'Classique', sub: '4 indices clés', icon: Trophy },
  { key: 'custom', label: 'Personnalisé', sub: 'À ta façon', icon: SlidersHorizontal },
  { key: 'tryhard', label: 'Tryhard', sub: 'Aucun indice', icon: Skull },
];

const UNIVERSES: { key: Universe; label: string; sub: string; icon: React.ElementType }[] = [
  { key: 'Anime', label: 'Anime', sub: 'Séries animées', icon: Clapperboard },
  { key: 'Manga', label: 'Manga', sub: 'Œuvres papier', icon: BookOpen },
  { key: 'Character', label: 'Personnages', sub: 'Héros & figures', icon: Users },
];

const DIFFICULTIES: { key: Difficulty; label: string; sub: string; active: string }[] = [
  { key: 'Easy', label: 'Facile', sub: 'Titres très connus', active: 'border-green-500 bg-green-500/10 text-green-600 dark:text-green-400' },
  { key: 'Normal', label: 'Normal', sub: 'Grand public', active: 'border-blue-500 bg-blue-500/10 text-blue-600 dark:text-blue-400' },
  { key: 'Hard', label: 'Difficile', sub: 'Pour connaisseurs', active: 'border-orange-500 bg-orange-500/10 text-orange-600 dark:text-orange-400' },
  { key: 'Impossible', label: 'Impossible', sub: 'Pépites obscures', active: 'border-red-600 bg-red-600/10 text-red-600 dark:text-red-400' },
];

const HINT_DEFS: Record<ClassicHintKey, { label: string; desc: string; icon: React.ElementType; tone: string }> = {
  year:   { label: 'Année de sortie', desc: 'Année de parution', icon: Calendar, tone: 'text-blue-500' },
  origin: { label: 'Origine', desc: "Œuvre / pays d'origine", icon: Globe, tone: 'text-teal-500' },
  tags:   { label: 'Tags', desc: 'Principaux thèmes', icon: Tags, tone: 'text-yellow-500' },
  genres: { label: 'Genres', desc: 'Catégories principales', icon: Shapes, tone: 'text-orange-500' },
  studio: { label: 'Studio', desc: "Studio d'animation / éditeur", icon: Clapperboard, tone: 'text-purple-500' },
  letter: { label: 'Première lettre', desc: 'La lettre initiale du titre', icon: CaseSensitive, tone: 'text-pink-500' },
  words:  { label: 'Nombre de mots', desc: 'Combien de mots dans le titre', icon: Hash, tone: 'text-cyan-500' },
  desc:   { label: 'Description', desc: 'Extrait du synopsis', icon: ScrollText, tone: 'text-green-500' },
};

const UNLOCK_STEP = 5;

const Section: React.FC<{ step: number; title: string; hint?: string; children: React.ReactNode }> = ({ step, title, hint, children }) => (
  <div>
    <div className="flex items-baseline gap-3 mb-4">
      <span className="shrink-0 w-6 h-6 rounded-lg bg-blue-500/10 text-blue-500 grid place-items-center font-black text-xs">{step}</span>
      <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-400 dark:text-gray-500">{title}</h2>
      {hint && <span className="text-[11px] font-bold text-gray-400/80">{hint}</span>}
    </div>
    {children}
  </div>
);

const ClassicLobbyPage: React.FC = () => {
  const navigate = useNavigate();
  const addToast = useToastStore((s) => s.addToast);

  const [universe, setUniverse] = useState<Universe>('Anime');
  const [difficulty, setDifficulty] = useState<Difficulty>('Normal');
  const [hintMode, setHintMode] = useState<HintMode>('classic');
  const [hintOrder, setHintOrder] = useState<ClassicHintKey[]>(['year', 'origin', 'tags', 'genres', 'studio', 'letter', 'words', 'desc']);
  const [enabled, setEnabled] = useState<Record<ClassicHintKey, boolean>>({
    year: true, tags: true, genres: true, studio: true, desc: true, origin: false, letter: false, words: false,
  });
  const [launching, setLaunching] = useState(false);

  const customConfig = hintOrder.filter((k) => enabled[k]);
  const config =
    hintMode === 'classic' ? CLASSIC_PRESET : hintMode === 'tryhard' ? [] : customConfig;

  const move = (index: number, dir: -1 | 1) => {
    const target = index + dir;
    if (target < 0 || target >= hintOrder.length) return;
    setHintOrder((prev) => {
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const toggle = (key: ClassicHintKey) => setEnabled((prev) => ({ ...prev, [key]: !prev[key] }));

  const launch = async () => {
    if (launching) return;
    setLaunching(true);
    try {
      await classicGameService.start(universe, difficulty, config);
      navigate('/game/classic/play/');
    } catch {
      addToast("Impossible de lancer la partie. Réessayez.", 'error');
      setLaunching(false);
    }
  };

  // Unlock threshold of an enabled hint, by its position among enabled ones.
  const unlockAt = (key: ClassicHintKey) => (config.indexOf(key) + 1) * UNLOCK_STEP;

  return (
    <div className="max-w-3xl mx-auto px-6 py-14">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
          <Target className="w-3.5 h-3.5" /> Déduction
        </div>
        <h1 className="text-5xl md:text-6xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
          ANIMETIX <span className="text-blue-500">CLASSIQUE</span>
        </h1>
        <p className="mt-4 text-base font-medium text-gray-500 dark:text-white/50">
          Configure ta traque, puis pars démasquer l'œuvre mystère.
        </p>
      </div>

      <div className="rounded-[2.5rem] border-2 border-black/5 dark:border-white/10 bg-surface-card p-7 md:p-9 shadow-token-card space-y-10">
        {/* Univers */}
        <Section step={1} title="Univers">
          <div className="grid grid-cols-3 gap-3 sm:gap-4">
            {UNIVERSES.map(({ key, label, sub, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setUniverse(key)}
                aria-pressed={universe === key}
                className={`flex flex-col items-center gap-3 p-5 sm:p-6 rounded-3xl border-2 transition-all ${
                  universe === key ? 'border-blue-500 bg-blue-500/10 shadow-lg' : 'border-black/5 dark:border-white/10 hover:border-blue-500/50'
                }`}
              >
                <Icon className={`w-8 h-8 sm:w-9 sm:h-9 ${universe === key ? 'text-blue-500' : 'text-gray-400'}`} />
                <span className="manga-font text-base sm:text-lg text-black dark:text-white text-center leading-none">{label}</span>
                <span className="text-[10px] sm:text-[11px] font-bold uppercase tracking-widest text-gray-400 text-center">{sub}</span>
              </button>
            ))}
          </div>
        </Section>

        {/* Difficulté */}
        <Section step={2} title="Difficulté" hint="Rareté de l'œuvre à trouver">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {DIFFICULTIES.map((d) => (
              <button
                key={d.key}
                onClick={() => setDifficulty(d.key)}
                aria-pressed={difficulty === d.key}
                className={`flex flex-col items-center gap-1 py-4 rounded-2xl border-2 transition-all ${
                  difficulty === d.key ? d.active : 'border-black/5 dark:border-white/10 text-gray-500 dark:text-gray-400 hover:border-blue-500/40'
                }`}
              >
                <span className="font-black italic uppercase tracking-wide text-sm">{d.label}</span>
                <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">{d.sub}</span>
              </button>
            ))}
          </div>
        </Section>

        {/* Indices */}
        <Section
          step={3}
          title="Indices"
          hint={config.length === 0 ? 'aucun indice' : `${config.length} indice${config.length > 1 ? 's' : ''}`}
        >
          {/* Mode selector */}
          <div className="grid grid-cols-3 gap-3 mb-5">
            {HINT_MODES.map(({ key, label, sub, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setHintMode(key)}
                aria-pressed={hintMode === key}
                className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all ${
                  hintMode === key ? 'border-blue-500 bg-blue-500/10 shadow-lg' : 'border-black/5 dark:border-white/10 hover:border-blue-500/50'
                }`}
              >
                <Icon className={`w-6 h-6 ${hintMode === key ? 'text-blue-500' : 'text-gray-400'}`} />
                <span className="manga-font text-sm text-black dark:text-white leading-none">{label}</span>
                <span className="text-[9px] font-bold uppercase tracking-widest text-gray-400 text-center">{sub}</span>
              </button>
            ))}
          </div>

          {/* Classique — read-only preview */}
          {hintMode === 'classic' && (
            <ul className="space-y-2.5">
              {CLASSIC_PRESET.map((key, i) => {
                const def = HINT_DEFS[key];
                const Icon = def.icon;
                return (
                  <li key={key} className="flex items-center gap-3 rounded-2xl border-2 border-blue-500/30 bg-blue-500/[0.05] p-3">
                    <Icon className={`w-5 h-5 shrink-0 ${def.tone}`} />
                    <div className="min-w-0 flex-grow">
                      <p className="font-black text-sm leading-tight truncate">{def.label}</p>
                      <p className="text-[11px] font-medium opacity-50 truncate">{def.desc}</p>
                    </div>
                    <span className="shrink-0 text-[10px] font-black uppercase tracking-wider text-blue-500 bg-blue-500/10 px-2.5 py-1 rounded-full tabular-nums">
                      {(i + 1) * UNLOCK_STEP} essais
                    </span>
                  </li>
                );
              })}
            </ul>
          )}

          {/* Tryhard — no hints */}
          {hintMode === 'tryhard' && (
            <div className="rounded-2xl border-2 border-red-500/30 bg-red-500/[0.06] p-6 text-center">
              <Skull className="w-9 h-9 text-red-500 mx-auto mb-3" />
              <p className="font-black italic uppercase text-red-500">Aucun indice</p>
              <p className="text-xs font-bold opacity-50 mt-1">Juste toi, ton instinct et la chaleur des tentatives. Pour les vrais.</p>
            </div>
          )}

          {/* Personnalisé — editable list */}
          {hintMode === 'custom' && (
            <>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-4">
                Active les indices voulus et range-les : ils se débloqueront dans cet ordre, un toutes les {UNLOCK_STEP} tentatives.
              </p>
              <ul className="space-y-2.5">
                {hintOrder.map((key, i) => {
                  const def = HINT_DEFS[key];
                  const Icon = def.icon;
                  const on = enabled[key];
                  return (
                    <li
                      key={key}
                      className={`flex items-center gap-3 rounded-2xl border-2 p-3 transition-all ${
                        on ? 'border-blue-500/40 bg-blue-500/[0.05]' : 'border-black/5 dark:border-white/10 opacity-60'
                      }`}
                    >
                      {/* Reorder */}
                      <div className="flex flex-col">
                        <button
                          onClick={() => move(i, -1)}
                          disabled={i === 0}
                          aria-label={`Monter ${def.label}`}
                          className="p-0.5 rounded text-gray-400 hover:text-blue-500 disabled:opacity-20 disabled:hover:text-gray-400 transition-colors"
                        >
                          <ArrowUp className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => move(i, 1)}
                          disabled={i === hintOrder.length - 1}
                          aria-label={`Descendre ${def.label}`}
                          className="p-0.5 rounded text-gray-400 hover:text-blue-500 disabled:opacity-20 disabled:hover:text-gray-400 transition-colors"
                        >
                          <ArrowDown className="w-4 h-4" />
                        </button>
                      </div>

                      <Icon className={`w-5 h-5 shrink-0 ${on ? def.tone : 'text-gray-400'}`} />

                      <div className="min-w-0 flex-grow">
                        <p className="font-black text-sm leading-tight truncate">{def.label}</p>
                        <p className="text-[11px] font-medium opacity-50 truncate">{def.desc}</p>
                      </div>

                      {/* Unlock badge */}
                      {on && (
                        <span className="shrink-0 text-[10px] font-black uppercase tracking-wider text-blue-500 bg-blue-500/10 px-2.5 py-1 rounded-full tabular-nums">
                          {unlockAt(key)} essais
                        </span>
                      )}

                      {/* Toggle */}
                      <button
                        onClick={() => toggle(key)}
                        role="switch"
                        aria-checked={on}
                        aria-label={`${on ? 'Désactiver' : 'Activer'} ${def.label}`}
                        className={`shrink-0 w-11 h-6 rounded-full p-0.5 transition-colors ${on ? 'bg-blue-500' : 'bg-black/15 dark:bg-white/15'}`}
                      >
                        <span className={`grid place-items-center w-5 h-5 rounded-full bg-white shadow transition-transform ${on ? 'translate-x-5' : 'translate-x-0'}`}>
                          {on && <Check className="w-3 h-3 text-blue-500" />}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </Section>

        {/* Launch */}
        <button
          onClick={launch}
          disabled={launching}
          className="w-full flex items-center justify-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-black italic manga-font tracking-widest text-lg py-5 rounded-2xl shadow-xl shadow-blue-600/20 hover:scale-[1.01] active:scale-95 transition-all disabled:opacity-60 disabled:hover:scale-100"
        >
          {launching ? (
            <><Loader2 className="w-6 h-6 animate-spin" /> Préparation…</>
          ) : (
            <><Play className="w-6 h-6 fill-current" /> Lancer la partie</>
          )}
        </button>
        <p className="-mt-4 text-center text-[11px] font-bold uppercase tracking-widest text-gray-400 flex items-center justify-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-500" />
          {UNIVERSES.find((u) => u.key === universe)?.label} · {DIFFICULTIES.find((d) => d.key === difficulty)?.label} · {HINT_MODES.find((m) => m.key === hintMode)?.label} ({config.length} indice{config.length > 1 ? 's' : ''})
        </p>
      </div>
    </div>
  );
};

export default ClassicLobbyPage;
