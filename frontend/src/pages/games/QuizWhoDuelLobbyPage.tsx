import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { HelpCircle, Plus, LogIn, ArrowRight, Eye, Swords, Search } from 'lucide-react';

const CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const newCode = () => Array.from({ length: 5 }, () => CHARS[Math.floor(Math.random() * CHARS.length)]).join('');
const panel = 'rounded-[2rem] border-2 border-white/5 bg-[#0d0f17]/80 backdrop-blur-xl shadow-2xl';

const QuizWhoDuelLobbyPage: React.FC = () => {
  const navigate = useNavigate();
  const [joinCode, setJoinCode] = useState('');
  const enter = (code: string) => { const c = code.trim().toUpperCase(); if (c) navigate(`/game/quiz-who/arena/${c}/`); };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <div className="relative overflow-hidden rounded-[2.5rem] border-2 border-teal-500/30 bg-gradient-to-br from-teal-950/50 via-[#0d0f17] to-[#0d0f17] p-7 sm:p-9 mb-8 shadow-[0_0_60px_-15px_rgba(20,184,166,0.4)]">
        <div className="absolute -right-10 -top-10 w-48 h-48 bg-teal-500/20 blur-[80px] rounded-full pointer-events-none" />
        <div className="relative">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.4em] text-teal-300 mb-3"><Search className="w-4 h-4" /> Qui est-ce ? · Duel</div>
          <h1 className="text-5xl sm:text-6xl font-black italic manga-font uppercase tracking-tighter text-white leading-none">Qui est-ce ?</h1>
          <p className="mt-3 text-sm font-bold uppercase tracking-widest text-white/40">Chacun son perso secret — démasquez l'adversaire en premier</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className={`${panel} p-6 space-y-5`}>
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 flex items-center gap-2"><Plus className="w-4 h-4" /> Créer un duel</h3>
          <p className="text-[11px] text-white/35 italic">Génère un salon et partage le code avec ton adversaire (2 joueurs).</p>
          <button onClick={() => enter(newCode())}
            className="w-full py-4 rounded-2xl bg-teal-600 hover:bg-teal-500 text-white font-black italic uppercase tracking-widest text-lg shadow-[0_10px_30px_-10px_rgba(20,184,166,0.7)] transition-all hover:scale-[1.01] active:scale-95 flex items-center justify-center gap-2">
            <Plus className="w-5 h-5" /> Créer le duel
          </button>
        </div>

        <div className={`${panel} p-6 space-y-5`}>
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 flex items-center gap-2"><LogIn className="w-4 h-4" /> Rejoindre un duel</h3>
          <p className="text-[11px] text-white/35 italic">Saisis le code du salon partagé.</p>
          <input value={joinCode} onChange={(e) => setJoinCode(e.target.value.toUpperCase().slice(0, 8))} onKeyDown={(e) => { if (e.key === 'Enter') enter(joinCode); }}
            placeholder="CODE…" aria-label="Code du salon"
            className="w-full p-3.5 rounded-2xl bg-white/[0.04] border-2 border-white/10 focus:border-teal-400 outline-none font-black tracking-[0.3em] text-2xl text-center text-white placeholder:text-white/20 font-mono uppercase" />
          <button onClick={() => enter(joinCode)} disabled={!joinCode.trim()}
            className="w-full py-4 rounded-2xl bg-white/10 enabled:hover:bg-white/20 text-white font-black italic uppercase tracking-widest text-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
            <ArrowRight className="w-5 h-5" /> Rejoindre
          </button>
        </div>
      </div>

      <div className={`${panel} p-6 mt-6`}>
        <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 mb-4 flex items-center gap-2"><HelpCircle className="w-4 h-4" /> Comment jouer</h3>
        <div className="grid sm:grid-cols-3 gap-4 text-sm">
          <div className="flex items-start gap-3"><Eye className="w-5 h-5 text-teal-300 shrink-0 mt-0.5" /><p className="text-white/70">Chacun reçoit un <b className="text-white">perso secret</b> sur un plateau commun.</p></div>
          <div className="flex items-start gap-3"><Search className="w-5 h-5 text-teal-300 shrink-0 mt-0.5" /><p className="text-white/70">À ton tour, pose une <b className="text-white">question oui/non</b> et élimine les portraits.</p></div>
          <div className="flex items-start gap-3"><Swords className="w-5 h-5 text-teal-300 shrink-0 mt-0.5" /><p className="text-white/70">Devine le perso de l'adversaire <b className="text-white">avant lui</b> pour gagner !</p></div>
        </div>
      </div>
    </div>
  );
};

export default QuizWhoDuelLobbyPage;
