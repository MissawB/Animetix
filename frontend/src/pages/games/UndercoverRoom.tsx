import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import useSocket from '../../hooks/useSocket';
import { Users, Send, ShieldAlert, Crown, Play, Eye, RotateCcw, Check, Vote } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

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

const UndercoverRoom: React.FC = () => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const { gameState, connected, sendAction } = useSocket(roomCode, 'undercover');
  const [name, setName] = useState('');
  const [chat, setChat] = useState('');
  const [voteTarget, setVoteTarget] = useState<string | null>(null);

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
      <div className="text-center py-24 text-white font-black animate-pulse uppercase tracking-[0.4em]">
        Connexion au réseau…
      </div>
    );
  }

  const submitName = () => {
    if (name.trim()) sendAction('set_name', { name: name.trim() });
  };
  const castVote = (id: string) => {
    if (state !== 'playing' || id === myId) return;
    setVoteTarget(id);
    sendAction('vote', { voted_for: id });
  };
  const sendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (chat.trim()) {
      sendAction('chat', { message: chat.trim() });
      setChat('');
    }
  };

  // Reveal helpers
  const undercover = players.find((p) => p.role === 'Undercover');
  const tally: Record<string, number> = {};
  Object.values(votes).forEach((t) => { tally[t] = (tally[t] || 0) + 1; });
  const mostVotedId = Object.entries(tally).sort((a, b) => b[1] - a[1])[0]?.[0];
  const groupCaughtImpostor = !!undercover && mostVotedId === undercover.id;

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Roster */}
        <Card padding="lg" className="lg:col-span-1 h-fit">
          <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-[0.2em] flex items-center gap-2">
            <Users className="w-4 h-4" /> Unité d'élite ({players.length})
          </h3>
          <div className="space-y-3">
            {players.length === 0 && <p className="text-sm italic opacity-30">En attente d'agents…</p>}
            {players.map((p) => {
              const isMe = p.id === myId;
              const voted = state === 'playing' && p.id === voteTarget;
              const clickable = state === 'playing' && !isMe;
              return (
                <button
                  key={p.id}
                  onClick={() => castVote(p.id)}
                  disabled={!clickable}
                  className={`w-full flex items-center gap-3 p-3 rounded-2xl border-2 text-left transition-all ${
                    voted ? 'border-brand-danger bg-red-500/10'
                    : clickable ? 'border-transparent bg-black/5 dark:bg-navy-900 hover:border-brand-danger/50 cursor-pointer'
                    : 'border-transparent bg-black/5 dark:bg-navy-900 cursor-default'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl grid place-items-center font-black italic shadow ${isMe ? 'bg-yellow-400 text-black border-2 border-black' : 'bg-gray-200 dark:bg-navy-700'}`}>
                    {(p.name || '?')[0].toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-grow">
                    <span className="font-bold truncate block">{p.name}{isMe && <span className="opacity-50"> (toi)</span>}</span>
                    {state === 'revealed' && p.role && (
                      <span className={`text-[11px] font-black uppercase ${p.role === 'Undercover' ? 'text-brand-danger' : 'text-green-500'}`}>
                        {p.role === 'Undercover' ? 'Intrus' : 'Civil'} · {p.word}
                      </span>
                    )}
                  </div>
                  {p.is_host && <Crown className="w-4 h-4 text-yellow-500 shrink-0" />}
                  {state === 'playing' && p.has_voted && <Check className="w-4 h-4 text-green-500 shrink-0" />}
                </button>
              );
            })}
          </div>
        </Card>

        {/* Game + chat */}
        <div className="lg:col-span-2 space-y-6">
          <Card padding="lg">
            <h2 className="text-3xl font-black italic manga-font mb-6 flex items-center gap-3 uppercase tracking-tighter">
              <ShieldAlert className="w-8 h-8 text-brand-danger" /> Mission&nbsp;: <span className="text-brand-danger">{roomCode}</span>
            </h2>

            {/* ── LOBBY ───────────────────────────────── */}
            {state === 'lobby' && (
              <div className="space-y-6">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-widest opacity-40 mb-2">Ton nom de code {me?.name ? `· ${me.name}` : ''}</p>
                  <div className="flex gap-3">
                    <input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') submitName(); }}
                      placeholder="Choisis un pseudo…"
                      maxLength={15}
                      aria-label="Nom de code"
                      className="flex-grow p-3 rounded-2xl bg-black/5 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
                    />
                    <Button onClick={submitName} variant="primary" className="px-6">Valider</Button>
                  </div>
                </div>

                {isHost ? (
                  <div className="space-y-5 pt-2">
                    <div>
                      <p className="text-[11px] font-black uppercase tracking-widest opacity-40 mb-2">Univers</p>
                      <div className="grid grid-cols-3 gap-2">
                        {MEDIA.map((m) => (
                          <button
                            key={m.key}
                            onClick={() => sendAction('set_settings', { media_type: m.key, difficulty })}
                            className={`py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${mediaType === m.key ? 'border-yellow-400 bg-yellow-400/10 text-yellow-600 dark:text-yellow-400' : 'border-black/5 dark:border-white/10 text-gray-500'}`}
                          >{m.label}</button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-[11px] font-black uppercase tracking-widest opacity-40 mb-2">Difficulté</p>
                      <div className="grid grid-cols-3 gap-2">
                        {DIFFS.map((d) => (
                          <button
                            key={d}
                            onClick={() => sendAction('set_settings', { media_type: mediaType, difficulty: d })}
                            className={`py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${difficulty === d ? 'border-yellow-400 bg-yellow-400/10 text-yellow-600 dark:text-yellow-400' : 'border-black/5 dark:border-white/10 text-gray-500'}`}
                          >{DIFF_LABEL[d]}</button>
                        ))}
                      </div>
                    </div>
                    <Button
                      onClick={() => sendAction('start_game')}
                      disabled={players.length < MIN_PLAYERS}
                      variant="danger"
                      className="w-full py-4 text-lg flex items-center justify-center gap-2"
                    >
                      <Play className="w-5 h-5 fill-current" /> Lancer la mission
                    </Button>
                    {players.length < MIN_PLAYERS && (
                      <p className="text-center text-[11px] font-bold uppercase tracking-widest opacity-40">
                        Min. {MIN_PLAYERS} agents — partage le code <span className="text-brand-danger">{roomCode}</span>
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-center py-6 opacity-40 italic">En attente du lancement par l'hôte…</p>
                )}
              </div>
            )}

            {/* ── PLAYING ─────────────────────────────── */}
            {state === 'playing' && (
              <div className="space-y-5">
                <div className="flex items-center gap-4 p-4 rounded-2xl bg-yellow-400/10 border-2 border-yellow-400/40">
                  {myRole.image && <img src={myRole.image} alt="" className="w-14 h-20 object-cover rounded-xl shadow" />}
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-yellow-500">Ton mot secret</p>
                    <p className="text-2xl font-black italic">{myRole.word ?? '…'}</p>
                  </div>
                </div>
                {clue && (
                  <p className="text-sm font-medium opacity-70 italic">
                    <span className="font-black uppercase tracking-widest text-[10px] opacity-50">Indice commun · </span>{clue}
                  </p>
                )}
                <div className="p-4 rounded-2xl bg-black/5 dark:bg-navy-900 text-sm flex items-start gap-2">
                  <Vote className="w-5 h-5 text-brand-danger shrink-0 mt-0.5" />
                  <span>Décris ton mot sans le dire, puis <b>clique un agent</b> pour voter contre l'intrus.</span>
                </div>
                {isHost && (
                  <Button onClick={() => sendAction('reveal')} variant="primary" className="w-full flex items-center justify-center gap-2">
                    <Eye className="w-5 h-5" /> Révéler les rôles
                  </Button>
                )}
              </div>
            )}

            {/* ── REVEALED ────────────────────────────── */}
            {state === 'revealed' && (
              <div className="space-y-5">
                <div className={`p-5 rounded-2xl text-center border-2 ${groupCaughtImpostor ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-brand-danger'}`}>
                  <p className="font-black text-2xl italic manga-font">{groupCaughtImpostor ? '🎯 Intrus démasqué !' : '🕵️ L\'intrus s\'échappe !'}</p>
                  {undercover && (
                    <p className="mt-2 font-bold">
                      L'intrus était <span className="text-brand-danger">{undercover.name}</span> — mot : <span className="text-yellow-500">{undercover.word}</span>
                    </p>
                  )}
                </div>
                {isHost && (
                  <Button onClick={() => sendAction('back_to_lobby')} variant="primary" className="w-full flex items-center justify-center gap-2">
                    <RotateCcw className="w-5 h-5" /> Nouvelle manche
                  </Button>
                )}
              </div>
            )}
          </Card>

          {/* Chat */}
          <Card padding="lg" className="flex flex-col">
            <div className="flex-grow bg-black/5 dark:bg-navy-900 rounded-2xl p-5 mb-4 overflow-y-auto max-h-72 min-h-[160px] border border-black/5 dark:border-white/5 custom-scrollbar">
              {messages.length === 0 && <p className="text-center py-12 opacity-20 italic">En attente de communications…</p>}
              {messages.map((msg, i) => (
                <div key={i} className={`mb-3 ${msg.is_system ? 'text-center' : 'flex flex-col'}`}>
                  {msg.is_system ? (
                    <span className="text-[11px] font-black uppercase tracking-widest opacity-40">{msg.text}</span>
                  ) : (
                    <>
                      <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">{msg.user}</span>
                      <span className="font-medium">{msg.text}</span>
                    </>
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
                className="flex-grow p-3 rounded-2xl bg-black/5 dark:bg-navy-900 border-2 border-transparent focus:border-brand-danger outline-none font-medium"
              />
              <Button type="submit" variant="danger" className="px-5"><Send className="w-5 h-5" /></Button>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default UndercoverRoom;
