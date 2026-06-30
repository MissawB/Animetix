import React, { useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import useSocket from '../../hooks/useSocket';
import {
  Users, Send, Crown, Play, RotateCcw, Check, Vote,
  Fingerprint, Copy, Radio, Lock, Skull, HelpCircle, Ghost, Globe, EyeOff,
} from 'lucide-react';

interface UPlayer {
  id: string;
  name: string;
  is_host?: boolean;
  has_voted?: boolean;
  alive?: boolean;
  role?: string;
  word?: string;
  image?: string;
}
interface UMsg { user: string; text: string; is_system?: boolean }
interface UResult { winner: string; reason?: string; mrwhite_winners?: string[] }

const CATEGORIES: { key: string; label: string; anchor?: boolean }[] = [
  { key: 'Anime', label: 'Anime', anchor: true },
  { key: 'Manga', label: 'Manga', anchor: true },
  { key: 'Character', label: 'Persos anime', anchor: true },
  { key: 'Movie', label: 'Films' },
  { key: 'Game', label: 'Jeux vidéo' },
  { key: 'Actor', label: 'Acteurs' },
  { key: 'VGChar', label: 'Persos de jeux' },
];
const ANCHOR_KEYS = CATEGORIES.filter((c) => c.anchor).map((c) => c.key);
const DIFFS = ['Easy', 'Normal', 'Hard'];
const DIFF_LABEL: Record<string, string> = { Easy: 'Facile', Normal: 'Normal', Hard: 'Difficile' };
const DIFF_HINT: Record<string, string> = {
  Easy: 'œuvres très populaires',
  Normal: 'œuvres connues',
  Hard: 'œuvres plus pointues',
};
const MIN_PLAYERS = 3;

const STATUS: Record<string, string> = {
  lobby: 'Briefing en cours — recrutez votre unité',
  playing: 'Infiltration en cours — votez pour éliminer',
  mrwhite_guess: 'Un Mr. White tente de deviner le mot…',
  ended: 'Mission terminée — dossier déclassifié',
};

// Badge style for a revealed role.
const roleMeta = (role?: string): { label: string; cls: string } => {
  if (role === 'Undercover') return { label: '⚠ Intrus', cls: 'text-red-400' };
  if (role === 'MrWhite') return { label: '◐ Mr. White', cls: 'text-purple-300' };
  return { label: '✓ Civil', cls: 'text-green-400' };
};

const UndercoverRoom: React.FC = () => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const [searchParams] = useSearchParams();
  // Only meaningful when *creating* the room (carried from the chooser); the
  // server ignores it once the room exists.
  const createVisibility = searchParams.get('visibility') || undefined;
  const extraQuery = useMemo(
    () => (createVisibility ? { visibility: createVisibility } : undefined),
    [createVisibility],
  );
  const { gameState, connected, sendAction } = useSocket(roomCode, 'undercover', extraQuery);
  const [name, setName] = useState('');
  const [chat, setChat] = useState('');
  const [guess, setGuess] = useState('');
  // Local vote highlight, keyed by round so it auto-clears each new round.
  const [vote, setVote] = useState<{ round: number; target: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const gs = (gameState || {}) as Record<string, unknown>;
  const players = (gs.players as UPlayer[]) || [];
  const myId = gs.myId as string | undefined;
  const me = players.find((p) => p.id === myId);
  const isHost = !!me?.is_host;
  const state = (gs.state as string) || 'lobby';
  const messages = (gs.messages as UMsg[]) || [];
  const myRole = (gs.private_role as UPlayer) || {};
  const categories = (gs.categories as string[]) || ['Anime'];
  const difficulty = (gs.difficulty as string) || 'Normal';
  const visibility = (gs.visibility as string) || 'private';
  const isPublic = visibility === 'public';
  const numUnder = (gs.num_undercovers as number) || 1;
  const numWhite = (gs.num_mrwhites as number) || 0;
  const round = (gs.round as number) || 0;
  const pendingWhite = gs.pending_white as string | undefined;
  const pendingWhiteName = gs.pending_white_name as string | undefined;
  const result = gs.result as UResult | null;
  const civilWord = gs.civil_word as string | undefined;
  const undercoverWord = gs.undercover_word as string | undefined;

  const hasAnchor = categories.some((c) => ANCHOR_KEYS.includes(c));
  // Threats (intrus + Mr. White) cap so civils keep a majority at the start.
  const maxThreats = Math.max(1, Math.floor((players.length - 1) / 2));
  const under = Math.min(numUnder, Math.max(1, maxThreats - numWhite));
  const white = Math.min(numWhite, Math.max(0, maxThreats - under));
  const civilsCount = Math.max(0, players.length - under - white);
  // Highlight only the vote cast this round (server clears votes each round).
  const voteTarget = vote && vote.round === round ? vote.target : null;

  // Paints a range slider's filled portion + themes its thumb (see .uc-slider).
  const sliderStyle = (value: number, min: number, max: number, accent: string): React.CSSProperties => {
    // Fill tracks the thumb position; a degenerate (min==max) slider sits at 0.
    const pct = max > min ? ((value - min) / (max - min)) * 100 : 0;
    return {
      background: `linear-gradient(90deg, ${accent} 0%, ${accent} ${pct}%, rgba(255,255,255,0.08) ${pct}%, rgba(255,255,255,0.08) 100%)`,
      ['--uc-accent' as string]: accent,
    };
  };
  const maxUnderSlider = Math.max(1, maxThreats - white);
  const maxWhiteSlider = Math.max(0, maxThreats - under);

  if (!connected) {
    return (
      <div className="min-h-[60vh] grid place-items-center">
        <div className="flex flex-col items-center gap-4 text-red-400">
          <Radio className="w-12 h-12 animate-pulse" />
          <p className="font-black uppercase tracking-[0.4em] animate-pulse">Connexion au réseau sécurisé…</p>
        </div>
      </div>
    );
  }

  const submitName = () => { if (name.trim()) sendAction('set_name', { name: name.trim() }); };
  const iAmAlive = me?.alive !== false;
  const castVote = (id: string) => {
    const target = players.find((p) => p.id === id);
    if (state !== 'playing' || id === myId || !iAmAlive || target?.alive === false) return;
    setVote({ round, target: id });
    sendAction('vote', { voted_for: id });
  };
  const submitGuess = (e: React.FormEvent) => {
    e.preventDefault();
    if (guess.trim()) { sendAction('mrwhite_guess', { guess: guess.trim() }); setGuess(''); }
  };
  const sendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (chat.trim()) { sendAction('chat', { message: chat.trim() }); setChat(''); }
  };
  const code = (roomCode || '').toUpperCase();
  const copyCode = () => {
    navigator.clipboard?.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  // set_settings carries the full settings tuple — merge so changing one knob
  // doesn't reset the others.
  const applySettings = (patch: Record<string, unknown>) =>
    sendAction('set_settings', {
      categories, difficulty, num_undercovers: under, num_mrwhites: white, visibility, ...patch,
    });
  const toggleCategory = (key: string) => {
    const next = categories.includes(key)
      ? categories.filter((c) => c !== key)
      : [...categories, key];
    applySettings({ categories: next });
  };

  const iAmPendingWhite = state === 'mrwhite_guess' && pendingWhite === myId;
  const isMrWhite = myRole.role === 'MrWhite';

  const panel = 'rounded-[2rem] border-2 border-white/5 bg-[#0d0f17]/80 backdrop-blur-xl shadow-2xl';

  // ── Winner banner content (ended) ───────────────────────────────────────
  const winnerBanner = () => {
    const w = result?.winner;
    const whites = result?.mrwhite_winners || [];
    if (w === 'civils') return { cls: 'bg-green-500/10 border-green-500', title: '🎯 Les Civils gagnent !', sub: 'Toutes les menaces ont été démasquées.' };
    if (w === 'mrwhite') return { cls: 'bg-purple-500/10 border-purple-400', title: '◐ Mr. White gagne !', sub: `${whites.join(', ')} a deviné le mot des civils.` };
    return {
      cls: 'bg-red-500/10 border-red-500',
      title: '🕵️ Les infiltrés gagnent !',
      sub: whites.length ? `Mr. White ${whites.join(', ')} survit jusqu'au bout.` : 'Ils ont atteint la parité.',
    };
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      {/* ── Mission banner ───────────────────────────────── */}
      <div className="relative overflow-hidden rounded-[2.5rem] border-2 border-red-500/30 bg-gradient-to-br from-red-950/50 via-[#0d0f17] to-[#0d0f17] p-7 sm:p-9 mb-8 shadow-[0_0_60px_-15px_rgba(239,68,68,0.4)]">
        <div
          className="absolute inset-0 opacity-[0.07] pointer-events-none"
          style={{ backgroundImage: 'repeating-linear-gradient(45deg, #fff 0 2px, transparent 2px 14px)' }}
        />
        <div className="absolute -right-10 -top-10 w-48 h-48 bg-red-600/20 blur-[80px] rounded-full pointer-events-none" />
        <div className="relative">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.4em] text-red-500 mb-3">
            <Fingerprint className="w-4 h-4" /> Dossier classifié · Undercover
            <span className="ml-2 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-500/15 text-red-400 normal-case tracking-wider">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> {players.length} agent{players.length > 1 ? 's' : ''}
            </span>
            {round > 0 && state !== 'ended' && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-white/10 text-white/60 normal-case tracking-wider">Manche {round}</span>
            )}
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full normal-case tracking-wider ${isPublic ? 'bg-green-500/15 text-green-400' : 'bg-white/10 text-white/60'}`}>
              {isPublic ? <Globe className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}{isPublic ? 'Public' : 'Privé'}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
            <h1 className="text-5xl sm:text-7xl font-black italic manga-font uppercase tracking-tighter text-white leading-none">
              Mission
            </h1>
            <button
              onClick={copyCode}
              title="Copier le code de la salle"
              className="group inline-flex items-center gap-3 rounded-2xl border-2 border-red-500/40 bg-red-500/10 hover:bg-red-500/20 px-5 py-2.5 transition-all"
            >
              <span className="text-3xl sm:text-4xl font-black tracking-[0.25em] text-red-400 font-mono">{code}</span>
              {copied ? <Check className="w-5 h-5 text-green-400" /> : <Copy className="w-5 h-5 text-red-400 opacity-60 group-hover:opacity-100" />}
            </button>
          </div>
          <p className="mt-3 text-sm font-bold uppercase tracking-widest text-white/40">{STATUS[state]}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Roster ─────────────────────────────────────── */}
        <div className={`${panel} p-6 h-fit lg:col-span-1`}>
          <h3 className="text-[11px] font-black uppercase opacity-40 mb-5 tracking-[0.25em] flex items-center gap-2">
            <Users className="w-4 h-4" /> Unité d'élite
          </h3>
          <div className="space-y-2.5">
            {players.length === 0 && <p className="text-sm italic opacity-30">En attente d'agents…</p>}
            {players.map((p, i) => {
              const isMe = p.id === myId;
              const dead = p.alive === false;
              const voted = state === 'playing' && p.id === voteTarget;
              const clickable = state === 'playing' && !isMe && iAmAlive && !dead;
              const meta = roleMeta(p.role);
              const showRole = state === 'ended' || dead;
              return (
                <button
                  key={p.id}
                  onClick={() => castVote(p.id)}
                  disabled={!clickable}
                  className={`w-full flex items-center gap-3 p-3 rounded-2xl border-2 text-left transition-all ${
                    dead ? 'border-white/5 bg-white/[0.01] opacity-50'
                    : voted ? 'border-red-500 bg-red-500/10'
                    : clickable ? 'border-white/5 bg-white/[0.03] hover:border-red-500/50 hover:bg-red-500/5 cursor-pointer'
                    : 'border-white/5 bg-white/[0.03] cursor-default'
                  }`}
                >
                  <div className={`relative w-11 h-11 rounded-xl grid place-items-center font-black italic shadow-lg shrink-0 ${dead ? 'bg-white/10 text-white/40' : isMe ? 'bg-yellow-400 text-black' : 'bg-gradient-to-br from-navy-700 to-navy-900 text-white/80'}`}>
                    {dead ? <Skull className="w-5 h-5" /> : (p.name || '?')[0].toUpperCase()}
                    <span className="absolute -bottom-1 -right-1 text-[8px] font-black bg-black/80 text-white/60 rounded-md px-1 leading-tight">{String(i + 1).padStart(2, '0')}</span>
                  </div>
                  <div className="min-w-0 flex-grow">
                    <span className={`font-bold truncate block ${dead ? 'text-white/50 line-through' : 'text-white'}`}>{p.name}{isMe && <span className="text-yellow-400/70"> · toi</span>}</span>
                    {showRole && p.role ? (
                      <span className={`text-[11px] font-black uppercase ${meta.cls}`}>
                        {meta.label}{p.role !== 'MrWhite' && p.word ? ` · ${p.word}` : ''}
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold uppercase tracking-widest text-white/25">{dead ? 'Éliminé' : 'Agent'}</span>
                    )}
                  </div>
                  {p.is_host && <Crown className="w-4 h-4 text-yellow-400 shrink-0" />}
                  {state === 'playing' && !dead && p.has_voted && <Check className="w-4 h-4 text-green-400 shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Game + chat ─────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-6">
          <div className={`${panel} p-7`}>
            {/* LOBBY */}
            {state === 'lobby' && (
              <div className="space-y-7">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.25em] text-yellow-400/70 mb-2">Nom de code {me?.name ? `· ${me.name}` : ''}</p>
                  <div className="flex gap-3">
                    <input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') submitName(); }}
                      placeholder="Choisis un pseudo d'agent…"
                      maxLength={15}
                      aria-label="Nom de code"
                      className="flex-grow p-3.5 rounded-2xl bg-white/[0.04] border-2 border-white/10 focus:border-yellow-400 outline-none font-bold text-white placeholder:text-white/25 transition-colors"
                    />
                    <button onClick={submitName} className="px-6 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic uppercase tracking-wide transition-colors">Valider</button>
                  </div>
                </div>

                {isHost ? (
                  <>
                    <div>
                      <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">Visibilité du salon</p>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => applySettings({ visibility: 'public' })}
                          className={`flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${isPublic ? 'border-green-500 bg-green-500/15 text-green-400' : 'border-white/10 text-white/40 hover:border-green-500/40'}`}
                        ><Globe className="w-3.5 h-3.5" /> Public</button>
                        <button
                          onClick={() => applySettings({ visibility: 'private' })}
                          className={`flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${!isPublic ? 'border-red-500 bg-red-500/15 text-red-400' : 'border-white/10 text-white/40 hover:border-red-500/40'}`}
                        ><EyeOff className="w-3.5 h-3.5" /> Privé</button>
                      </div>
                      <p className="mt-2 text-[11px] text-white/35 italic">
                        {isPublic ? 'Visible dans la liste des salons publics — tout le monde peut rejoindre.' : 'Accessible uniquement via le code ou l\'URL.'}
                      </p>
                    </div>
                    <div>
                      <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">Catégories à inclure</p>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {CATEGORIES.map((c) => {
                          const on = categories.includes(c.key);
                          return (
                            <button
                              key={c.key}
                              onClick={() => toggleCategory(c.key)}
                              className={`flex items-center gap-2 py-2.5 px-3 rounded-xl border-2 text-xs font-black uppercase transition-all ${on ? 'border-red-500 bg-red-500/15 text-red-400' : 'border-white/10 text-white/40 hover:border-red-500/40'}`}
                            >
                              <span className={`w-4 h-4 rounded grid place-items-center border-2 shrink-0 ${on ? 'bg-red-500 border-red-500' : 'border-white/25'}`}>
                                {on && <Check className="w-3 h-3 text-white" />}
                              </span>
                              <span className="truncate">{c.label}{c.anchor && <span className="text-yellow-400/70"> ⚓</span>}</span>
                            </button>
                          );
                        })}
                      </div>
                      <p className={`mt-2 text-[11px] italic ${hasAnchor ? 'text-white/35' : 'text-red-400'}`}>
                        ⚓ Au moins une catégorie ancre (anime/manga/perso) doit être cochée — chaque paire en garde un mot.
                      </p>
                    </div>

                    <div>
                      <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">Difficulté · popularité</p>
                      <div className="grid grid-cols-3 gap-2">
                        {DIFFS.map((d) => (
                          <button
                            key={d}
                            onClick={() => applySettings({ difficulty: d })}
                            className={`py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${difficulty === d ? 'border-red-500 bg-red-500/15 text-red-400' : 'border-white/10 text-white/40 hover:border-red-500/40'}`}
                          >{DIFF_LABEL[d]}</button>
                        ))}
                      </div>
                      <p className="mt-2 text-[11px] text-white/35 italic">{DIFF_HINT[difficulty]} — plus c'est dur, plus les œuvres sont obscures.</p>
                    </div>

                    {/* Sliders : intrus + Mr. White, bornés par la taille du lobby */}
                    <div className="space-y-6">
                      <div>
                        <div className="flex items-center justify-between mb-2.5">
                          <p className="text-[11px] font-black uppercase tracking-[0.25em] text-red-400/80 flex items-center gap-1.5"><Vote className="w-3.5 h-3.5" /> Intrus</p>
                          <span className="min-w-9 text-center px-2.5 py-1 rounded-lg bg-red-500/15 text-red-400 text-base font-black tabular-nums shadow-[0_0_14px_-4px_rgba(239,68,68,0.6)]">{under}</span>
                        </div>
                        <input
                          type="range" min={1} max={maxUnderSlider} value={under}
                          onChange={(e) => applySettings({ num_undercovers: Number(e.target.value) })}
                          className="uc-slider"
                          style={sliderStyle(under, 1, maxUnderSlider, '#ef4444')}
                          aria-label="Nombre d'intrus"
                        />
                        <div className="flex justify-between mt-1.5 text-[10px] font-bold text-white/25 tabular-nums"><span>1</span><span>max {maxUnderSlider}</span></div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-2.5">
                          <p className="text-[11px] font-black uppercase tracking-[0.25em] text-purple-300/80 flex items-center gap-1.5"><Ghost className="w-3.5 h-3.5" /> Mr. White</p>
                          <span className="min-w-9 text-center px-2.5 py-1 rounded-lg bg-purple-500/15 text-purple-300 text-base font-black tabular-nums shadow-[0_0_14px_-4px_rgba(192,132,252,0.6)]">{white}</span>
                        </div>
                        <input
                          type="range" min={0} max={maxWhiteSlider} value={white}
                          onChange={(e) => applySettings({ num_mrwhites: Number(e.target.value) })}
                          className="uc-slider"
                          style={sliderStyle(white, 0, maxWhiteSlider, '#c084fc')}
                          aria-label="Nombre de Mr. White"
                        />
                        <div className="flex justify-between mt-1.5 text-[10px] font-bold text-white/25 tabular-nums"><span>0</span><span>max {maxWhiteSlider}</span></div>
                        <p className="mt-2 text-[11px] text-white/35 italic">Le Mr. White n'a pas de mot : éliminé, il doit deviner celui des civils pour gagner.</p>
                      </div>
                      {/* Composition bar */}
                      <div>
                        <div className="flex h-2.5 rounded-full overflow-hidden bg-white/5">
                          {civilsCount > 0 && <div className="bg-green-500/70" style={{ width: `${(civilsCount / Math.max(1, players.length)) * 100}%` }} />}
                          {under > 0 && <div className="bg-red-500/70" style={{ width: `${(under / Math.max(1, players.length)) * 100}%` }} />}
                          {white > 0 && <div className="bg-purple-400/70" style={{ width: `${(white / Math.max(1, players.length)) * 100}%` }} />}
                        </div>
                        <div className="flex flex-wrap items-center gap-2 mt-3 text-[11px] font-black uppercase tracking-wider">
                          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-green-500/10 text-green-400"><span className="w-2 h-2 rounded-full bg-green-500" />{civilsCount} civils</span>
                          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400"><span className="w-2 h-2 rounded-full bg-red-500" />{under} intrus</span>
                          {white > 0 && <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-300"><span className="w-2 h-2 rounded-full bg-purple-400" />{white} Mr. White</span>}
                        </div>
                      </div>
                    </div>

                    <div>
                      <button
                        onClick={() => sendAction('start_game')}
                        disabled={players.length < MIN_PLAYERS || !hasAnchor}
                        className="w-full py-4 rounded-2xl bg-red-600 enabled:hover:bg-red-500 text-white font-black italic uppercase tracking-widest text-lg shadow-[0_10px_30px_-10px_rgba(239,68,68,0.7)] transition-all enabled:hover:scale-[1.01] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <Play className="w-5 h-5 fill-current" /> Lancer la mission
                      </button>
                      {players.length < MIN_PLAYERS && (
                        <p className="mt-3 text-center text-[11px] font-bold uppercase tracking-widest text-white/35 flex items-center justify-center gap-1.5">
                          <Lock className="w-3.5 h-3.5" /> Min. {MIN_PLAYERS} agents — partage le code ci-dessus
                        </p>
                      )}
                      {players.length >= MIN_PLAYERS && !hasAnchor && (
                        <p className="mt-3 text-center text-[11px] font-bold uppercase tracking-widest text-red-400 flex items-center justify-center gap-1.5">
                          <Lock className="w-3.5 h-3.5" /> Coche au moins une catégorie ancre (anime/manga/perso)
                        </p>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <Radio className="w-8 h-8 text-white/20 mx-auto mb-3 animate-pulse" />
                    <p className="opacity-40 italic">En attente du briefing par le chef d'unité…</p>
                  </div>
                )}
              </div>
            )}

            {/* PLAYING / MR. WHITE GUESS */}
            {(state === 'playing' || state === 'mrwhite_guess') && (
              <div className="space-y-5">
                {/* My secret word (or Mr. White card) */}
                {isMrWhite ? (
                  <div className="flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-br from-purple-500/15 to-transparent border-2 border-purple-400/40">
                    <div className="w-16 h-20 rounded-xl bg-purple-500/15 grid place-items-center"><Ghost className="w-7 h-7 text-purple-300" /></div>
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.25em] text-purple-300">Tu es Mr. White</p>
                      <p className="text-lg font-black italic text-white leading-tight">Pas de mot — bluffe, devine, survis.</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-br from-yellow-400/15 to-transparent border-2 border-yellow-400/40">
                    {myRole.image
                      ? <img src={myRole.image} alt="" className="w-16 h-20 object-cover rounded-xl shadow-lg" />
                      : <div className="w-16 h-20 rounded-xl bg-white/10 grid place-items-center"><Lock className="w-6 h-6 text-white/30" /></div>}
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-[0.25em] text-yellow-400">Ton mot secret</p>
                      <p className="text-2xl font-black italic text-white">{myRole.word ?? '…'}</p>
                    </div>
                  </div>
                )}

                {/* Mr. White guess sub-state */}
                {state === 'mrwhite_guess' ? (
                  iAmPendingWhite ? (
                    <form onSubmit={submitGuess} className="p-4 rounded-2xl bg-purple-500/10 border-2 border-purple-400/50 space-y-3">
                      <p className="text-sm text-white/85 flex items-start gap-2"><HelpCircle className="w-5 h-5 text-purple-300 shrink-0 mt-0.5" /> Tu es éliminé ! Devine le mot des <b className="text-green-400">civils</b> — si tu trouves, tu gagnes la partie.</p>
                      <div className="flex gap-3">
                        <input
                          value={guess}
                          onChange={(e) => setGuess(e.target.value)}
                          placeholder="Le mot des civils…"
                          aria-label="Deviner le mot"
                          autoFocus
                          className="flex-grow p-3.5 rounded-2xl bg-white/[0.04] border-2 border-purple-400/40 focus:border-purple-300 outline-none font-bold text-white placeholder:text-white/25"
                        />
                        <button type="submit" className="px-6 rounded-2xl bg-purple-500 hover:bg-purple-400 text-white font-black italic uppercase tracking-wide transition-colors">Deviner</button>
                      </div>
                    </form>
                  ) : (
                    <div className="p-4 rounded-2xl bg-purple-500/5 border border-purple-400/20 text-sm text-white/80 flex items-center gap-3">
                      <Ghost className="w-5 h-5 text-purple-300 shrink-0 animate-pulse" />
                      <span><b className="text-purple-300">{pendingWhiteName}</b> (Mr. White) a été éliminé et tente de deviner le mot des civils…</span>
                    </div>
                  )
                ) : (
                  <div className="p-4 rounded-2xl bg-red-500/5 border border-red-500/20 text-sm text-white/80 flex items-start gap-3">
                    <Vote className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                    {iAmAlive ? (
                      <span>Décris ton mot sans le nommer, puis <b className="text-red-400">clique un agent vivant</b> pour voter. Quand tout le monde a voté, le plus visé est éliminé (égalité → on revote).</span>
                    ) : (
                      <span className="italic text-white/50">Tu es éliminé — observe la partie en spectateur.</span>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ENDED */}
            {state === 'ended' && (
              <div className="space-y-5">
                <div className={`p-6 rounded-2xl text-center border-2 ${winnerBanner().cls}`}>
                  <p className="font-black text-2xl italic manga-font text-white">{winnerBanner().title}</p>
                  <p className="mt-2 font-bold text-white/80">{winnerBanner().sub}</p>
                  <div className="mt-4 flex flex-wrap items-center justify-center gap-3 text-sm">
                    <span className="px-3 py-1.5 rounded-xl bg-green-500/10 text-green-400 font-bold">Mot civil : <span className="text-white">{civilWord}</span></span>
                    <span className="px-3 py-1.5 rounded-xl bg-red-500/10 text-red-400 font-bold">Mot intrus : <span className="text-white">{undercoverWord}</span></span>
                  </div>
                </div>
                {isHost && (
                  <button onClick={() => sendAction('back_to_lobby')} className="w-full py-3.5 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic uppercase tracking-wide flex items-center justify-center gap-2 transition-colors">
                    <RotateCcw className="w-5 h-5" /> Nouvelle partie
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Comms / chat */}
          <div className={`${panel} p-6 flex flex-col`}>
            <h3 className="text-[11px] font-black uppercase opacity-40 mb-3 tracking-[0.25em] flex items-center gap-2">
              <Radio className="w-4 h-4" /> Canal d'infiltration
            </h3>
            <div className="flex-grow bg-black/40 rounded-2xl p-5 mb-4 overflow-y-auto max-h-72 min-h-[150px] border border-white/5 custom-scrollbar font-mono">
              {messages.length === 0 && <p className="text-center py-12 opacity-20 italic font-sans">En attente de communications…</p>}
              {messages.map((msg, i) => (
                <div key={i} className={`mb-2.5 ${msg.is_system ? 'text-center' : ''}`}>
                  {msg.is_system ? (
                    <span className="text-[11px] font-black uppercase tracking-widest text-yellow-400/50">— {msg.text} —</span>
                  ) : (
                    <p className="text-sm">
                      <span className="text-red-400/70 font-bold">{msg.user}&gt; </span>
                      <span className="text-white/85">{msg.text}</span>
                    </p>
                  )}
                </div>
              ))}
            </div>
            <form onSubmit={sendChat} className="flex gap-3">
              <input
                value={chat}
                onChange={(e) => setChat(e.target.value)}
                placeholder="Message d'infiltration…"
                aria-label="Message"
                maxLength={100}
                className="flex-grow p-3.5 rounded-2xl bg-white/[0.04] border-2 border-white/10 focus:border-red-500 outline-none font-medium text-white placeholder:text-white/25 transition-colors"
              />
              <button type="submit" className="px-5 rounded-2xl bg-red-600 hover:bg-red-500 text-white transition-colors"><Send className="w-5 h-5" /></button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UndercoverRoom;
