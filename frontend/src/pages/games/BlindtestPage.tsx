import React from 'react';
import { Check, X, Trophy, ArrowRight, Music } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { useBlindtestGame } from './hooks/useBlindtestGame';
import { BlindtestBonusRecap } from './components/BlindtestBonusRecap';
import { BlindtestSecretReveal } from './components/BlindtestSecretReveal';
import { BlindtestPlayer } from './components/BlindtestPlayer';

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
      <div className="text-center py-20 text-white font-black animate-pulse uppercase tracking-widest">
        {t('games.blindtest.game.loading', "Récupération de l'audio...")}
      </div>
    );

  if (error) {
    return (
      <div className="flex justify-center items-center py-20">
        <Card padding="lg" className="text-center border-red-500/50">
          <h2 className="text-2xl font-black text-red-500 mb-4 italic">
            {t('games.blindtest.game.error_title', 'SIGNAL PERDU')}
          </h2>
          <p className="mb-8 opacity-60 font-bold">{error}</p>
          <Button variant="danger" onClick={() => restartGame()}>
            {t('games.blindtest.game.reconnect', 'RECONNEXION')}
          </Button>
        </Card>
      </div>
    );
  }

  if (!gameState) return null;

  const isSession = mode === 'session';

  if (sessionOver) {
    const maxScore = sessionLength * 100;
    const wins = results.filter((r) => r.won).length;
    return (
      <div className="max-w-2xl mx-auto px-6 py-20">
        <Card padding="lg" className="text-center">
          <Trophy className="w-14 h-14 text-yellow-400 mx-auto mb-4" />
          <h1 className="text-4xl font-black italic manga-font uppercase text-black dark:text-white">
            {t('games.blindtest.game.session_over', 'Session terminée')}
          </h1>
          <p className="mt-6 text-6xl font-black manga-font text-yellow-500">{totalScore}</p>
          <p className="text-xs font-black uppercase tracking-widest text-gray-400 mt-1">
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
                  r.won
                    ? 'bg-green-500/20 text-green-600 dark:text-green-400'
                    : 'bg-red-500/15 text-red-500'
                }`}
              >
                {r.score}
              </div>
            ))}
          </div>

          <div className="flex gap-3 justify-center mt-10">
            <Button variant="primary" onClick={() => navigate('/blindtest/')}>
              {t('games.blindtest.game.new_session', 'NOUVELLE SESSION')}
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      {/* Session progress */}
      {isSession && (
        <div className="max-w-7xl mx-auto mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-black uppercase tracking-widest text-gray-500 dark:text-gray-400">
              {t('games.blindtest.game.round_progress', {
                defaultValue: 'Manche {{round}} / {{total}}',
                round,
                total: sessionLength,
              })}
            </span>
            <span className="text-xs font-black uppercase tracking-widest text-yellow-600 dark:text-yellow-400">
              {t('games.blindtest.game.points', {
                defaultValue: '{{score}} pts',
                score: totalScore,
              })}
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-black/10 dark:bg-white/10 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 transition-all"
              style={{ width: `${((round - 1) / sessionLength) * 100}%` }}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* LECTEUR */}
        <Card padding="md">
          {gameState.gameOver ? (
            <video
              src={gameState.video_url}
              controls
              className="w-full rounded-3xl shadow-lg"
              aria-label={t('games.blindtest.game.video_player_aria', "Lecteur vidéo de l'extrait")}
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
        </Card>

        {/* JEU */}
        <Card padding="lg">
          <h2 className="text-3xl font-black mb-8 flex items-center gap-3 italic">
            <Music className="w-8 h-8 text-yellow-400" />{' '}
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
                  className="w-full p-4 rounded-2xl bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
                  placeholder={t('games.blindtest.game.input_placeholder', "Titre de l'animé...")}
                  aria-label={t('games.blindtest.game.input_aria', "Titre de l'animé")}
                  autoComplete="off"
                />
                {showSug && suggestions.length > 0 && (
                  <ul className="absolute z-30 left-0 right-0 mt-2 bg-white dark:bg-[#0f0f1a] rounded-2xl border border-gray-100 dark:border-white/10 shadow-2xl overflow-hidden max-h-72 overflow-y-auto">
                    {suggestions.map((tt) => (
                      <li key={tt}>
                        <button
                          type="button"
                          onMouseDown={(e) => {
                            e.preventDefault();
                            pick(tt);
                          }}
                          className="w-full text-left px-4 py-3 hover:bg-yellow-400/10 font-bold text-sm text-black dark:text-white truncate transition-colors"
                        >
                          {tt}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <Button variant="primary" fullWidth onClick={() => onSubmit()}>
                {t('games.blindtest.game.submit', 'VALIDER MA RÉPONSE')}
              </Button>
            </div>
          ) : bonusPending ? (
            <div className="p-6 rounded-2xl text-center border-2 bg-green-500/10 border-green-500">
              <p className="font-black text-2xl text-green-500">
                {t('games.blindtest.game.found_base_score', {
                  defaultValue: '🎉 Trouvé ! +{{score}} pts',
                  score: baseScore,
                })}
              </p>
              <BlindtestSecretReveal
                title={gameState.secret_title}
                image={gameState.secret_image}
              />
              <div className="mt-5 pt-5 border-t border-white/10 space-y-3 text-left max-w-sm mx-auto">
                <p className="text-[11px] font-black uppercase tracking-widest text-yellow-500 text-center">
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
                    className="w-full p-3 rounded-xl bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
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
                    className="w-full p-3 rounded-xl bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-yellow-400 outline-none font-bold"
                  />
                )}
                <Button variant="primary" fullWidth onClick={validateBonus}>
                  {t('games.blindtest.game.submit_bonus', 'VALIDER LE BONUS')}
                </Button>
              </div>
            </div>
          ) : isSession ? (
            <div
              className={`p-6 rounded-2xl text-center border-2 ${gameState.won ? 'bg-green-500/10 border-green-500' : 'bg-red-500/10 border-red-500'}`}
            >
              <p
                className={`font-black text-2xl ${gameState.won ? 'text-green-500' : 'text-red-500'}`}
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
              <Button variant="primary" className="mt-6" onClick={finishRound}>
                {lastRound
                  ? t('games.blindtest.game.see_result', 'VOIR LE RÉSULTAT')
                  : t('games.blindtest.game.next_round', 'MANCHE SUIVANTE')}{' '}
                <ArrowRight className="w-5 h-5" />
              </Button>
            </div>
          ) : lost ? (
            <div className="bg-red-500/10 border-2 border-red-500 p-6 rounded-2xl text-center">
              <p className="text-red-500 font-black text-2xl">
                {t('games.blindtest.game.lost', '😵 PERDU !')}
              </p>
              <BlindtestSecretReveal
                title={gameState.secret_title}
                image={gameState.secret_image}
              />
              <Button variant="danger" className="mt-6" onClick={replay}>
                {t('games.blindtest.game.replay', 'REJOUER')}
              </Button>
            </div>
          ) : (
            <div className="bg-green-500/10 border-2 border-green-500 p-6 rounded-2xl text-center">
              <p className="text-green-500 font-black text-2xl animate-bounce">
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
              <Button variant="success" className="mt-6" onClick={replay}>
                {t('games.blindtest.game.replay', 'REJOUER')}
              </Button>
            </div>
          )}

          <div className="mt-10 space-y-3">
            <h4 className="text-[10px] font-black opacity-30 uppercase tracking-widest">
              {t('games.blindtest.game.previous_attempts', 'Tentatives précédentes')}
            </h4>
            {gameState.guesses.map((g: { title: string; is_correct: boolean }, i: number) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-navy-900 rounded-xl border border-gray-100 dark:border-white/5"
              >
                <span className="font-bold opacity-80">{g.title}</span>
                {g.is_correct ? (
                  <Check className="text-green-500 w-5 h-5" />
                ) : (
                  <X className="text-red-500 w-5 h-5" />
                )}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default BlindtestPage;
