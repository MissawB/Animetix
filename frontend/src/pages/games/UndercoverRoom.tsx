import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import useSocket from '../../hooks/useSocket';
import {
  Users, Send, Crown, Play, Eye, RotateCcw, Check, Vote,
  Fingerprint, Copy, Radio, Lock,
} from 'lucide-react';

interface UPlayer {
  id: string;
  name: string;
  is_host?: boolean;
  has_voted?: boolean;
  role?: string;
  word?: string;
  image?: string;
}
interface UMsg { user: string; text: string; is_system?: boolean }

const MEDIA: { key: string; label: string }[] = [
  { key: 'Anime', label: 'Anime' },
  { key: 'Manga', label: 'Manga' },
  { key: 'Character', label: 'Perso' },
];
const DIFFS = ['Easy', 'Normal', 'Hard'];
const DIFF_LABEL: Record<string, string> = { Easy: 'Facile', Normal: 'Normal', Hard: 'Difficile' };
const MIN_PLAYERS = 3;

const STATUS: Record<string, string> = {
  lobby: 'Briefing en cours — recrutez votre unité',
  playing: 'Infiltration en cours — démasquez l\'intrus',
  revealed: 'Mission terminée — dossier déclassifié',
};

const UndercoverRoom: React.FC = () => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const { gameState, connected, sendAction } = useSocket(roomCode, 'undercover');
  const [name, setName] = useState('');
  const [chat, setChat] = useState('');
  const [voteTarget, setVoteTarget] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const gs = (gameState || {}) as Record<string, unknown>;
  const players = (gs.players as UPlayer[]) || [];
  const myId = gs.myId as string | undefined;
  const me = players.find((p) => p.id === myId);
  const isHost = !!me?.is_host;
  const state = (gs.state as string) || 'lobby';
  const clue = gs.clue as string | undefined;
  const messages = (gs.messages as UMsg[]) || [];
  const myRole = (gs.private_role as UPlayer) || {};
  const mediaType = (gs.media_type as string) || 'Anime';
  const difficulty = (gs.difficulty as string) || 'Normal';
  const votes = (gs.votes as Record<string, string>) || {};

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
  const castVote = (id: string) => {
    if (state !== 'playing' || id === myId) return;
    setVoteTarget(id);
    sendAction('vote', { voted_for: id });
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

  const undercover = players.find((p) => p.role === 'Undercover');
  const tally: Record<string, number> = {};
  Object.values(votes).forEach((t) => { tally[t] = (tally[t] || 0) + 1; });
  const mostVotedId = Object.entries(tally).sort((a, b) => b[1] - a[1])[0]?.[0];
  const groupCaughtImpostor = !!undercover && mostVotedId === undercover.id;

  const panel = 'rounded-[2rem] border-2 border-white/5 bg-[#0d0f17]/80 backdrop-blur-xl shadow-2xl';

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
              const voted = state === 'playing' && p.id === voteTarget;
              const clickable = state === 'playing' && !isMe;
              return (
                <button
                  key={p.id}
                  onClick={() => castVote(p.id)}
                  disabled={!clickable}
                  className={`w-full flex items-center gap-3 p-3 rounded-2xl border-2 text-left transition-all ${
                    voted ? 'border-red-500 bg-red-500/10'
                    : clickable ? 'border-white/5 bg-white/[0.03] hover:border-red-500/50 hover:bg-red-500/5 cursor-pointer'
                    : 'border-white/5 bg-white/[0.03] cursor-default'
                  }`}
                >
                  <div className={`relative w-11 h-11 rounded-xl grid place-items-center font-black italic shadow-lg shrink-0 ${isMe ? 'bg-yellow-400 text-black' : 'bg-gradient-to-br from-navy-700 to-navy-900 text-white/80'}`}>
                    {(p.name || '?')[0].toUpperCase()}
                    <span className="absolute -bottom-1 -right-1 text-[8px] font-black bg-black/80 text-white/60 rounded-md px-1 leading-tight">{String(i + 1).padStart(2, '0')}</span>
                  </div>
                  <div className="min-w-0 flex-grow">
                    <span className="font-bold truncate block text-white">{p.name}{isMe && <span className="text-yellow-400/70"> · toi</span>}</span>
                    {state === 'revealed' && p.role ? (
                      <span className={`text-[11px] font-black uppercase ${p.role === 'Undercover' ? 'text-red-400' : 'text-green-400'}`}>
                        {p.role === 'Undercover' ? '⚠ Intrus' : '✓ Civil'} · {p.word}
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold uppercase tracking-widest text-white/25">Agent</span>
                    )}
                  </div>
                  {p.is_host && <Crown className="w-4 h-4 text-yellow-400 shrink-0" />}
                  {state === 'playing' && p.has_voted && <Check className="w-4 h-4 text-green-400 shrink-0" />}
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
                    <div className="grid sm:grid-cols-2 gap-5">
                      <div>
                        <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">Univers</p>
                        <div className="grid grid-cols-3 gap-2">
                          {MEDIA.map((m) => (
                            <button
                              key={m.key}
                              onClick={() => sendAction('set_settings', { media_type: m.key, difficulty })}
                              className={`py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${mediaType === m.key ? 'border-red-500 bg-red-500/15 text-red-400' : 'border-white/10 text-white/40 hover:border-red-500/40'}`}
                            >{m.label}</button>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">Difficulté</p>
                        <div className="grid grid-cols-3 gap-2">
                          {DIFFS.map((d) => (
                            <button
                              key={d}
                              onClick={() => sendAction('set_settings', { media_type: mediaType, difficulty: d })}
                              className={`py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${difficulty === d ? 'border-red-500 bg-red-500/15 text-red-400' : 'border-white/10 text-white/40 hover:border-red-500/40'}`}
                            >{DIFF_LABEL[d]}</button>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div>
                      <button
                        onClick={() => sendAction('start_game')}
                        disabled={players.length < MIN_PLAYERS}
                        className="w-full py-4 rounded-2xl bg-red-600 enabled:hover:bg-red-500 text-white font-black italic uppercase tracking-widest text-lg shadow-[0_10px_30px_-10px_rgba(239,68,68,0.7)] transition-all enabled:hover:scale-[1.01] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <Play className="w-5 h-5 fill-current" /> Lancer la mission
                      </button>
                      {players.length < MIN_PLAYERS && (
                        <p className="mt-3 text-center text-[11px] font-bold uppercase tracking-widest text-white/35 flex items-center justify-center gap-1.5">
                          <Lock className="w-3.5 h-3.5" /> Min. {MIN_PLAYERS} agents — partage le code ci-dessus
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

            {/* PLAYING */}
            {state === 'playing' && (
              <div className="space-y-5">
                <div className="flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-br from-yellow-400/15 to-transparent border-2 border-yellow-400/40">
                  {myRole.image
                    ? <img src={myRole.image} alt="" className="w-16 h-20 object-cover rounded-xl shadow-lg" />
                    : <div className="w-16 h-20 rounded-xl bg-white/10 grid place-items-center"><Lock className="w-6 h-6 text-white/30" /></div>}
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.25em] text-yellow-400">Ton mot secret</p>
                    <p className="text-2xl font-black italic text-white">{myRole.word ?? '…'}</p>
                  </div>
                </div>
                {clue && (
                  <p className="text-sm font-medium text-white/70 italic">
                    <span className="font-black uppercase tracking-widest text-[10px] text-white/40">Indice commun · </span>{clue}
                  </p>
                )}
                <div className="p-4 rounded-2xl bg-red-500/5 border border-red-500/20 text-sm text-white/80 flex items-start gap-3">
                  <Vote className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <span>Décris ton mot sans le révéler, puis <b className="text-red-400">clique un agent</b> pour voter contre l'intrus.</span>
                </div>
                {isHost && (
                  <button onClick={() => sendAction('reveal')} className="w-full py-3.5 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic uppercase tracking-wide flex items-center justify-center gap-2 transition-colors">
                    <Eye className="w-5 h-5" /> Révéler les rôles
                  </button>
                )}
              </div>
            )}

            {/* REVEALED */}
            {state === 'revealed' && (
              <div className="space-y-5">
                <div className={`p-6 rounded-2xl text-center border-2 ${groupCaughtImpostor ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}>
                  <p className="font-black text-2xl italic manga-font text-white">{groupCaughtImpostor ? '🎯 Intrus démasqué !' : '🕵️ L\'intrus s\'échappe !'}</p>
                  {undercover && (
                    <p className="mt-2 font-bold text-white/80">
                      L'intrus était <span className="text-red-400">{undercover.name}</span> — son mot : <span className="text-yellow-400">{undercover.word}</span>
                    </p>
                  )}
                </div>
                {isHost && (
                  <button onClick={() => sendAction('back_to_lobby')} className="w-full py-3.5 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic uppercase tracking-wide flex items-center justify-center gap-2 transition-colors">
                    <RotateCcw className="w-5 h-5" /> Nouvelle manche
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
                    <span className="text-[11px] font-black uppercase tracking-widest text-white/30">— {msg.text} —</span>
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
