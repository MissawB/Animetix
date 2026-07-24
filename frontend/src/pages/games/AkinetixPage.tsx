import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Brain,
  History,
  Check,
  X,
  HelpCircle,
  Sparkles,
  Target,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';
import { useAkinetixStore } from '../../features/games/stores/akinetixStore';
import { Button } from '../../components/ui/Button';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { useTranslation } from 'react-i18next';
import { Badge } from '../../components/ui/Badge';

const AkinetixPage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, isLoading, error, loadGame, restartGame, submitAnswer, submitConfirmation } =
    useAkinetixStore();
  const location = useLocation();
  const navState = location.state as { mediaType?: string; difficulty?: string } | null;
  const mediaType = navState?.mediaType;
  const difficulty = navState?.difficulty;
  const [showActualTargetInput, setShowActualTargetInput] = useState(false);
  const [actualTarget, setActualTarget] = useState('');
  const historyScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Arrivé depuis le lobby avec un univers choisi → nouvelle partie dans cet
    // univers ; sinon on reprend/charge la partie courante.
    if (mediaType) {
      restartGame(mediaType, difficulty);
    } else {
      loadGame();
    }
  }, [mediaType, difficulty, restartGame, loadGame]);

  // Garde le journal défilé en bas, mais SANS bouger la page : on défile
  // uniquement le conteneur du journal (scrollIntoView faisait descendre toute
  // la page, masquant la question suivante).
  useEffect(() => {
    const el = historyScrollRef.current;
    if (el && typeof el.scrollTo === 'function') {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }, [gameState?.history]);

  if (isLoading)
    return (
      <div className="min-h-screen bg-[#0B0C10] flex justify-center items-center py-20 px-6">
        <div className="w-full max-w-4xl space-y-8">
          <CardSkeleton />
          <div className="grid grid-cols-3 gap-4">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    );

  if (error) {
    return (
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8] flex justify-center items-center py-20 px-6">
        <div className="text-center rounded-2xl border border-[#E8442B]/40 bg-[#0F1016] p-8 md:p-10 max-w-2xl w-full relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-[#E8442B] animate-pulse" />
          <AlertTriangle className="w-16 h-16 text-[#E8442B] mx-auto mb-6" />
          <h2 className="font-manga text-4xl font-black italic text-[#E8442B] mb-4 tracking-tighter uppercase">
            {t('games.akinetix.anomaly', 'Anomalie Détectée')}
          </h2>
          <p className="mb-10 text-[#8F94A5] font-bold leading-relaxed">{error}</p>
          <Button
            variant="danger"
            size="lg"
            onClick={() => restartGame()}
            className="uppercase tracking-widest font-black !bg-[#E8442B] hover:!bg-[#c93a24] text-[#F4F1E8]"
          >
            {t('games.akinetix.reset_core', 'Réinitialiser le Noyau')}
          </Button>
        </div>
      </div>
    );
  }

  if (!gameState) return null;

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-6xl mx-auto px-6 py-12 lg:py-20">
        <header className="mb-12 text-center">
          <div className="inline-flex items-center gap-3 mb-5">
            <span className="explore-stamp -rotate-2" aria-hidden>
              読
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              {t('games.akinetix.tagline', "L'IA peut-elle lire dans vos pensées ?")}
            </span>
          </div>
          <div className="inline-flex items-center justify-center mb-4">
            <Brain className="w-12 h-12 text-[#E8442B]" />
          </div>
          <h1 className="font-manga text-5xl md:text-7xl font-black italic mb-2 tracking-tighter uppercase text-[#F4F1E8]">
            Akinetix
          </h1>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: History */}
          <div className="lg:col-span-4 order-2 lg:order-1 hidden md:block">
            <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sticky top-24 max-h-[600px] flex flex-col">
              <h3 className="text-xs font-black uppercase text-[#8F94A5] mb-6 tracking-[0.2em] flex items-center gap-2 shrink-0">
                <History className="w-4 h-4" /> {t('games.akinetix.journal', "Journal d'Analyse")}
              </h3>

              <div
                ref={historyScrollRef}
                className="overflow-y-auto pr-2 custom-scrollbar flex-1 space-y-4"
              >
                {gameState.history.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-[#8F94A5]/40 py-20">
                    <Sparkles className="w-8 h-8 mb-4" />
                    <p className="text-[10px] font-black uppercase tracking-widest text-center">
                      {t('games.akinetix.not_started', "L'analyse n'a pas encore commencé")}
                    </p>
                  </div>
                ) : (
                  gameState.history.map((item: { q: string; a: string }, i: number) => (
                    <div
                      key={i}
                      className="bg-[#0B0C10] p-4 rounded-xl border border-[#F4F1E8]/5 animate-slide-up"
                    >
                      <p className="text-xs font-bold text-[#F4F1E8]/80 mb-2 leading-relaxed">
                        {item.q}
                      </p>
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-2 h-2 rounded-full ${
                            item.a === 'OUI'
                              ? 'bg-[#FDB913]'
                              : item.a === 'NON'
                                ? 'bg-[#E8442B]'
                                : 'bg-[#8F94A5]'
                          }`}
                        />
                        <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                          {item.a}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Center/Right Column: Main Game Area */}
          <div className="lg:col-span-8 order-1 lg:order-2 space-y-8">
            <div className="relative overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 md:p-10 min-h-[400px] flex flex-col justify-center">
              {/* Background Decorations */}
              <div className="absolute top-0 right-0 p-12 opacity-[0.04] pointer-events-none">
                <Target className="w-64 h-64 text-[#E8442B] spin-slow" />
              </div>

              <div className="relative z-10 flex flex-col items-center text-center">
                <Badge
                  variant="primary"
                  className="mb-6 !bg-[#E8442B]/15 !text-[#E8442B] !border-[#E8442B]/30"
                >
                  {t('games.akinetix.question_num', {
                    defaultValue: 'Question #{{num}}',
                    num: gameState.history.length + 1,
                  })}
                </Badge>

                {/* Barre de progression : confiance de l'IA (à quel point elle est
                  proche de deviner). */}
                {!showActualTargetInput && (
                  <div className="w-full max-w-md mx-auto mb-10">
                    <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-2">
                      <span className="flex items-center gap-1.5">
                        <Target className="w-3 h-3" />{' '}
                        {t('games.akinetix.ai_confidence', "Confiance de l'IA")}
                      </span>
                      <span className="text-[#FDB913]">
                        {Math.round((gameState.confidence ?? 0) * 100)}%
                      </span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-[#F4F1E8]/5 overflow-hidden border border-[#F4F1E8]/5">
                      <div
                        className="h-full rounded-full bg-[#FDB913] transition-all duration-700 ease-out"
                        style={{
                          width: `${Math.min(100, Math.round((gameState.confidence ?? 0) * 100))}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                <div className="text-3xl md:text-5xl mb-12 font-black text-[#F4F1E8] leading-tight">
                  {gameState.gameOver && !showActualTargetInput ? (
                    <div className="animate-fade-in">
                      <span className="block text-sm text-[#E8442B] uppercase tracking-widest mb-4">
                        {t('games.akinetix.ai_decided', "L'IA a tranché :")}
                      </span>
                      <span className="font-manga text-5xl md:text-7xl italic text-[#FDB913]">
                        {gameState.aiGuess}
                      </span>
                    </div>
                  ) : showActualTargetInput ? (
                    <span className="text-[#FDB913]">
                      {t('games.akinetix.who_really', 'À qui pensiez-vous réellement ?')}
                    </span>
                  ) : (
                    <span className="italic">{gameState.currentQuestion}</span>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="w-full max-w-2xl mx-auto">
                  {!gameState.gameOver ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4 md:gap-6">
                        <Button
                          variant="success"
                          size="lg"
                          onClick={() => submitAnswer('OUI')}
                          className="py-6 text-lg font-black uppercase tracking-widest !bg-[#FDB913] hover:!bg-[#e0a50f] !text-[#0B0C10] border-none transition-colors"
                        >
                          <Check className="w-6 h-6 mr-2" /> {t('common.yes')}
                        </Button>
                        <Button
                          variant="danger"
                          size="lg"
                          onClick={() => submitAnswer('NON')}
                          className="py-6 text-lg font-black uppercase tracking-widest !bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8] border-none transition-colors"
                        >
                          <X className="w-6 h-6 mr-2" /> {t('common.no')}
                        </Button>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <Button
                          variant="secondary"
                          onClick={() => submitAnswer('PROBABLEMENT')}
                          className="py-4 text-sm font-black uppercase tracking-wider !bg-[#FDB913]/10 !text-[#FDB913] hover:!bg-[#FDB913]/20 border border-[#FDB913]/30 transition-colors"
                        >
                          <ThumbsUp className="w-4 h-4 mr-2" />{' '}
                          {t('games.akinetix.probably', 'Probablement')}
                        </Button>
                        <Button
                          variant="secondary"
                          onClick={() => submitAnswer('PROBABLEMENT PAS')}
                          className="py-4 text-sm font-black uppercase tracking-wider !bg-[#E8442B]/10 !text-[#E8442B] hover:!bg-[#E8442B]/20 border border-[#E8442B]/30 transition-colors"
                        >
                          <ThumbsDown className="w-4 h-4 mr-2" />{' '}
                          {t('games.akinetix.probably_not', 'Probablement pas')}
                        </Button>
                        <Button
                          variant="secondary"
                          onClick={() => submitAnswer('JE NE SAIS PAS')}
                          className="py-4 text-sm font-black uppercase tracking-wider !bg-[#8F94A5]/10 !text-[#8F94A5] hover:!bg-[#8F94A5]/20 border border-[#8F94A5]/30 transition-colors"
                        >
                          <HelpCircle className="w-4 h-4 mr-2" />{' '}
                          {t('games.akinetix.dont_know', 'Je ne sais pas')}
                        </Button>
                      </div>
                    </div>
                  ) : showActualTargetInput ? (
                    <div className="flex flex-col gap-4 animate-fade-in">
                      <input
                        type="text"
                        value={actualTarget}
                        onChange={(e) => setActualTarget(e.target.value)}
                        className="w-full p-6 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/15 focus:border-[#FDB913] outline-none font-bold text-xl text-center text-[#F4F1E8] placeholder-[#8F94A5]/50 transition-colors"
                        placeholder={t(
                          'games.akinetix.target_placeholder',
                          'Nom exact du personnage...',
                        )}
                        aria-label={t('games.akinetix.target_aria', 'Nom exact du personnage')}
                        autoFocus
                      />
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                        <Button
                          variant="primary"
                          size="lg"
                          onClick={() => submitConfirmation(false, actualTarget)}
                          disabled={!actualTarget.trim()}
                          className="py-5 font-black uppercase tracking-widest !bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8]"
                        >
                          {t('games.akinetix.confirm_victory', 'CONFIRMER LA VICTOIRE')}
                        </Button>
                        <Button
                          variant="outline"
                          size="lg"
                          onClick={() => setShowActualTargetInput(false)}
                          className="py-5 font-black uppercase tracking-widest !border-[#F4F1E8]/15 hover:!border-[#FDB913] !text-[#F4F1E8]"
                        >
                          {t('common.cancel', 'Annuler')}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 animate-fade-in">
                      <Button
                        variant="primary"
                        size="lg"
                        onClick={() => submitConfirmation(true)}
                        className="py-6 !bg-[#FDB913] hover:!bg-[#e0a50f] !text-[#0B0C10] border-none font-black uppercase tracking-widest"
                      >
                        {t('games.akinetix.its_right', "C'EST BIEN ÇA !")}
                      </Button>
                      <Button
                        variant="outline"
                        size="lg"
                        onClick={() => setShowActualTargetInput(true)}
                        className="py-6 !border-[#E8442B]/50 !text-[#E8442B] hover:!bg-[#E8442B]/10 font-black uppercase tracking-widest"
                      >
                        {t('games.akinetix.ai_wrong', "NON, L'IA S'EST TROMPÉE")}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                variant="outline"
                onClick={() => restartGame()}
                className="text-xs font-black uppercase tracking-widest !border-[#F4F1E8]/10 !text-[#8F94A5] hover:!text-[#F4F1E8] hover:!border-[#FDB913]"
              >
                {t('games.akinetix.restart', 'Recommencer une partie')}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AkinetixPage;
