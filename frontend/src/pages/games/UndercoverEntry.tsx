import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../utils/apiClient';
import {
  Fingerprint,
  Plus,
  Globe,
  EyeOff,
  LogIn,
  Users,
  RefreshCw,
  ArrowRight,
  Radio,
  Crown,
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

const panel = 'rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]';

const UndercoverEntry: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [createPublic, setCreatePublic] = useState(true);
  const [joinCode, setJoinCode] = useState('');

  const STATE_LABEL: Record<string, string> = {
    lobby: t('games.undercover.entry.state_lobby', 'En attente'),
    playing: t('games.undercover.entry.state_playing', 'En partie'),
    mrwhite_guess: t('games.undercover.entry.state_playing', 'En partie'),
    ended: t('games.undercover.entry.state_ended', 'Terminé'),
  };

  const enter = (code: string, visibility?: 'public' | 'private') => {
    const c = code.trim().toUpperCase();
    if (!c) return;
    navigate(`/undercover/room/${c}/${visibility === 'public' ? '?visibility=public' : ''}`);
  };

  // Live listing of public rooms — polled, refetched on mount (the list is
  // ephemeral, so we don't trust a persisted cache).
  const {
    data: rooms = [],
    isFetching,
    refetch,
  } = useQuery<PublicRoom[]>({
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
      <header className="relative mb-8">
        <div
          className="explore-halftone pointer-events-none absolute -inset-x-6 -top-8 h-40"
          aria-hidden
        />
        <div className="relative flex items-center gap-3">
          <span className="explore-stamp -rotate-2" aria-hidden>
            潜
          </span>
          <span className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
            <Fingerprint className="w-4 h-4" />{' '}
            {t('games.undercover.classified_badge', 'Dossier classifié · Undercover')}
          </span>
        </div>
        <h1 className="font-manga relative mt-4 text-5xl sm:text-6xl font-black italic uppercase tracking-tighter text-[#F4F1E8] leading-none">
          {t('games.undercover.entry.title', "Salle d'opérations")}
        </h1>
        <p className="relative mt-3 max-w-2xl text-sm font-bold uppercase tracking-widest text-[#8F94A5]">
          {t('games.undercover.entry.subtitle', 'Crée une mission ou rejoins une unité existante')}
        </p>
        <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Create */}
        <div className={`${panel} p-6 space-y-5`}>
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-[#8F94A5] flex items-center gap-2">
            <Plus className="w-4 h-4" />{' '}
            {t('games.undercover.entry.create_title', 'Créer un salon')}
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setCreatePublic(true)}
              className={`flex items-center justify-center gap-2 py-2.5 rounded-xl border text-xs font-black uppercase transition-colors ${createPublic ? 'border-[#FDB913] bg-[#FDB913]/15 text-[#FDB913]' : 'border-[#F4F1E8]/10 text-[#8F94A5] hover:border-[#FDB913]/40'}`}
            >
              <Globe className="w-3.5 h-3.5" /> {t('games.undercover.visibility.public', 'Public')}
            </button>
            <button
              onClick={() => setCreatePublic(false)}
              className={`flex items-center justify-center gap-2 py-2.5 rounded-xl border text-xs font-black uppercase transition-colors ${!createPublic ? 'border-[#E8442B] bg-[#E8442B]/15 text-[#E8442B]' : 'border-[#F4F1E8]/10 text-[#8F94A5] hover:border-[#E8442B]/40'}`}
            >
              <EyeOff className="w-3.5 h-3.5" /> {t('games.undercover.visibility.private', 'Privé')}
            </button>
          </div>
          <p className="text-[11px] text-[#8F94A5]/80 italic">
            {createPublic
              ? t(
                  'games.undercover.entry.public_hint',
                  'Apparaîtra dans la liste des salons publics — tout le monde peut rejoindre.',
                )
              : t(
                  'games.undercover.entry.private_hint',
                  "Accessible uniquement via le code ou l'URL que tu partages.",
                )}
          </p>
          <button
            onClick={() => enter(newCode(), createPublic ? 'public' : 'private')}
            className="w-full py-4 rounded-xl bg-[#E8442B] hover:bg-[#c93a24] text-[#F4F1E8] font-manga font-black italic uppercase tracking-widest text-lg transition-colors flex items-center justify-center gap-2 border-none cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
          >
            <Plus className="w-5 h-5" />{' '}
            {t('games.undercover.entry.create_button', 'Créer la mission')}
          </button>
        </div>

        {/* Join private */}
        <div className={`${panel} p-6 space-y-5`}>
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-[#8F94A5] flex items-center gap-2">
            <LogIn className="w-4 h-4" />{' '}
            {t('games.undercover.entry.join_title', 'Rejoindre un salon privé')}
          </h3>
          <p className="text-[11px] text-[#8F94A5]/80 italic">
            {t(
              'games.undercover.entry.join_hint',
              "Saisis le code à 5 caractères qu'on t'a partagé.",
            )}
          </p>
          <input
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase().slice(0, 8))}
            onKeyDown={(e) => {
              if (e.key === 'Enter') enter(joinCode);
            }}
            placeholder={t('games.undercover.entry.code_placeholder', 'CODE…')}
            aria-label={t('games.undercover.entry.code_aria', 'Code du salon')}
            className="w-full p-3.5 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none font-black tracking-[0.3em] text-2xl text-center text-[#F4F1E8] placeholder:text-[#8F94A5]/40 font-mono uppercase transition-colors"
          />
          <button
            onClick={() => enter(joinCode)}
            disabled={!joinCode.trim()}
            className="w-full py-4 rounded-xl bg-[#FDB913] enabled:hover:bg-[#e0a50f] text-[#0B0C10] font-manga font-black italic uppercase tracking-widest text-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 border-none cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#F4F1E8]"
          >
            <ArrowRight className="w-5 h-5" />{' '}
            {t('games.undercover.entry.join_button', 'Rejoindre')}
          </button>
        </div>
      </div>

      {/* Public listing */}
      <div className={`${panel} p-6 mt-6`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[11px] font-black uppercase tracking-[0.25em] text-[#8F94A5] flex items-center gap-2">
            <Globe className="w-4 h-4" />{' '}
            {t('games.undercover.entry.public_rooms_title', 'Salons publics ouverts')}
          </h3>
          <button
            onClick={fetchRooms}
            title={t('games.undercover.entry.refresh_title', 'Rafraîchir')}
            className="p-2 rounded-xl border border-[#F4F1E8]/10 text-[#8F94A5] hover:text-[#F4F1E8] hover:border-[#F4F1E8]/30 transition-colors bg-transparent cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        {rooms.length === 0 ? (
          <div className="text-center py-12">
            <Radio className="w-8 h-8 text-[#8F94A5]/30 mx-auto mb-3 animate-pulse" />
            <p className="text-[#8F94A5]/60 italic">
              {loading
                ? t('games.undercover.entry.scanning', 'Scan du réseau…')
                : t(
                    'games.undercover.entry.no_rooms',
                    'Aucun salon public ouvert — crée le premier !',
                  )}
            </p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {rooms.map((r) => (
              <button
                key={r.code}
                onClick={() => enter(r.code)}
                className="w-full flex items-center gap-4 p-3.5 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] hover:border-[#E8442B]/50 hover:bg-[#E8442B]/5 transition-colors text-left group cursor-pointer"
              >
                <div className="w-12 h-12 rounded-xl border border-[#E8442B]/30 bg-[#E8442B]/10 grid place-items-center font-black text-[#E8442B] font-mono shrink-0">
                  {r.code.slice(0, 2)}
                </div>
                <div className="min-w-0 flex-grow">
                  <div className="flex items-center gap-2">
                    <span className="font-black tracking-[0.15em] text-[#F4F1E8] font-mono">
                      {r.code}
                    </span>
                    <span
                      className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-md ${r.state === 'lobby' ? 'bg-[#FDB913]/15 text-[#FDB913]' : 'bg-[#F4F1E8]/10 text-[#8F94A5]'}`}
                    >
                      {STATE_LABEL[r.state] || r.state}
                    </span>
                  </div>
                  <span className="text-[11px] text-[#8F94A5] flex items-center gap-2">
                    {r.host && (
                      <span className="flex items-center gap-1">
                        <Crown className="w-3 h-3 text-[#FDB913]/70" /> {r.host}
                      </span>
                    )}
                    {(r.num_mrwhites ?? 0) > 0 && (
                      <span className="text-[#F4F1E8]/70">
                        {t('games.undercover.entry.mrwhite_count', {
                          defaultValue: '{{count}} Mr. White',
                          count: r.num_mrwhites,
                        })}
                      </span>
                    )}
                  </span>
                </div>
                <span className="flex items-center gap-1.5 text-[#8F94A5] font-bold text-sm shrink-0">
                  <Users className="w-4 h-4" /> {r.players}
                </span>
                <ArrowRight className="w-5 h-5 text-[#8F94A5]/40 group-hover:text-[#E8442B] transition-colors shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UndercoverEntry;
