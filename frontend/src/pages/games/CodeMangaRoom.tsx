import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import useSocket from '../../hooks/useSocket';
import {
  Users, Send, Crown, Play, Copy, Check, Eye, KeyRound, Skull, RotateCcw, Radio, Shield,
} from 'lucide-react';

interface CCard { title?: string; image?: string; role: string; revealed: boolean }
interface CPlayer { id: string; name: string; team?: string | null; role?: string | null; is_host?: boolean }
interface CClue { team: string; word: string; number: number; guesses_left: number }
interface CMsg { user: string; text: string }

// Same card universes as Undercover — the host ticks any mix.
const CATEGORIES = [
  { key: 'Anime', label: 'Anime' },
  { key: 'Manga', label: 'Manga' },
  { key: 'Character', label: 'Persos anime' },
  { key: 'Movie', label: 'Films' },
  { key: 'Game', label: 'Jeux vidéo' },
  { key: 'Actor', label: 'Acteurs' },
  { key: 'VGChar', label: 'Persos de jeux' },
];
// Difficulty = required anime/manga knowledge (popularity depth of the cards).
const DIFFS = [
  { key: 'Easy', label: 'Grand public', hint: 'œuvres très connues' },
  { key: 'Normal', label: 'Amateur', hint: 'œuvres connues' },
  { key: 'Hard', label: 'Otaku', hint: 'œuvres pointues' },
];
const TEAM_LABEL: Record<string, string> = { blue: 'Bleue', red: 'Rouge' };

