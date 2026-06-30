import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import {
  Fingerprint, Plus, Globe, EyeOff, LogIn, Users, RefreshCw, ArrowRight, Radio, Crown,
} from 'lucide-react';

interface PublicRoom {
  code: string;
  name?: string;
  players: number;
  state: string;
  host?: string;
  num_undercovers?: number;
  num_mrwhites?: number;
}

const CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // no ambiguous chars (0/O, 1/I)
const newCode = () =>
  Array.from({ length: 5 }, () => CHARS[Math.floor(Math.random() * CHARS.length)]).join('');

const STATE_LABEL: Record<string, string> = {
  lobby: 'En attente', playing: 'En partie', mrwhite_guess: 'En partie', ended: 'Terminé',
};

const panel = 'rounded-[2rem] border-2 border-white/5 bg-[#0d0f17]/80 backdrop-blur-xl shadow-2xl';

const UndercoverEntry: React.FC = () => {
  const navigate = useNavigate();
  const [createPublic, setCreatePublic] = useState(true);
  const [joinCode, setJoinCode] = useState('');

  const enter = (code: string, visibility?: 'public' | 'private') => {
    const c = code.trim().toUpperCase();
    if (!c) return;
    navigate(`/undercover/room/${c}/${visibility === 'public' ? '?visibility=public' : ''}`);
  };

  // Live listing of public rooms — polled, refetched on mount (the list is
  // ephemeral, so we don't trust a persisted cache).
  const { data: rooms = [], isFetching, refetch } = useQuery<PublicRoom[]>({
    queryKey: ['undercover-public-rooms'],
    queryFn: async () => {
      const data = await apiClient('/api/v1/game/undercover/public-rooms/', { skipToast: true });
      return (data?.rooms as PublicRoom[]) || [];
    },
    refetchInterval: 6000,
    refetchOnMount: 'always',
    staleTime: 0,
  });
  const loading = isFetching;
  const fetchRooms = () => refetch();

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      {/* Banner */}
      <div className="relative overflow-hidden rounded-[2.5rem] border-2 border-red-500/30 bg-gradient-to-br from-red-950/50 via-[#0d0f17] to-[#0d0f17] p-7 sm:p-9 mb-8 shadow-[0_0_60px_-15px_rgba(239,68,68,0.4)]">
        <div className="absolute inset-0 opacity-[0.07] pointer-events-none" style={{ backgroundImage: 'repeating-linear-gradient(45deg, #fff 0 2px, transparent 2px 14px)' }} />
        <div className="absolute -right-10 -top-10 w-48 h-48 bg-red-600/20 blur-[80px] rounded-full pointer-events-none" />
        <div className="relative">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.4em] text-red-500 mb-3">
            <Fingerprint className="w-4 h-4" /> Dossier classifié · Undercover
          </div>
          <h1 className="text-5xl sm:text-6xl font-black italic manga-font uppercase tracking-tighter text-white leading-none">Salle d'opérations</h1>
          <p className="mt-3 text-sm font-bold uppercase tracking-widest text-white/40">Crée une mission ou rejoins une unité existante</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Create */}
        <div className={`${panel} p-6 space-y-5`}>
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 flex items-center gap-2"><Plus className="w-4 h-4" /> Créer un salon</h3>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setCreatePublic(true)}
              className={`flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${createPublic ? 'border-green-500 bg-green-500/15 text-green-400' : 'border-white/10 text-white/40 hover:border-green-500/40'}`}
            ><Globe className="w-3.5 h-3.5" /> Public</button>
            <button
              onClick={() => setCreatePublic(false)}
              className={`flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 text-xs font-black uppercase transition-all ${!createPublic ? 'border-red-500 bg-red-500/15 text-red-400' : 'border-white/10 text-white/40 hover:border-red-500/40'}`}
            ><EyeOff className="w-3.5 h-3.5" /> Privé</button>
          </div>
          <p className="text-[11px] text-white/35 italic">
            {createPublic ? 'Apparaîtra dans la liste des salons publics — tout le monde peut rejoindre.' : 'Accessible uniquement via le code ou l\'URL que tu partages.'}
          </p>
          <button
            onClick={() => enter(newCode(), createPublic ? 'public' : 'private')}
            className="w-full py-4 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-black italic uppercase tracking-widest text-lg shadow-[0_10px_30px_-10px_rgba(239,68,68,0.7)] transition-all hover:scale-[1.01] active:scale-95 flex items-center justify-center gap-2"
          ><Plus className="w-5 h-5" /> Créer la mission</button>
        </div>

        {/* Join private */}
        <div className={`${panel} p-6 space-y-5`}>
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 flex items-center gap-2"><LogIn className="w-4 h-4" /> Rejoindre un salon privé</h3>
          <p className="text-[11px] text-white/35 italic">Saisis le code à 5 caractères qu'on t'a partagé.</p>
          <input
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase().slice(0, 8))}
            onKeyDown={(e) => { if (e.key === 'Enter') enter(joinCode); }}
            placeholder="CODE…"
            aria-label="Code du salon"
            className="w-full p-3.5 rounded-2xl bg-white/[0.04] border-2 border-white/10 focus:border-yellow-400 outline-none font-black tracking-[0.3em] text-2xl text-center text-white placeholder:text-white/20 font-mono uppercase transition-colors"
          />
          <button
            onClick={() => enter(joinCode)}
            disabled={!joinCode.trim()}
            className="w-full py-4 rounded-2xl bg-yellow-400 enabled:hover:bg-yellow-500 text-black font-black italic uppercase tracking-widest text-lg transition-all enabled:hover:scale-[1.01] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          ><ArrowRight className="w-5 h-5" /> Rejoindre</button>
        </div>
      </div>

      {/* Public listing */}
      <div className={`${panel} p-6 mt-6`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-white/40 flex items-center gap-2"><Globe className="w-4 h-4" /> Salons publics ouverts</h3>
          <button onClick={fetchRooms} title="Rafraîchir" className="p-2 rounded-xl border border-white/10 text-white/40 hover:text-white hover:border-white/30 transition-colors">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        {rooms.length === 0 ? (
          <div className="text-center py-12">
            <Radio className="w-8 h-8 text-white/15 mx-auto mb-3 animate-pulse" />
            <p className="opacity-30 italic">{loading ? 'Scan du réseau…' : 'Aucun salon public ouvert — crée le premier !'}</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {rooms.map((r) => (
              <button
                key={r.code}
                onClick={() => enter(r.code)}
                className="w-full flex items-center gap-4 p-3.5 rounded-2xl border-2 border-white/5 bg-white/[0.03] hover:border-red-500/50 hover:bg-red-500/5 transition-all text-left group"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-600/30 to-red-900/30 grid place-items-center font-black text-red-300 font-mono shrink-0">
                  {r.code.slice(0, 2)}
                </div>
                <div className="min-w-0 flex-grow">
                  <div className="flex items-center gap-2">
                    <span className="font-black tracking-[0.15em] text-white font-mono">{r.code}</span>
                    <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-md ${r.state === 'lobby' ? 'bg-green-500/15 text-green-400' : 'bg-white/10 text-white/50'}`}>{STATE_LABEL[r.state] || r.state}</span>
                  </div>
                  <span className="text-[11px] text-white/40 flex items-center gap-2">
                    {r.host && <span className="flex items-center gap-1"><Crown className="w-3 h-3 text-yellow-400/70" /> {r.host}</span>}
                    {(r.num_mrwhites ?? 0) > 0 && <span className="text-purple-300/70">{r.num_mrwhites} Mr. White</span>}
                  </span>
                </div>
                <span className="flex items-center gap-1.5 text-white/60 font-bold text-sm shrink-0"><Users className="w-4 h-4" /> {r.players}</span>
                <ArrowRight className="w-5 h-5 text-white/20 group-hover:text-red-400 transition-colors shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UndercoverEntry;
