import React from 'react';
import { Check, X, Trophy, ArrowRight, Music } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useBlindtestGame } from './hooks/useBlindtestGame';
import { BlindtestBonusRecap } from './components/BlindtestBonusRecap';
import { BlindtestSecretReveal } from './components/BlindtestSecretReveal';
import { BlindtestPlayer } from './components/BlindtestPlayer';

const PANEL = 'rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]';
const SHU_CTA =
  'inline-flex items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-6 py-4 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] cursor-pointer';

const BlindtestPage: React.FC = () => {
  const { t } = useTranslation();
  const {
    gameState,
    isLoading,
    error,
    mode,
    sessionLength,
    hintsEnabled,
    bonusArtistOn,
    bonusSeqOn,
    currentMode,
    lost,
    showVisual,
    hintLevel,
    hintType,
    aspect,
    setAspect,
    baseScore,
    round,
    totalScore,
    results,
    sessionOver,
    guess,
    isPlaying,
    setIsPlaying,
    suggestions,
    showSug,
    setShowSug,
    artistGuess,
    setArtistGuess,
    seqGuess,
    setSeqGuess,
    bonusDone,
    artistCorrect,
    seqCorrect,
    bonusEnabled,
    bonusPending,
    bonusScore,
    roundScore,
    lastRound,
    mediaRef,
    onSubmit,
    onGuessChange,
    pick,
    togglePlay,
    validateBonus,
    finishRound,
    replay,
    navigate,
    restartGame,
  } = useBlindtestGame();

  if (isLoading)
    return (
      <div className="min-h-screen bg-[#0B0C10] text-center py-20 text-[#F4F1E8] font-black animate-pulse uppercase tracking-widest">
        {t('games.blindtest.game.loading', "Récupération de l'audio...")}
      </div>
    );

  if (error) {
    return (
      <div className="min-h-screen bg-[#0B0C10] flex justify-center items-center py-20 px-6">
        <div className={`${PANEL} border-[#E8442B]/40 p-8 md:p-10 text-center max-w-md`}>
          <h2 className="font-manga text-2xl font-black italic uppercase text-[#E8442B] mb-4">
            {t('games.blindtest.game.error_title', 'SIGNAL PERDU')}
          </h2>
          <p className="mb-8 font-bold text-[#8F94A5]">{error}</p>
          <button className={SHU_CTA} onClick={() => restartGame()}>
            {t('games.blindtest.game.reconnect', 'RECONNEXION')}
          </button>
        </div>
      </div>
    );
  }

  if (!gameState) return null;

  const isSession = mode === 'session';

  if (sessionOver) {
    const maxScore = sessionLength * 100;
    const wins = results.filter((r) => r.won).length;
    return (
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-2xl mx-auto px-6 py-20">
          <div className={`${PANEL} p-8 md:p-10 text-center`}>
            <Trophy className="w-14 h-14 text-[#FDB913] mx-auto mb-4" />
            <h1 className="font-manga text-4xl font-black italic uppercase text-[#F4F1E8]">
              {t('games.blindtest.game.session_over', 'Session terminée')}
            </h1>
            <p className="font-manga mt-6 text-6xl font-black italic text-[#FDB913]">
              {totalScore}
            </p>
            <p className="text-xs font-black uppercase tracking-widest text-[#8F94A5] mt-1">
              {t('games.blindtest.game.session_summary', {
                defaultValue: 'sur {{max}} points · {{wins}}/{{total}} trouvés',
                max: maxScore,
                wins,
                total: sessionLength,
              })}
            </p>

            <div className="mt-8 grid grid-cols-5 sm:grid-cols-10 gap-1.5">
              {results.map((r, i) => (
                <div
                  key={i}
                  title={t('games.blindtest.game.round_tooltip', {
                    defaultValue: 'Manche {{num}}: {{score}} pts{{secret}}',
                    num: i + 1,
                    score: r.score,
                    secret: r.secret ? ` — ${r.secret}` : '',
                  })}
                  className={`h-8 rounded-md grid place-items-center text-[10px] font-black ${
                    r.won ? 'bg-[#FDB913]/15 text-[#FDB913]' : 'bg-[#E8442B]/15 text-[#E8442B]'
                  }`}
                >
                  {r.score}
                </div>
              ))}
            </div>

            <div className="flex gap-3 justify-center mt-10">
              <button className={SHU_CTA} onClick={() => navigate('/blindtest/')}>
                {t('games.blindtest.game.new_session', 'NOUVELLE SESSION')}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-7xl mx-auto px-6 py-16">
        {/* Session progress */}
        {isSession && (
          <div className="max-w-7xl mx-auto mb-8">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
                {t('games.blindtest.game.round_progress', {
                  defaultValue: 'Manche {{round}} / {{total}}',
                  round,
                  total: sessionLength,
                })}
              </span>
              <span className="text-xs font-black uppercase tracking-widest text-[#FDB913]">
                {t('games.blindtest.game.points', {
                  defaultValue: '{{score}} pts',
                  score: totalScore,
                })}
              </span>
            </div>
            <div className="w-full h-2 rounded-full bg-[#F4F1E8]/10 overflow-hidden">
              <div
                className="h-full bg-[#FDB913] transition-all"
                style={{ width: `${((round - 1) / sessionLength) * 100}%` }}
              />
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* LECTEUR */}
          <div className={`${PANEL} p-6`}>
            {gameState.gameOver ? (
              <video
                src={gameState.video_url}
                controls
                className="w-full rounded-2xl"
                aria-label={t(
                  'games.blindtest.game.video_player_aria',
                  "Lecteur vidéo de l'extrait",
                )}
              >
                <track kind="captions" />
              </video>
            ) : (
              <BlindtestPlayer
                videoUrl={gameState.video_url ?? ''}
                hintsEnabled={hintsEnabled}
                showVisual={showVisual}
                hintType={hintType}
                hintLevel={hintLevel}
                aspect={aspect}
                setAspect={setAspect}
                isPlaying={isPlaying}
                setIsPlaying={setIsPlaying}
                mediaRef={mediaRef}
                togglePlay={togglePlay}
                currentMode={currentMode}
                attemptsLeft={gameState.attemptsLeft}
              />
            )}
          </div>

          {/* JEU */}
          <div className={`${PANEL} p-8 md:p-10`}>
            <h2 className="font-manga text-3xl font-black italic uppercase mb-8 flex items-center gap-3 text-[#F4F1E8]">
              <span className="explore-stamp -rotate-2" aria-hidden>
                歌
              </span>
              <Music className="w-8 h-8 text-[#FDB913]" />{' '}
              {t('games.blindtest.game.title', "DÉCOUVREZ L'ANIMÉ")}
            </h2>
            {!gameState.gameOver ? (
              <div className="space-y-6">
                <div className="relative">
                  <input
                    type="text"
                    value={guess}
                    onChange={(e) => onGuessChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && guess.trim()) {
                        setShowSug(false);
                        onSubmit();
                      }
                    }}
                    onFocus={() => {
                      if (suggestions.length) setShowSug(true);
                    }}
                    onBlur={() => setTimeout(() => setShowSug(false), 150)}
                    className="w-full p-4 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none font-bold text-[#F4F1E8] transition-colors placeholder:text-[#8F94A5]/60"
                    placeholder={t('games.blindtest.game.input_placeholder', "Titre de l'animé...")}
                    aria-label={t('games.blindtest.game.input_aria', "Titre de l'animé")}
                    autoComplete="off"
                  />
                  {showSug && suggestions.length > 0 && (
                    <ul className="absolute z-30 left-0 right-0 mt-2 bg-[#0F1016] rounded-xl border border-[#F4F1E8]/10 shadow-2xl overflow-hidden max-h-72 overflow-y-auto">
                      {suggestions.map((tt) => (
                        <li key={tt}>
                          <button
                            type="button"
                            onMouseDown={(e) => {
                              e.preventDefault();
                              pick(tt);
                            }}
                            className="w-full text-left px-4 py-3 hover:bg-[#FDB913]/10 font-bold text-sm text-[#F4F1E8] truncate transition-colors"
                          >
                            {tt}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <button className={`${SHU_CTA} w-full`} onClick={() => onSubmit()}>
                  {t('games.blindtest.game.submit', 'VALIDER MA RÉPONSE')}
                </button>
              </div>
            ) : bonusPending ? (
              <div className="p-6 rounded-2xl text-center border-2 bg-[#FDB913]/[0.06] border-[#FDB913]/40">
                <p className="font-manga font-black text-2xl italic text-[#FDB913]">
                  {t('games.blindtest.game.found_base_score', {
                    defaultValue: '🎉 Trouvé ! +{{score}} pts',
                    score: baseScore,
                  })}
                </p>
                <BlindtestSecretReveal
                  title={gameState.secret_title}
                  image={gameState.secret_image}
                />
                <div className="mt-5 pt-5 border-t border-[#F4F1E8]/10 space-y-3 text-left max-w-sm mx-auto">
                  <p className="text-[11px] font-black uppercase tracking-widest text-[#FDB913] text-center">
                    {t('games.blindtest.game.bonus_title', 'Bonus (+25 pts chacun)')}
                  </p>
                  {bonusArtistOn && (
                    <input
                      value={artistGuess}
                      onChange={(e) => setArtistGuess(e.target.value)}
                      placeholder={t(
                        'games.blindtest.game.singer_placeholder',
                        'Chanteur / interprète…',
                      )}
                      aria-label={t('games.blindtest.game.singer_aria', 'Chanteur')}
                      className="w-full p-3 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none font-bold text-[#F4F1E8] transition-colors placeholder:text-[#8F94A5]/60"
                    />
                  )}
                  {bonusSeqOn && (
                    <input
                      type="number"
                      value={seqGuess}
                      onChange={(e) => setSeqGuess(e.target.value)}
                      placeholder={t('games.blindtest.game.number_placeholder', {
                        defaultValue: "Numéro d'{{format}} (ex: 1)",
                        format: currentMode === 'ED' ? 'ending' : 'opening',
                      })}
                      aria-label={t('games.blindtest.game.number_aria', "Numéro d'opening")}
                      className="w-full p-3 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none font-bold text-[#F4F1E8] transition-colors placeholder:text-[#8F94A5]/60"
                    />
                  )}
                  <button className={`${SHU_CTA} w-full`} onClick={validateBonus}>
                    {t('games.blindtest.game.submit_bonus', 'VALIDER LE BONUS')}
                  </button>
                </div>
              </div>
            ) : isSession ? (
              <div
                className={`p-6 rounded-2xl text-center border-2 ${gameState.won ? 'bg-[#FDB913]/[0.06] border-[#FDB913]/40' : 'bg-[#E8442B]/[0.06] border-[#E8442B]/40'}`}
              >
                <p
                  className={`font-black text-2xl ${gameState.won ? 'text-[#FDB913]' : 'text-[#E8442B]'}`}
                >
                  {gameState.won
                    ? t('games.blindtest.game.round_won_score', {
                        defaultValue: '🎉 +{{score}} pts',
                        score: roundScore,
                      })
                    : t('games.blindtest.game.round_lost', '😵 Manche perdue')}
                </p>
                <BlindtestSecretReveal
                  title={gameState.secret_title}
                  image={gameState.secret_image}
                />
                {bonusEnabled && bonusDone && (
                  <BlindtestBonusRecap
                    bonusArtistOn={bonusArtistOn}
                    bonusSeqOn={bonusSeqOn}
                    artistCorrect={artistCorrect}
                    seqCorrect={seqCorrect}
                    artists={gameState.artists}
                    sequence={gameState.sequence}
                    type={currentMode}
                  />
                )}
                <button className={`${SHU_CTA} mt-6`} onClick={finishRound}>
                  {lastRound
                    ? t('games.blindtest.game.see_result', 'VOIR LE RÉSULTAT')
                    : t('games.blindtest.game.next_round', 'MANCHE SUIVANTE')}{' '}
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            ) : lost ? (
              <div className="bg-[#E8442B]/[0.06] border-2 border-[#E8442B]/40 p-6 rounded-2xl text-center">
                <p className="text-[#E8442B] font-black text-2xl">
                  {t('games.blindtest.game.lost', '😵 PERDU !')}
                </p>
                <BlindtestSecretReveal
                  title={gameState.secret_title}
                  image={gameState.secret_image}
                />
                <button className={`${SHU_CTA} mt-6`} onClick={replay}>
                  {t('games.blindtest.game.replay', 'REJOUER')}
                </button>
              </div>
            ) : (
              <div className="bg-[#FDB913]/[0.06] border-2 border-[#FDB913]/40 p-6 rounded-2xl text-center">
                <p className="text-[#FDB913] font-black text-2xl animate-bounce">
                  {t('games.blindtest.game.well_played', '🎉 BIEN JOUÉ !')}
                  {bonusScore > 0
                    ? t('games.blindtest.game.bonus_suffix', {
                        defaultValue: ' +{{score}} bonus',
                        score: bonusScore,
                      })
                    : ''}
                </p>
                <BlindtestSecretReveal
                  title={gameState.secret_title}
                  image={gameState.secret_image}
                />
                {bonusEnabled && bonusDone && (
                  <BlindtestBonusRecap
                    bonusArtistOn={bonusArtistOn}
                    bonusSeqOn={bonusSeqOn}
                    artistCorrect={artistCorrect}
                    seqCorrect={seqCorrect}
                    artists={gameState.artists}
                    sequence={gameState.sequence}
                    type={currentMode}
                  />
                )}
                <button className={`${SHU_CTA} mt-6`} onClick={replay}>
                  {t('games.blindtest.game.replay', 'REJOUER')}
                </button>
              </div>
            )}

            <div className="mt-10 space-y-3">
              <h4 className="text-[10px] font-black text-[#8F94A5]/60 uppercase tracking-widest">
                {t('games.blindtest.game.previous_attempts', 'Tentatives précédentes')}
              </h4>
              {gameState.guesses.map((g: { title: string; is_correct: boolean }, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-4 bg-[#0B0C10] rounded-xl border border-[#F4F1E8]/10"
                >
                  <span className="font-bold text-[#F4F1E8]/80">{g.title}</span>
                  {g.is_correct ? (
                    <Check className="text-[#FDB913] w-5 h-5" />
                  ) : (
                    <X className="text-[#E8442B] w-5 h-5" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BlindtestPage;
