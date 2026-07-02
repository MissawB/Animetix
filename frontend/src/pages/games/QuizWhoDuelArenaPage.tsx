import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import useSocket from '../../hooks/useSocket';
import {
  X, Trophy, Frown, HelpCircle, Check, Hourglass, Copy, Crown, Radio, Search,
  Play, RotateCcw, Eye, Send, Crosshair, MessageCircleQuestion,
} from 'lucide-react';

interface QCard { id: string; title: string; image?: string }
interface QQ { attr: string; label: string }
interface QPlayer { num: number; name: string; is_host?: boolean }
interface QAns { by: number; name?: string; label: string; answer: string }
interface QMsg { user: string; text: string; is_system?: boolean }
interface QPending { by: number; name: string; text: string }

const UNIVERSES = [
  { key: 'Character', label: 'Personnages' },
  { key: 'Anime', label: 'Anime' },
  { key: 'Manga', label: 'Manga' },
];
const DIFFS = [
  { key: 'Easy', label: 'Facile', hint: 'persos très connus' },
  { key: 'Normal', label: 'Normal', hint: 'persos connus' },
  { key: 'Hard', label: 'Difficile', hint: 'persos pointus' },
  { key: 'Impossible', label: 'Extrême', hint: 'persos obscurs' },
];

const panel = 'rounded-[1.75rem] border-2 border-white/5 bg-[#0d0f17]/80 backdrop-blur-xl shadow-2xl';