const CodeMangaRoom: React.FC = () => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const { gameState, connected, sendAction } = useSocket(roomCode, 'codemanga');
  const [name, setName] = useState('');
  const [chat, setChat] = useState('');
  const [clueWord, setClueWord] = useState('');
  const [clueNum, setClueNum] = useState(2);
  const [copied, setCopied] = useState(false);

  const gs = (gameState || {}) as Record<string, unknown>;
  const state = (gs.state as string) || 'lobby';
  const grid = (gs.grid as CCard[]) || [];
  const players = (gs.players as CPlayer[]) || [];
  const turn = (gs.turn as string) || 'blue';
  const blueScore = (gs.blue_score as number) || 0;
  const redScore = (gs.red_score as number) || 0;
  const winner = gs.winner as string | null;
  const clue = (gs.clue as CClue) || null;
  const messages = (gs.messages as CMsg[]) || [];
  const categories = (gs.categories as string[]) || ['Anime'];
  const difficulty = (gs.difficulty as string) || 'Normal';
  const myId = (gs.my_id as string) || (gs.myId as string) || '';
  const myTeam = (gs.my_team as string) || null;
  const myRole = (gs.my_role as string) || null;
  const me = players.find((p) => p.id === myId);
  const isHost = !!me?.is_host;
  const code = (roomCode || '').toUpperCase();

  if (!connected) {
    return (
      <div className="min-h-[60vh] grid place-items-center">
        <div className="flex flex-col items-center gap-4 text-indigo-400">
          <Radio className="w-12 h-12 animate-pulse" />
          <p className="font-black uppercase tracking-[0.4em] animate-pulse">Connexion au réseau…</p>
        </div>
      </div>
    );
  }

  const setPlayer = (patch: Record<string, unknown>) =>
    sendAction('set_player', {
      name: (name.trim() || me?.name || ''), team: myTeam, role: myRole, ...patch,
    });
  const submitName = () => { if (name.trim()) setPlayer({}); };
  const copyCode = () => { navigator.clipboard?.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 1500); };
  const sendChat = (e: React.FormEvent) => { e.preventDefault(); if (chat.trim()) { sendAction('chat', { message: chat.trim() }); setChat(''); } };
  const giveClue = (e: React.FormEvent) => { e.preventDefault(); if (clueWord.trim()) { sendAction('give_clue', { word: clueWord.trim(), number: clueNum }); setClueWord(''); } };
  const toggleCategory = (key: string) => {
    const next = categories.includes(key) ? categories.filter((c) => c !== key) : [...categories, key];
    if (next.length) sendAction('set_categories', { categories: next });
  };

  // Team composition helpers.
  const byTeamRole = (team: string, role: string) => players.filter((p) => p.team === team && p.role === role);
  const teamReady = (team: string) => byTeamRole(team, 'spymaster').length >= 1 && byTeamRole(team, 'operative').length >= 1;
  const canStart = teamReady('blue') && teamReady('red');

  const isMyTurn = myTeam === turn && !winner;
  const iAmClueGiver = state === 'playing' && myRole === 'spymaster' && isMyTurn && !clue;
  const iCanGuess = state === 'playing' && myRole === 'operative' && isMyTurn && !!clue;

  const clickCard = (i: number) => { if (iCanGuess && !grid[i].revealed) sendAction('click_card', { index: i }); };

  const panel = 'rounded-[1.75rem] border-2 border-white/5 bg-[#0d0f17]/80 backdrop-blur-xl shadow-2xl';

  // ── Card styling ────────────────────────────────────────────────────────
  const revealedBg: Record<string, string> = {
    blue: 'bg-blue-600 border-blue-300', red: 'bg-red-600 border-red-300',
    neutral: 'bg-amber-200/90 border-amber-100', assassin: 'bg-zinc-950 border-zinc-600',
  };
  const spyTint: Record<string, string> = {
    blue: 'border-blue-500/70 ring-1 ring-inset ring-blue-500/40',
    red: 'border-red-500/70 ring-1 ring-inset ring-red-500/40',
    neutral: 'border-amber-400/50', assassin: 'border-white/60 ring-2 ring-inset ring-red-500/60',
  };
  const cardCls = (c: CCard) => {
    if (c.revealed || winner) return `${revealedBg[c.role] || 'bg-white/10 border-white/10'}`;
    if (myRole === 'spymaster' && c.role !== 'unknown') return `bg-white/[0.03] ${spyTint[c.role] || 'border-white/10'}`;
    return 'bg-white/[0.04] border-white/10';
  };

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-8">
      {/* Banner */}
      <div className="relative overflow-hidden rounded-[2.25rem] border-2 border-indigo-500/30 bg-gradient-to-br from-indigo-950/50 via-[#0d0f17] to-[#0d0f17] p-6 sm:p-8 mb-6 shadow-[0_0_60px_-15px_rgba(99,102,241,0.4)]">
        <div className="absolute -right-10 -top-10 w-48 h-48 bg-indigo-600/20 blur-[80px] rounded-full pointer-events-none" />
        <div className="relative flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.4em] text-indigo-400 mb-2">
              <KeyRound className="w-4 h-4" /> Code Manga · Décryptage
            </div>
            <div className="flex items-center gap-4">
              <h1 className="text-4xl sm:text-6xl font-black italic manga-font uppercase tracking-tighter text-white leading-none">Code Manga</h1>
              <button onClick={copyCode} title="Copier le code" className="group inline-flex items-center gap-2 rounded-xl border-2 border-indigo-500/40 bg-indigo-500/10 hover:bg-indigo-500/20 px-4 py-2 transition-all">
                <span className="text-2xl sm:text-3xl font-black tracking-[0.25em] text-indigo-300 font-mono">{code}</span>
                {copied ? <Check className="w-5 h-5 text-green-400" /> : <Copy className="w-4 h-4 text-indigo-300 opacity-60 group-hover:opacity-100" />}
              </button>
            </div>
          </div>
          {/* Scoreboard */}
          <div className="flex items-center gap-3">
            <div className={`px-4 py-2 rounded-2xl border-2 ${turn === 'blue' && !winner && state === 'playing' ? 'border-blue-400 bg-blue-500/20' : 'border-blue-500/20 bg-blue-500/5'}`}>
              <p className="text-[9px] font-black uppercase tracking-widest text-blue-300/70">Bleue</p>
              <p className="text-2xl font-black text-blue-300 tabular-nums leading-none">{blueScore}<span className="text-sm text-blue-300/40">/9</span></p>
            </div>
            <div className={`px-4 py-2 rounded-2xl border-2 ${turn === 'red' && !winner && state === 'playing' ? 'border-red-400 bg-red-500/20' : 'border-red-500/20 bg-red-500/5'}`}>
              <p className="text-[9px] font-black uppercase tracking-widest text-red-300/70">Rouge</p>
              <p className="text-2xl font-black text-red-300 tabular-nums leading-none">{redScore}<span className="text-sm text-red-300/40">/8</span></p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Left: teams / players */}
        <div className={`${panel} p-5 lg:col-span-1 h-fit space-y-5`}>
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-indigo-300/70 mb-2">Ton pseudo {me?.name ? `· ${me.name}` : ''}</p>
            <div className="flex gap-2">
              <input value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') submitName(); }}
                placeholder="Pseudo…" maxLength={20} aria-label="Pseudo"
                className="flex-grow min-w-0 p-2.5 rounded-xl bg-white/[0.04] border-2 border-white/10 focus:border-indigo-400 outline-none font-bold text-white placeholder:text-white/25 text-sm" />
              <button onClick={submitName} className="px-3 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white font-black text-xs uppercase">OK</button>
            </div>
          </div>

          {(['blue', 'red'] as const).map((team) => (
            <div key={team} className={`rounded-2xl border-2 p-3 ${team === 'blue' ? 'border-blue-500/30 bg-blue-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
              <p className={`text-xs font-black uppercase tracking-widest mb-2.5 ${team === 'blue' ? 'text-blue-300' : 'text-red-300'}`}>Équipe {TEAM_LABEL[team]}</p>
              {state === 'lobby' && (
                <div className="grid grid-cols-2 gap-2 mb-3">
                  {([
                    { role: 'spymaster', label: 'Espion', Icon: Eye, sub: 'voit les couleurs' },
                    { role: 'operative', label: 'Agent', Icon: Shield, sub: 'devine' },
                  ] as const).map(({ role, label, Icon, sub }) => {
                    const active = myTeam === team && myRole === role;
                    const activeCls = team === 'blue' ? 'bg-blue-500 border-blue-400 text-white' : 'bg-red-500 border-red-400 text-white';
                    return (
                      <button key={role} onClick={() => setPlayer({ team, role })}
                        className={`flex flex-col items-center justify-center gap-1 py-3 rounded-xl border-2 transition-all ${active ? `${activeCls} shadow-lg` : 'border-white/15 text-white/60 hover:border-white/40 hover:text-white/90'}`}>
                        <Icon className="w-5 h-5" />
                        <span className="text-xs font-black uppercase leading-none">{label}</span>
                        <span className="text-[9px] font-medium opacity-70 leading-none">{sub}</span>
                      </button>
                    );
                  })}
                </div>
              )}
              {(['spymaster', 'operative'] as const).map((role) => (
                <div key={role} className="mb-1.5 last:mb-0">
                  <p className="text-[9px] font-bold uppercase tracking-wider text-white/30 flex items-center gap-1">
                    {role === 'spymaster' ? <Eye className="w-2.5 h-2.5" /> : <Shield className="w-2.5 h-2.5" />}
                    {role === 'spymaster' ? 'Espion' : 'Agents'}
                  </p>
                  {byTeamRole(team, role).map((p) => (
                    <span key={p.id} className="inline-flex items-center gap-1 text-xs font-bold text-white/80 mr-2">
                      {p.id === myId ? <span className={team === 'blue' ? 'text-blue-300' : 'text-red-300'}>{p.name} ·toi</span> : p.name}
                      {p.is_host && <Crown className="w-3 h-3 text-yellow-400" />}
                    </span>
                  ))}
                  {byTeamRole(team, role).length === 0 && <span className="text-[10px] italic text-white/20">—</span>}
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Center: board / lobby */}
        <div className="lg:col-span-3 space-y-4">
          {state === 'lobby' ? (
            <div className={`${panel} p-6 space-y-5`}>
              <div className="text-center py-4">
                <KeyRound className="w-10 h-10 text-indigo-400/50 mx-auto mb-3" />
                <p className="text-white/70 font-bold">Choisis ton équipe et ton rôle à gauche.</p>
                <p className="text-[11px] text-white/40 mt-1">Un <b className="text-white/70">Espion</b> par équipe voit les couleurs et donne des indices ; les <b className="text-white/70">Agents</b> devinent les cartes.</p>
              </div>
              {isHost ? (
                <>
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">Catégories des cartes</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {CATEGORIES.map((m) => {
                        const on = categories.includes(m.key);
                        return (
                          <button key={m.key} onClick={() => toggleCategory(m.key)}
                            className={`flex items-center gap-2 py-2.5 px-3 rounded-xl border-2 text-xs font-black uppercase transition-all ${on ? 'border-indigo-500 bg-indigo-500/15 text-indigo-300' : 'border-white/10 text-white/40 hover:border-indigo-500/40'}`}>
                            <span className={`w-4 h-4 rounded grid place-items-center border-2 shrink-0 ${on ? 'bg-indigo-500 border-indigo-500' : 'border-white/25'}`}>{on && <Check className="w-3 h-3 text-white" />}</span>
                            <span className="truncate">{m.label}</span>
                          </button>
                        );
                      })}
                    </div>
                    <p className="mt-2 text-[11px] text-white/35 italic">Les 25 cartes sont tirées des catégories cochées (mélange possible).</p>
                  </div>
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">Difficulté · connaissances requises</p>
                    <div className="grid grid-cols-3 gap-2">
                      {DIFFS.map((d) => (
                        <button key={d.key} onClick={() => sendAction('set_difficulty', { difficulty: d.key })}
                          className={`py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${difficulty === d.key ? 'border-indigo-500 bg-indigo-500/15 text-indigo-300' : 'border-white/10 text-white/40 hover:border-indigo-500/40'}`}>{d.label}</button>
                      ))}
                    </div>
                    <p className="mt-2 text-[11px] text-white/35 italic">{DIFFS.find((d) => d.key === difficulty)?.hint} — plus c'est dur, plus il faut s'y connaître en anime/manga.</p>
                  </div>
                  <button onClick={() => sendAction('start_game')} disabled={!canStart}
                    className="w-full py-4 rounded-2xl bg-indigo-600 enabled:hover:bg-indigo-500 text-white font-black italic uppercase tracking-widest text-lg shadow-[0_10px_30px_-10px_rgba(99,102,241,0.7)] transition-all enabled:hover:scale-[1.01] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                    <Play className="w-5 h-5 fill-current" /> Lancer la partie
                  </button>
                  {!canStart && <p className="text-center text-[11px] font-bold uppercase tracking-widest text-white/35">Il faut 1 espion + 1 agent dans chaque équipe</p>}
                </>
              ) : (
                <p className="text-center opacity-40 italic py-4">En attente du lancement par l'hôte…</p>
              )}
            </div>
          ) : (
            <>
              {/* Turn / clue bar */}
              <div className={`${panel} p-4`}>
                {winner ? (
                  <div className={`text-center rounded-xl py-3 border-2 ${winner === 'blue' ? 'border-blue-400 bg-blue-500/15 text-blue-200' : 'border-red-400 bg-red-500/15 text-red-200'}`}>
                    <p className="font-black text-xl italic manga-font">🏆 Équipe {TEAM_LABEL[winner]} gagne !</p>
                  </div>
                ) : (
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl font-black uppercase text-xs tracking-widest ${turn === 'blue' ? 'bg-blue-500/20 text-blue-300' : 'bg-red-500/20 text-red-300'}`}>
                      <Radio className="w-4 h-4 animate-pulse" /> Tour · Équipe {TEAM_LABEL[turn]}
                    </span>
                    {clue ? (
                      <span className="text-white font-bold">Indice : <span className="text-indigo-300 font-black text-lg">{clue.word}</span> · {clue.number} <span className="text-white/40 text-xs">({clue.guesses_left} essai{clue.guesses_left > 1 ? 's' : ''})</span></span>
                    ) : (
                      <span className="text-white/40 text-xs italic">En attente de l'indice de l'espion…</span>
                    )}
                  </div>
                )}
              </div>

              {/* Clue input for the current spymaster */}
              {iAmClueGiver && (
                <form onSubmit={giveClue} className={`${panel} p-4 flex gap-2 items-center`}>
                  <input value={clueWord} onChange={(e) => setClueWord(e.target.value)} placeholder="Mot-indice…" maxLength={24} aria-label="Mot-indice"
                    className="flex-grow min-w-0 p-3 rounded-xl bg-white/[0.04] border-2 border-indigo-500/40 focus:border-indigo-400 outline-none font-bold text-white placeholder:text-white/25" />
                  <select value={clueNum} onChange={(e) => setClueNum(Number(e.target.value))} aria-label="Nombre" className="p-3 rounded-xl bg-white/[0.06] border-2 border-white/10 text-white font-black">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => <option key={n} value={n} className="bg-[#0d0f17]">{n}</option>)}
                  </select>
                  <button type="submit" className="px-5 py-3 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white font-black italic uppercase text-sm">Indice</button>
                </form>
              )}
              {iCanGuess && <p className="text-center text-[11px] font-bold uppercase tracking-widest text-indigo-300/70 -mt-1">À toi de deviner — clique une carte</p>}
              {myRole === 'spymaster' && !winner && <p className="text-center text-[11px] font-bold uppercase tracking-widest text-white/30 -mt-1">Tu es espion — tu vois les couleurs (ne clique pas)</p>}

              {/* 5×5 grid */}
              <div className="grid grid-cols-5 gap-2">
                {grid.map((c, i) => {
                  const clickable = iCanGuess && !c.revealed;
                  return (
                    <button key={i} onClick={() => clickCard(i)} disabled={!clickable}
                      className={`relative aspect-[4/3] rounded-xl border-2 overflow-hidden transition-all ${cardCls(c)} ${clickable ? 'cursor-pointer hover:scale-[1.03] hover:z-10' : 'cursor-default'} ${c.revealed ? '' : 'shadow-lg'}`}>
                      {c.image && <img src={c.image} alt="" loading="lazy" className={`absolute inset-0 w-full h-full object-cover ${c.revealed || winner ? 'opacity-25' : 'opacity-40'}`} />}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/30 to-transparent" />
                      <div className="relative h-full flex flex-col justify-end p-1.5">
                        <span className={`text-[9px] sm:text-[11px] font-black leading-tight line-clamp-3 ${(c.revealed || winner) && c.role === 'neutral' ? 'text-black' : 'text-white'}`}>{c.title}</span>
                      </div>
                      {(c.revealed || winner) && c.role === 'assassin' && <Skull className="absolute top-1 right-1 w-4 h-4 text-red-500" />}
                      {c.revealed && <Check className="absolute top-1 left-1 w-3.5 h-3.5 text-white/80" />}
                    </button>
                  );
                })}
              </div>

              {winner && isHost && (
                <button onClick={() => sendAction('back_to_lobby')} className="w-full py-3.5 rounded-2xl bg-indigo-500 hover:bg-indigo-400 text-white font-black italic uppercase tracking-wide flex items-center justify-center gap-2">
                  <RotateCcw className="w-5 h-5" /> Rejouer
                </button>
              )}
            </>
          )}
        </div>

        {/* Right: chat */}
        <div className={`${panel} p-5 lg:col-span-1 flex flex-col h-fit`}>
          <h3 className="text-[10px] font-black uppercase opacity-40 mb-3 tracking-[0.25em] flex items-center gap-2"><Users className="w-4 h-4" /> Discussion</h3>
          <div className="flex-grow bg-black/40 rounded-2xl p-3 mb-3 overflow-y-auto max-h-72 min-h-[160px] border border-white/5 custom-scrollbar">
            {messages.length === 0 && <p className="text-center py-10 opacity-20 italic text-xs">Aucun message…</p>}
            {messages.map((m, i) => (
              <p key={i} className="text-xs mb-1.5"><span className="text-indigo-300/70 font-bold">{m.user}&gt; </span><span className="text-white/85">{m.text}</span></p>
            ))}
          </div>
          <form onSubmit={sendChat} className="flex gap-2">
            <input value={chat} onChange={(e) => setChat(e.target.value)} placeholder="Message…" maxLength={120} aria-label="Message"
              className="flex-grow min-w-0 p-2.5 rounded-xl bg-white/[0.04] border-2 border-white/10 focus:border-indigo-400 outline-none text-white placeholder:text-white/25 text-sm" />
            <button type="submit" className="px-3 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white"><Send className="w-4 h-4" /></button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CodeMangaRoom;
