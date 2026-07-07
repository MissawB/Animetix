import React from 'react';
import { useTranslation } from 'react-i18next';
import { Skull, Crown, Check, Users } from 'lucide-react';
import { UPlayer } from '../../types';

interface UndercoverGameBoardProps {
  players: UPlayer[];
  myId?: string;
  voteTarget: string | null;
  state: string;
  iAmAlive: boolean;
  castVote: (id: string) => void;
  roleMeta: (role?: string) => { label: string; cls: string };
}

export const UndercoverGameBoard: React.FC<UndercoverGameBoardProps> = ({
  players,
  myId,
  voteTarget,
  state,
  iAmAlive,
  castVote,
  roleMeta,
}) => {
  const { t } = useTranslation();

  return (
    <div>
      <h3 className="text-[11px] font-black uppercase opacity-40 mb-5 tracking-[0.25em] flex items-center gap-2">
        <Users className="w-4 h-4" /> {t('games.undercover.room.roster_title', "Unité d'élite")}
      </h3>
      <div className="space-y-2.5">
        {players.length === 0 && (
          <p className="text-sm italic opacity-30">{t('games.undercover.room.waiting_agents', "En attente d'agents…")}</p>
        )}
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
                dead
                  ? 'border-white/5 bg-white/[0.01] opacity-50'
                  : voted
                  ? 'border-red-500 bg-red-500/10'
                  : clickable
                  ? 'border-white/5 bg-white/[0.03] hover:border-red-500/50 hover:bg-red-500/5 cursor-pointer'
                  : 'border-white/5 bg-white/[0.03] cursor-default'
              }`}
            >
              <div
                className={`relative w-11 h-11 rounded-xl grid place-items-center font-black italic shadow-lg shrink-0 ${
                  dead
                    ? 'bg-white/10 text-white/40'
                    : isMe
                    ? 'bg-yellow-400 text-black'
                    : 'bg-gradient-to-br from-navy-700 to-navy-900 text-white/80'
                }`}
              >
                {dead ? <Skull className="w-5 h-5" /> : (p.name || '?')[0].toUpperCase()}
                <span className="absolute -bottom-1 -right-1 text-[8px] font-black bg-black/80 text-white/60 rounded-md px-1 leading-tight">
                  {String(i + 1).padStart(2, '0')}
                </span>
              </div>
              <div className="min-w-0 flex-grow">
                <span className={`font-bold truncate block ${dead ? 'text-white/50 line-through' : 'text-white'}`}>
                  {p.name}
                  {isMe && <span className="text-yellow-400/70"> · {t('games.undercover.room.you', 'toi')}</span>}
                </span>
                {showRole && p.role ? (
                  <span className={`text-[11px] font-black uppercase ${meta.cls}`}>
                    {meta.label}
                    {p.role !== 'MrWhite' && p.word ? ` · ${p.word}` : ''}
                  </span>
                ) : (
                  <span className="text-[10px] font-bold uppercase tracking-widest text-white/25">
                    {dead ? t('games.undercover.room.eliminated', 'Éliminé') : t('games.undercover.room.agent', 'Agent')}
                  </span>
                )}
              </div>
              {p.is_host && <Crown className="w-4 h-4 text-yellow-400 shrink-0" />}
              {state === 'playing' && !dead && p.has_voted && <Check className="w-4 h-4 text-green-400 shrink-0" />}
            </button>
          );
        })}
      </div>
    </div>
  );
};