const QuizWhoDuelArenaPage: React.FC = () => {
  const { roomCode = '' } = useParams();
  const { gameState, connected, sendAction } = useSocket(roomCode, 'quizwho');
  const [name, setName] = useState('');
  const [chat, setChat] = useState('');
  const [customQ, setCustomQ] = useState('');
  const [copied, setCopied] = useState(false);

  const gs = (gameState || {}) as Record<string, unknown>;
  const state = (gs.state as string) || 'lobby';
  const board = (gs.board as QCard[]) || [];
  const questions = (gs.questions as QQ[]) || [];
  const players = (gs.players as QPlayer[]) || [];
  const lastAnswer = (gs.last_answer as QAns) || null;
  const winner = (gs.winner as number) || null;
  const messages = (gs.messages as QMsg[]) || [];
  const mediaType = (gs.media_type as string) || 'Character';
  const difficulty = (gs.difficulty as string) || 'Normal';
  const myNum = (gs.your_num as number) || 0;
  const isHost = !!gs.is_host;
  const mySecretId = gs.your_secret_id as string | undefined;
  const mySecretTitle = gs.your_secret_title as string | undefined;
  const eliminated = new Set((gs.your_eliminated as string[]) || []);
  const yourTurn = !!gs.your_turn;
  const youWon = !!gs.you_won;
  const opponentJoined = !!gs.opponent_joined;
  const pending = (gs.pending as QPending) || null;
  const awaitingMyAnswer = !!gs.awaiting_my_answer;
  const code = (roomCode || '').toUpperCase();

  if (!connected) {
    return (
      <div className="min-h-[60vh] grid place-items-center">
        <div className="flex flex-col items-center gap-4 text-teal-300">
          <Radio className="w-12 h-12 animate-pulse" />
          <p className="font-black uppercase tracking-[0.4em] animate-pulse">Connexion au duel…</p>
        </div>
      </div>
    );
  }

  const copyCode = () => { navigator.clipboard?.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 1500); };
  const submitName = () => { if (name.trim()) sendAction('set_name', { name: name.trim() }); };
  const applySettings = (patch: Record<string, unknown>) => sendAction('set_settings', { media_type: mediaType, difficulty, ...patch });
  const ask = (attr: string) => { if (yourTurn) sendAction('ask', { attribute: attr }); };
  const askCustom = (e: React.FormEvent) => { e.preventDefault(); if (yourTurn && customQ.trim()) { sendAction('ask_custom', { text: customQ.trim() }); setCustomQ(''); } };
  const answerCustom = (a: string) => sendAction('answer_custom', { answer: a });
  const guess = (id: string) => { if (yourTurn && !eliminated.has(id)) sendAction('guess', { guess_id: id }); };
  const toggle = (id: string) => { if (myNum > 0) sendAction('toggle_card', { card_id: id }); };
  const sendChat = (e: React.FormEvent) => { e.preventDefault(); if (chat.trim()) { sendAction('chat', { message: chat.trim() }); setChat(''); } };

  const opponent = players.find((p) => p.num !== myNum && p.num > 0);
  const remaining = board.filter((b) => !eliminated.has(b.id)).length;
  const isSpectator = myNum === 0;

  // ── Banner ──────────────────────────────────────────────────────────────
  const banner = (
    <div className="relative overflow-hidden rounded-[2rem] border-2 border-teal-500/30 bg-gradient-to-br from-teal-950/50 via-[#0d0f17] to-[#0d0f17] p-5 sm:p-7 mb-6 shadow-[0_0_60px_-15px_rgba(20,184,166,0.4)]">
      <div className="absolute -right-10 -top-10 w-40 h-40 bg-teal-500/20 blur-[80px] rounded-full pointer-events-none" />
      <div className="relative flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.4em] text-teal-300 mb-2"><Search className="w-4 h-4" /> Qui est-ce ? · Duel</div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl sm:text-5xl font-black italic manga-font uppercase tracking-tighter text-white leading-none">Duel</h1>
            <button onClick={copyCode} title="Copier le code" className="group inline-flex items-center gap-2 rounded-xl border-2 border-teal-500/40 bg-teal-500/10 hover:bg-teal-500/20 px-3.5 py-1.5 transition-all">
              <span className="text-xl sm:text-2xl font-black tracking-[0.25em] text-teal-200 font-mono">{code}</span>
              {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-teal-300 opacity-60 group-hover:opacity-100" />}
            </button>
          </div>
        </div>
        {state === 'playing' && !winner && (
          <div className={`px-4 py-2 rounded-2xl font-black uppercase tracking-widest text-sm ${yourTurn ? 'bg-green-500/20 text-green-300' : 'bg-white/10 text-white/50'}`}>
            {isSpectator ? 'Spectateur' : yourTurn ? 'À toi de jouer' : "Tour de l'adversaire…"}
          </div>
        )}
      </div>
    </div>
  );

  // ── LOBBY ───────────────────────────────────────────────────────────────
  if (state === 'lobby') {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        {banner}
        <div className={`${panel} p-6 space-y-6`}>
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.25em] text-teal-300/70 mb-2">Ton pseudo</p>
            <div className="flex gap-2">
              <input value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') submitName(); }}
                placeholder="Pseudo…" maxLength={20} aria-label="Pseudo"
                className="flex-grow p-3 rounded-xl bg-white/[0.04] border-2 border-white/10 focus:border-teal-400 outline-none font-bold text-white placeholder:text-white/25" />
              <button onClick={submitName} className="px-5 rounded-xl bg-teal-500 hover:bg-teal-400 text-white font-black uppercase text-sm">OK</button>
            </div>
          </div>

          {/* Players */}
          <div className="grid grid-cols-2 gap-3">
            {[1, 2].map((n) => {
              const p = players.find((pl) => pl.num === n);
              return (
                <div key={n} className={`rounded-2xl border-2 p-4 ${p ? 'border-teal-500/40 bg-teal-500/5' : 'border-white/10 border-dashed'}`}>
                  <p className="text-[10px] font-black uppercase tracking-widest text-white/40 mb-1">Joueur {n}</p>
                  {p ? (
                    <p className="font-black text-white flex items-center gap-1.5">{p.name}{p.is_host && <Crown className="w-4 h-4 text-yellow-400" />}{p.num === myNum && <span className="text-teal-300 text-xs">· toi</span>}</p>
                  ) : (
                    <p className="text-white/30 italic flex items-center gap-2"><Hourglass className="w-4 h-4 animate-pulse" /> en attente…</p>
                  )}
                </div>
              );
            })}
          </div>

          {isHost ? (
            <>
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">Univers</p>
                <div className="grid grid-cols-3 gap-2">
                  {UNIVERSES.map((u) => (
                    <button key={u.key} onClick={() => applySettings({ media_type: u.key })}
                      className={`py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${mediaType === u.key ? 'border-teal-500 bg-teal-500/15 text-teal-300' : 'border-white/10 text-white/40 hover:border-teal-500/40'}`}>{u.label}</button>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-2">Difficulté · connaissances</p>
                <div className="grid grid-cols-4 gap-2">
                  {DIFFS.map((d) => (
                    <button key={d.key} onClick={() => applySettings({ difficulty: d.key })}
                      className={`py-2.5 rounded-xl border-2 text-[11px] font-black uppercase transition-all ${difficulty === d.key ? 'border-teal-500 bg-teal-500/15 text-teal-300' : 'border-white/10 text-white/40 hover:border-teal-500/40'}`}>{d.label}</button>
                  ))}
                </div>
                <p className="mt-2 text-[11px] text-white/35 italic">{DIFFS.find((d) => d.key === difficulty)?.hint} — plus c'est dur, plus les persos sont obscurs.</p>
              </div>
              <button onClick={() => sendAction('start_game')} disabled={!opponentJoined}
                className="w-full py-4 rounded-2xl bg-teal-600 enabled:hover:bg-teal-500 text-white font-black italic uppercase tracking-widest text-lg shadow-[0_10px_30px_-10px_rgba(20,184,166,0.7)] transition-all enabled:hover:scale-[1.01] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                <Play className="w-5 h-5 fill-current" /> Lancer le duel
              </button>
              {!opponentJoined && <p className="text-center text-[11px] font-bold uppercase tracking-widest text-white/35">En attente du 2ᵉ joueur — partage le code {code}</p>}
            </>
          ) : (
            <p className="text-center opacity-40 italic py-2">{isSpectator ? 'Duel complet — tu es spectateur.' : "En attente du lancement par l'hôte…"}</p>
          )}
        </div>
      </div>
    );
  }

  // ── ENDED ───────────────────────────────────────────────────────────────
  if (state === 'ended') {
    const winnerName = players.find((p) => p.num === winner)?.name || `Joueur ${winner}`;
    return (
      <div className="max-w-lg mx-auto px-6 py-16 text-center">
        {youWon ? (
          <><Trophy className="w-20 h-20 text-yellow-400 mx-auto mb-6 animate-bounce" /><h1 className="text-4xl font-black italic uppercase mb-2 text-white">Victoire !</h1><p className="text-white/60">Tu as démasqué le perso adverse en premier.</p></>
        ) : isSpectator ? (
          <><Search className="w-20 h-20 text-teal-300 mx-auto mb-6" /><h1 className="text-4xl font-black italic uppercase mb-2 text-white">{winnerName} gagne</h1></>
        ) : (
          <><Frown className="w-20 h-20 text-white/40 mx-auto mb-6" /><h1 className="text-4xl font-black italic uppercase mb-2 text-white">Perdu…</h1><p className="text-white/60">L'adversaire a trouvé ton perso avant toi.</p></>
        )}
        {isHost && (
          <button onClick={() => sendAction('back_to_lobby')} className="mt-8 inline-flex items-center gap-2 bg-teal-500 hover:bg-teal-400 text-white font-black italic uppercase tracking-widest px-8 py-4 rounded-2xl transition-all">
            <RotateCcw className="w-5 h-5" /> Rejouer
          </button>
        )}
      </div>
    );
  }

  // ── PLAYING ─────────────────────────────────────────────────────────────
  const answerCard = lastAnswer && (
    <div className={`rounded-2xl border-2 p-4 ${lastAnswer.answer === 'OUI' ? 'border-green-500/40 bg-green-500/10' : lastAnswer.answer === 'NON' ? 'border-red-500/40 bg-red-500/10' : 'border-white/20 bg-white/5'}`}>
      <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-1">{lastAnswer.by === myNum ? 'Toi' : (opponent?.name || 'Adversaire')} · {lastAnswer.answer === 'RATÉ' || lastAnswer.answer === 'GAGNÉ' ? 'accusation' : 'question'}</p>
      <p className="text-[11px] font-bold opacity-70 mb-1">{lastAnswer.label}</p>
      <p className="flex items-center gap-2 font-black italic uppercase text-sm text-white">
        {lastAnswer.answer === 'OUI' && <Check className="w-4 h-4 text-green-400" />}
        {lastAnswer.answer === 'NON' && <X className="w-4 h-4 text-red-400" />}
        {lastAnswer.answer}
      </p>
    </div>
  );

  return (
    <div className="max-w-[1500px] mx-auto px-4 sm:px-6 py-8">
      {banner}
      <div className="flex flex-wrap items-center gap-4 mb-5">
        {mySecretId && !isSpectator && (
          <div className="flex items-center gap-3 rounded-2xl border-2 border-teal-400/40 bg-teal-400/5 p-2.5 pr-5">
            {board.find((b) => b.id === mySecretId)?.image
              ? <img src={board.find((b) => b.id === mySecretId)?.image} alt="" className="w-11 h-14 object-cover rounded-lg" />
              : <div className="w-11 h-14 rounded-lg bg-white/10 grid place-items-center"><Eye className="w-5 h-5 text-white/30" /></div>}
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-teal-300">Ton perso secret</p>
              <p className="font-black text-white">{mySecretTitle}</p>
            </div>
          </div>
        )}
        <div className={`ml-auto flex items-center gap-2 px-4 py-2 rounded-2xl ${panel}`}>
          <span className="text-[11px] font-black uppercase tracking-widest text-white/40">Restants</span>
          <span className="text-2xl font-black tabular-nums text-teal-300">{remaining}</span>
        </div>
      </div>

      {/* Full board — all 16 portraits visible at once */}
      <div className="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 gap-2 sm:gap-3">
        {board.map((c) => {
          const out = eliminated.has(c.id);
          const canAccuse = yourTurn && !out && !isSpectator && !pending;
          return (
            <div key={c.id} className={`relative group aspect-[3/4] rounded-xl overflow-hidden border-2 transition-all ${out ? 'border-red-500/30' : 'border-white/10 hover:border-white/25'}`}>
              <button onClick={() => toggle(c.id)} disabled={isSpectator} title={isSpectator ? c.title : out ? 'Rétablir' : 'Barrer'} className="absolute inset-0 w-full h-full cursor-pointer disabled:cursor-default">
                {c.image ? <img src={c.image} alt={c.title} loading="lazy" className={`w-full h-full object-cover transition-all ${out ? 'grayscale opacity-25' : ''}`} /> : <div className="w-full h-full grid place-items-center bg-black/40 text-white/40 text-[10px] p-1 text-center">{c.title}</div>}
                <span className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 to-transparent p-1 pt-4"><span className="block text-[9px] font-black uppercase text-white truncate text-left leading-tight">{c.title}</span></span>
              </button>
              {out && <span className="absolute inset-0 grid place-items-center pointer-events-none"><X className="w-8 h-8 text-red-500" strokeWidth={3} /></span>}
              {canAccuse && (
                <button onClick={() => guess(c.id)} title={`Accuser : ${c.title}`} className="absolute top-1 right-1 w-7 h-7 rounded-lg bg-teal-500 hover:bg-teal-400 text-white grid place-items-center opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity shadow-lg">
                  <Crosshair className="w-4 h-4" />
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Controls */}
      <div className="grid lg:grid-cols-3 gap-4 mt-5">
        <div className="lg:col-span-2 space-y-4">
          {awaitingMyAnswer && pending ? (
            <div className={`${panel} p-5 border-teal-400/50`}>
              <p className="text-[11px] font-black uppercase tracking-widest text-teal-300 mb-1 flex items-center gap-2"><MessageCircleQuestion className="w-4 h-4" /> {pending.name} te demande</p>
              <p className="text-xl font-black text-white mb-4">« {pending.text} »</p>
              <div className="grid grid-cols-2 gap-3">
                <button onClick={() => answerCustom('OUI')} className="py-3.5 rounded-xl bg-green-500 hover:bg-green-400 text-white font-black italic uppercase text-lg flex items-center justify-center gap-2"><Check className="w-5 h-5" /> Oui</button>
                <button onClick={() => answerCustom('NON')} className="py-3.5 rounded-xl bg-red-500 hover:bg-red-400 text-white font-black italic uppercase text-lg flex items-center justify-center gap-2"><X className="w-5 h-5" /> Non</button>
              </div>
              <p className="mt-2 text-[11px] text-white/35 italic">Réponds honnêtement d'après TON perso secret.</p>
            </div>
          ) : pending ? (
            <div className={`${panel} p-6 text-center`}>
              <Hourglass className="w-6 h-6 text-teal-300 mx-auto mb-2 animate-pulse" />
              <p className="text-sm font-bold text-white/60">En attente de la réponse de {opponent?.name || "l'adversaire"}…</p>
              <p className="text-[11px] text-white/30 mt-1 italic">« {pending.text} »</p>
            </div>
          ) : isSpectator ? (
            <div className={`${panel} p-6 text-center text-white/40 text-xs font-bold uppercase tracking-widest`}>Mode spectateur</div>
          ) : yourTurn ? (
            <div className={`${panel} p-4 space-y-3`}>
              <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-white/40 flex items-center gap-2"><HelpCircle className="w-4 h-4" /> Questions préenregistrées</h3>
              <div className="grid sm:grid-cols-2 gap-2 max-h-52 overflow-y-auto pr-1 custom-scrollbar">
                {questions.map((q) => (
                  <button key={q.attr} onClick={() => ask(q.attr)}
                    className="text-left rounded-xl border-2 border-white/10 hover:border-teal-400 hover:bg-teal-400/5 px-3 py-2 text-sm font-bold text-white transition-all">{q.label}</button>
                ))}
              </div>
              <form onSubmit={askCustom} className="flex gap-2 pt-2 border-t border-white/5">
                <input value={customQ} onChange={(e) => setCustomQ(e.target.value)} placeholder="Ta question perso — l'adversaire répond…" maxLength={120} aria-label="Question personnalisée"
                  className="flex-grow min-w-0 p-2.5 rounded-xl bg-white/[0.04] border-2 border-white/10 focus:border-teal-400 outline-none text-white placeholder:text-white/25 text-sm" />
                <button type="submit" disabled={!customQ.trim()} className="px-4 rounded-xl bg-teal-500 enabled:hover:bg-teal-400 text-white font-black uppercase text-xs disabled:opacity-40 disabled:cursor-not-allowed">Demander</button>
              </form>
              <p className="text-[11px] text-white/35 italic flex items-center gap-1 flex-wrap">Clique un portrait pour le <b className="text-white/60">barrer</b> ; survole puis <Crosshair className="inline w-3 h-3 text-teal-300" /> pour <b className="text-white/60">accuser</b>.</p>
            </div>
          ) : (
            <div className={`${panel} p-6 text-center`}><p className="text-xs font-bold uppercase tracking-widest text-white/40 animate-pulse">{opponent?.name || "L'adversaire"} réfléchit…</p></div>
          )}
          {answerCard}
        </div>

        {/* Journal / chat */}
        <div className={`${panel} p-4 flex flex-col`}>
          <h3 className="text-[10px] font-black uppercase opacity-40 mb-2 tracking-[0.25em]">Journal</h3>
          <div className="flex-grow bg-black/40 rounded-xl p-3 mb-2 max-h-40 min-h-[100px] overflow-y-auto border border-white/5 custom-scrollbar">
            {messages.length === 0 && <p className="text-center py-4 opacity-20 italic text-[11px]">—</p>}
            {messages.map((m, i) => (
              <p key={i} className="text-[11px] mb-1">
                {m.is_system ? <span className="text-teal-300/60 italic">{m.text}</span> : <><span className="text-teal-300/70 font-bold">{m.user}&gt; </span><span className="text-white/80">{m.text}</span></>}
              </p>
            ))}
          </div>
          {!isSpectator && (
            <form onSubmit={sendChat} className="flex gap-2">
              <input value={chat} onChange={(e) => setChat(e.target.value)} placeholder="Message…" maxLength={120} aria-label="Message"
                className="flex-grow min-w-0 p-2 rounded-lg bg-white/[0.04] border-2 border-white/10 focus:border-teal-400 outline-none text-white placeholder:text-white/25 text-xs" />
              <button type="submit" className="px-2.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-white"><Send className="w-4 h-4" /></button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuizWhoDuelArenaPage;
