import React from 'react';
import { useTranslation } from 'react-i18next';
import { Ghost, Lock, HelpCircle, Vote, RotateCcw } from 'lucide-react';
import { UPlayer, UMsg, UResult } from '../../types';

interface UndercoverActionCenterProps {
  state: string;
  isMrWhite: boolean;
  myRole: UPlayer;
  iAmPendingWhite: boolean;
  pendingWhiteName?: string;
  iAmAlive: boolean;
  guess: string;
  setGuess: (v: string) => void;
  submitGuess: (e: React.FormEvent) => void;
  result: UResult | null;
  civilWord?: string;
  undercoverWord?: string;
  isHost: boolean;
  sendAction: (action: string, payload?: any) => void;
  winnerBanner: () => { cls: string; title: string; sub: string };
}

export const UndercoverActionCenter: React.FC<UndercoverActionCenterProps> = ({
  state,
  isMrWhite,
  myRole,
  iAmPendingWhite,
  pendingWhiteName,
  iAmAlive,
  guess,
  setGuess,
  submitGuess,
  result,
  civilWord,
  undercoverWord,
  isHost,
  sendAction,
  winnerBanner,
}) => {
  const { t } = useTranslation();

  return (
    <div className="space-y-5">
      {/* My secret word (or Mr. White card) */}
      {state !== 'ended' && (
        <>
          {isMrWhite ? (
            <div className="flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-br from-purple-500/15 to-transparent border-2 border-purple-400/40">
              <div className="w-16 h-20 rounded-xl bg-purple-500/15 grid place-items-center">
                <Ghost className="w-7 h-7 text-purple-300" />
              </div>
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.25em] text-purple-300">
                  {t('games.undercover.room.you_are_mrwhite', 'Tu es Mr. White')}
                </p>
                <p className="text-lg font-black italic text-white leading-tight">
                  {t('games.undercover.room.mrwhite_card_text', 'Pas de mot — bluffe, devine, survis.')}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-br from-yellow-400/15 to-transparent border-2 border-yellow-400/40">
              {myRole.image ? (
                <img src={myRole.image} alt="" className="w-16 h-20 object-cover rounded-xl shadow-lg" />
              ) : (
                <div className="w-16 h-20 rounded-xl bg-white/10 grid place-items-center">
                  <Lock className="w-6 h-6 text-white/30" />
                </div>
              )}
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.25em] text-yellow-400">
                  {t('games.undercover.room.secret_word_label', 'Ton mot secret')}
                </p>
                <p className="text-2xl font-black italic text-white">{myRole.word ?? '…'}</p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Mr. White guess sub-state */}
      {state === 'mrwhite_guess' && (
        <>
          {iAmPendingWhite ? (
            <form
              onSubmit={submitGuess}
              className="p-4 rounded-2xl bg-purple-500/10 border-2 border-purple-400/50 space-y-3"
            >
              <p className="text-sm text-white/85 flex items-start gap-2">
                <HelpCircle className="w-5 h-5 text-purple-300 shrink-0 mt-0.5" />{' '}
                {t('games.undercover.room.guess_prompt_before', 'Tu es éliminé ! Devine le mot des')}{' '}
                <b className="text-green-400">{t('games.undercover.room.guess_prompt_civils', 'civils')}</b>
                {t(
                  'games.undercover.room.guess_prompt_after',
                  ' — si tu trouves, tu gagnes la partie.'
                )}
              </p>
              <div className="flex gap-3">
                <input
                  value={guess}
                  onChange={(e) => setGuess(e.target.value)}
                  placeholder={t('games.undercover.room.guess_placeholder', 'Le mot des civils…')}
                  aria-label={t('games.undercover.room.guess_aria', 'Deviner le mot')}
                  autoFocus
                  className="flex-grow p-3.5 rounded-2xl bg-white/[0.04] border-2 border-purple-400/40 focus:border-purple-300 outline-none font-bold text-white placeholder:text-white/25"
                />
                <button
                  type="submit"
                  className="px-6 rounded-2xl bg-purple-500 hover:bg-purple-400 text-white font-black italic uppercase tracking-wide transition-colors"
                >
                  {t('games.undercover.room.guess_button', 'Deviner')}
                </button>
              </div>
            </form>
          ) : (
            <div className="p-4 rounded-2xl bg-purple-500/5 border border-purple-400/20 text-sm text-white/80 flex items-center gap-3">
              <Ghost className="w-5 h-5 text-purple-300 shrink-0 animate-pulse" />
              <span>
                <b className="text-purple-300">{pendingWhiteName}</b>
                {t(
                  'games.undercover.room.pending_white_status',
                  ' (Mr. White) a été éliminé et tente de deviner le mot des civils…'
                )}
              </span>
            </div>
          )}
        </>
      )}

      {state === 'playing' && (
        <div className="p-4 rounded-2xl bg-red-500/5 border border-red-500/20 text-sm text-white/80 flex items-start gap-3">
          <Vote className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          {iAmAlive ? (
            <span>
              {t('games.undercover.room.vote_hint_before', 'Décris ton mot sans le nommer, puis')}{' '}
              <b className="text-red-400">{t('games.undercover.room.vote_hint_click', 'clique un agent vivant')}</b>{' '}
              {t(
                'games.undercover.room.vote_hint_after',
                'pour voter. Quand tout le monde a voté, le plus visé est éliminé (égalité → on revote).'
              )}
            </span>
          ) : (
            <span className="italic text-white/50">
              {t('games.undercover.room.spectator_hint', 'Tu es éliminé — observe la partie en spectateur.')}
            </span>
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
              <span className="px-3 py-1.5 rounded-xl bg-green-500/10 text-green-400 font-bold">
                {t('games.undercover.room.civil_word_label', 'Mot civil :')} <span className="text-white">{civilWord}</span>
              </span>
              <span className="px-3 py-1.5 rounded-xl bg-red-500/10 text-red-400 font-bold">
                {t('games.undercover.room.undercover_word_label', 'Mot intrus :')}{' '}
                <span className="text-white">{undercoverWord}</span>
              </span>
            </div>
          </div>
          {isHost && (
            <button
              onClick={() => sendAction('back_to_lobby')}
              className="w-full py-3.5 rounded-2xl bg-yellow-400 hover:bg-yellow-500 text-black font-black italic uppercase tracking-wide flex items-center justify-center gap-2 transition-colors"
            >
              <RotateCcw className="w-5 h-5" /> {t('games.undercover.room.new_game', 'Nouvelle partie')}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
