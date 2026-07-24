import React from 'react';
import { useTranslation } from 'react-i18next';
import { Fingerprint, Check, Copy, Radio, Globe, EyeOff } from 'lucide-react';
import { useUndercoverRoom } from '../../hooks/useUndercoverRoom';
import { UndercoverJoinForm } from '../../components/games/UndercoverJoinForm';
import { UndercoverLobbySettings } from '../../components/games/UndercoverLobbySettings';
import { UndercoverGameBoard } from '../../components/games/UndercoverGameBoard';
import { UndercoverChatPanel } from '../../components/games/UndercoverChatPanel';
import { UndercoverActionCenter } from '../../components/games/UndercoverActionCenter';

const MIN_PLAYERS = 3;

const UndercoverRoom: React.FC = () => {
  const { t } = useTranslation();

  const {
    roomCode,
    connected,
    players,
    myId,
    me,
    isHost,
    state,
    messages,
    myRole,
    categories,
    difficulty,
    isPublic,
    under,
    white,
    round,
    pendingWhite,
    pendingWhiteName,
    result,
    civilWord,
    undercoverWord,
    civilsCount,
    voteTarget,
    maxUnderSlider,
    maxWhiteSlider,

    // Local form states
    name,
    setName,
    chat,
    setChat,
    guess,
    setGuess,
    copied,

    // Handlers
    submitName,
    castVote,
    submitGuess,
    sendChat,
    copyCode,
    applySettings,
    toggleCategory,
    sendAction,
  } = useUndercoverRoom();

  // Paint revealed roles metadata.
  const roleMeta = (role?: string): { label: string; cls: string } => {
    if (role === 'Undercover')
      return { label: t('games.undercover.roles.intruder', '⚠ Intrus'), cls: 'text-[#E8442B]' };
    if (role === 'MrWhite')
      return { label: t('games.undercover.roles.mrwhite', '◐ Mr. White'), cls: 'text-[#F4F1E8]' };
    return { label: t('games.undercover.roles.civil', '✓ Civil'), cls: 'text-[#FDB913]' };
  };

  const STATUS: Record<string, string> = {
    lobby: t('games.undercover.status.lobby', 'Briefing en cours — recrutez votre unité'),
    playing: t('games.undercover.status.playing', 'Infiltration en cours — votez pour éliminer'),
    mrwhite_guess: t(
      'games.undercover.status.mrwhite_guess',
      'Un Mr. White tente de deviner le mot…',
    ),
    ended: t('games.undercover.status.ended', 'Mission terminée — dossier déclassifié'),
  };

  if (!connected) {
    return (
      <div className="min-h-[60vh] grid place-items-center">
        <div className="flex flex-col items-center gap-4 text-[#E8442B]">
          <Radio className="w-12 h-12 animate-pulse" />
          <p className="font-black uppercase tracking-[0.4em] animate-pulse">
            {t('games.undercover.room.connecting', 'Connexion au réseau sécurisé…')}
          </p>
        </div>
      </div>
    );
  }

  const iAmAlive = me?.alive !== false;
  const code = (roomCode || '').toUpperCase();
  const iAmPendingWhite = state === 'mrwhite_guess' && pendingWhite === myId;
  const isMrWhite = myRole.role === 'MrWhite';

  const panel = 'rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]';

  // ── Winner banner content (ended) ───────────────────────────────────────
  const winnerBanner = () => {
    const w = result?.winner;
    const whites = result?.mrwhite_winners || [];
    if (w === 'civils') {
      return {
        cls: 'bg-[#FDB913]/10 border-[#FDB913]',
        title: t('games.undercover.room.winner_civils_title', '🎯 Les Civils gagnent !'),
        sub: t('games.undercover.room.winner_civils_sub', 'Toutes les menaces ont été démasquées.'),
      };
    }
    if (w === 'mrwhite') {
      return {
        cls: 'bg-[#F4F1E8]/10 border-[#F4F1E8]',
        title: t('games.undercover.room.winner_mrwhite_title', '◐ Mr. White gagne !'),
        sub: t('games.undercover.room.winner_mrwhite_sub', {
          defaultValue: '{{names}} a deviné le mot des civils.',
          names: whites.join(', '),
        }),
      };
    }
    return {
      cls: 'bg-[#E8442B]/10 border-[#E8442B]',
      title: t('games.undercover.room.winner_intruders_title', '🕵️ Les infiltrés gagnent !'),
      sub: whites.length
        ? t('games.undercover.room.winner_intruders_sub_mrwhite', {
            defaultValue: "Mr. White {{names}} survit jusqu'au bout.",
            names: whites.join(', '),
          })
        : t('games.undercover.room.winner_intruders_sub', 'Ils ont atteint la parité.'),
    };
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      {/* ── Mission banner ───────────────────────────────── */}
      <div className="relative overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-7 sm:p-9 mb-8">
        <div
          className="explore-halftone absolute -inset-x-6 -top-10 h-40 pointer-events-none"
          aria-hidden
        />
        <div className="relative">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.4em] text-[#E8442B] mb-3">
            <span className="explore-stamp -rotate-2" aria-hidden>
              潜
            </span>
            <Fingerprint className="w-4 h-4" />{' '}
            {t('games.undercover.classified_badge', 'Dossier classifié · Undercover')}
            <span className="ml-2 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#E8442B]/15 text-[#E8442B] normal-case tracking-wider">
              <span className="w-1.5 h-1.5 rounded-full bg-[#E8442B] animate-pulse" />{' '}
              {players.length > 1
                ? t('games.undercover.room.agents_count_plural', {
                    defaultValue: '{{count}} agents',
                    count: players.length,
                  })
                : t('games.undercover.room.agents_count', {
                    defaultValue: '{{count}} agent',
                    count: players.length,
                  })}
            </span>
            {round > 0 && state !== 'ended' && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-[#F4F1E8]/10 text-[#8F94A5] normal-case tracking-wider">
                {t('games.undercover.room.round_badge', {
                  defaultValue: 'Manche {{round}}',
                  round,
                })}
              </span>
            )}
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full normal-case tracking-wider ${
                isPublic ? 'bg-[#FDB913]/15 text-[#FDB913]' : 'bg-[#F4F1E8]/10 text-[#8F94A5]'
              }`}
            >
              {isPublic ? <Globe className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
              {isPublic
                ? t('games.undercover.visibility.public', 'Public')
                : t('games.undercover.visibility.private', 'Privé')}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
            <h1 className="text-5xl sm:text-7xl font-black italic font-manga uppercase tracking-tighter text-[#F4F1E8] leading-none">
              {t('games.undercover.room.title', 'Mission')}
            </h1>
            <button
              onClick={copyCode}
              title={t('games.undercover.room.copy_code_title', 'Copier le code de la salle')}
              className="group inline-flex items-center gap-3 rounded-xl border border-[#FDB913]/40 bg-[#FDB913]/10 hover:bg-[#FDB913]/20 px-5 py-2.5 transition-colors"
            >
              <span className="text-3xl sm:text-4xl font-black tracking-[0.25em] text-[#FDB913] font-mono">
                {code}
              </span>
              {copied ? (
                <Check className="w-5 h-5 text-[#FDB913]" />
              ) : (
                <Copy className="w-5 h-5 text-[#FDB913] opacity-60 group-hover:opacity-100" />
              )}
            </button>
          </div>
          <p className="mt-3 text-sm font-bold uppercase tracking-widest text-[#8F94A5]">
            {STATUS[state]}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Roster ─────────────────────────────────────── */}
        <div className={`${panel} p-6 h-fit lg:col-span-1`}>
          <UndercoverGameBoard
            players={players}
            myId={myId}
            voteTarget={voteTarget}
            state={state}
            iAmAlive={iAmAlive}
            castVote={castVote}
            roleMeta={roleMeta}
          />
        </div>

        {/* ── Game + chat ─────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-6">
          <div className={`${panel} p-7`}>
            {/* LOBBY */}
            {state === 'lobby' && (
              <div className="space-y-7">
                <UndercoverJoinForm
                  name={name}
                  setName={setName}
                  submitName={submitName}
                  meName={me?.name}
                />
                <UndercoverLobbySettings
                  isHost={isHost}
                  isPublic={isPublic}
                  categories={categories}
                  difficulty={difficulty}
                  under={under}
                  white={white}
                  players={players}
                  civilsCount={civilsCount}
                  maxUnderSlider={maxUnderSlider}
                  maxWhiteSlider={maxWhiteSlider}
                  applySettings={applySettings}
                  toggleCategory={toggleCategory}
                  sendAction={sendAction}
                  MIN_PLAYERS={MIN_PLAYERS}
                />
              </div>
            )}

            {/* PLAYING / MR. WHITE GUESS / ENDED */}
            {state !== 'lobby' && (
              <UndercoverActionCenter
                state={state}
                isMrWhite={isMrWhite}
                myRole={myRole}
                iAmPendingWhite={iAmPendingWhite}
                pendingWhiteName={pendingWhiteName}
                iAmAlive={iAmAlive}
                guess={guess}
                setGuess={setGuess}
                submitGuess={submitGuess}
                result={result}
                civilWord={civilWord}
                undercoverWord={undercoverWord}
                isHost={isHost}
                sendAction={sendAction}
                winnerBanner={winnerBanner}
              />
            )}
          </div>

          {/* Comms / chat */}
          <div className={`${panel} p-6 flex flex-col`}>
            <UndercoverChatPanel
              messages={messages}
              chat={chat}
              setChat={setChat}
              sendChat={sendChat}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default UndercoverRoom;
