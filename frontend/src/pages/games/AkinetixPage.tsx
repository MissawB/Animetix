import React, { useState, useEffect, useRef } from 'react';
import { Brain, History, Check, X, HelpCircle, Sparkles, Target, AlertTriangle } from 'lucide-react';
import { useAkinetixStore } from '../../features/games/stores/akinetixStore';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { useTranslation } from 'react-i18next';
import { Badge } from '../../components/ui/Badge';

const AkinetixPage: React.FC = () => {
  const { t } = useTranslation();
  const { gameState, isLoading, error, loadGame, restartGame, submitAnswer, submitConfirmation } = useAkinetixStore();
  const [showActualTargetInput, setShowActualTargetInput] = useState(false);
  const [actualTarget, setActualTarget] = useState('');
  const historyScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadGame();
  }, [loadGame]);

  // Garde le journal défilé en bas, mais SANS bouger la page : on défile
  // uniquement le conteneur du journal (scrollIntoView faisait descendre toute
  // la page, masquant la question suivante).
  useEffect(() => {
    const el = historyScrollRef.current;
    if (el && typeof el.scrollTo === 'function') {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }, [gameState?.history]);

  if (isLoading) return (
    <div className="flex justify-center items-center py-20 px-6 max-w-4xl mx-auto">
      <div className="w-full space-y-8">
        <CardSkeleton />
        <div className="grid grid-cols-3 gap-4"><CardSkeleton /><CardSkeleton /><CardSkeleton /></div>
      </div>
    </div>
  );
  
  if (error) {
    return (
        <div className="flex justify-center items-center min-h-[70vh] py-20 px-6">
          <Card padding="lg" className="text-center border-red-500/50 bg-red-500/5 max-w-2xl w-full relative overflow-hidden">
             <div className="absolute top-0 left-0 w-full h-1 bg-red-500 animate-pulse" />
             <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-6 opacity-80" />
             <h2 className="text-4xl font-black text-red-500 mb-4 tracking-tighter uppercase">Anomalie Détectée</h2>
             <p className="mb-10 text-white/60 font-bold leading-relaxed">{error}</p>
             <Button variant="danger" size="lg" onClick={restartGame} className="uppercase tracking-widest font-black">
               Réinitialiser le Noyau
             </Button>
          </Card>
        </div>
    );
  }

  if (!gameState) return null;

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 lg:py-20">
      
      <header className="mb-12 text-center">
        <div className="inline-flex items-center justify-center p-4 bg-blue-500/10 rounded-full mb-6 relative">
          <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full animate-pulse" />
          <Brain className="w-12 h-12 text-blue-500 relative z-10" />
        </div>
        <h1 className="text-5xl md:text-7xl font-black italic manga-font mb-4 tracking-tighter uppercase text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
          Akinetix
        </h1>
        <p className="text-white/50 font-bold uppercase tracking-[0.2em] text-sm md:text-base">
          L'IA peut-elle lire dans vos pensées ?
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: History */}
        <div className="lg:col-span-4 order-2 lg:order-1 hidden md:block">
          <Card padding="md" className="bg-[#0a0a0a] border-white/5 sticky top-24 max-h-[600px] flex flex-col">
            <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-[0.2em] flex items-center gap-2 text-white shrink-0">
                <History className="w-4 h-4" /> Journal d'Analyse
            </h3>
            
            <div ref={historyScrollRef} className="overflow-y-auto pr-2 custom-scrollbar flex-1 space-y-4">
              {gameState.history.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center opacity-20 py-20">
                  <Sparkles className="w-8 h-8 mb-4" />
                  <p className="text-[10px] font-black uppercase tracking-widest text-center">L'analyse n'a pas encore commencé</p>
                </div>
              ) : (
                gameState.history.map((item: { q: string; a: string }, i: number) => (
                  <div key={i} className="bg-[#121212] p-4 rounded-2xl border border-white/5 animate-slide-up">
                    <p className="text-xs font-bold text-white/80 mb-2 leading-relaxed">{item.q}</p>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        item.a === 'OUI' ? 'bg-green-500' : 
                        item.a === 'NON' ? 'bg-red-500' : 'bg-yellow-500'
                      }`} />
                      <span className="text-[10px] font-black uppercase tracking-widest text-white/50">{item.a}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* Center/Right Column: Main Game Area */}
        <div className="lg:col-span-8 order-1 lg:order-2 space-y-8">
          
          <Card padding="lg" className="relative overflow-hidden bg-gradient-to-b from-[#1a1a2e] to-[#0a0a14] border-blue-500/20 shadow-2xl shadow-blue-900/20 min-h-[400px] flex flex-col justify-center">
            
            {/* Background Decorations */}
            <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
                <Target className="w-64 h-64 text-blue-500 spin-slow" />
            </div>
            <div className="absolute inset-0 bg-[url('/static/img/noise.png')] opacity-10 mix-blend-overlay pointer-events-none"></div>

            <div className="relative z-10 flex flex-col items-center text-center">
              
              <Badge variant="primary" className="mb-8 bg-blue-500/20 text-blue-400 border-blue-500/30 backdrop-blur-md">
                Question #{gameState.history.length + 1}
              </Badge>

              <div className="text-3xl md:text-5xl mb-12 font-black text-white leading-tight drop-shadow-lg">
                {gameState.gameOver && !showActualTargetInput ? (
                  <div className="animate-fade-in">
                    <span className="block text-sm text-blue-400 uppercase tracking-widest mb-4">L'IA a tranché :</span>
                    <span className="text-5xl md:text-7xl text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                      {gameState.aiGuess}
                    </span>
                  </div>
                ) : showActualTargetInput ? (
                  <span className="text-yellow-400">À qui pensiez-vous réellement ?</span>
                ) : (
                  <span className="italic">{gameState.currentQuestion}</span>
                )}
              </div>

              {/* Action Buttons */}
              <div className="w-full max-w-2xl mx-auto">
                {!gameState.gameOver ? (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-6">
                    <Button 
                      variant="success" 
                      size="lg" 
                      onClick={() => submitAnswer('OUI')}
                      className="py-6 text-lg font-black uppercase tracking-widest bg-green-500 hover:bg-green-600 border-none shadow-[0_0_20px_rgba(34,197,94,0.3)] hover:shadow-[0_0_30px_rgba(34,197,94,0.5)] transition-all"
                    >
                      <Check className="w-6 h-6 mr-2" /> {t('common.yes')}
                    </Button>
                    <Button 
                      variant="danger" 
                      size="lg" 
                      onClick={() => submitAnswer('NON')}
                      className="py-6 text-lg font-black uppercase tracking-widest bg-red-500 hover:bg-red-600 border-none shadow-[0_0_20px_rgba(239,68,68,0.3)] hover:shadow-[0_0_30px_rgba(239,68,68,0.5)] transition-all"
                    >
                      <X className="w-6 h-6 mr-2" /> {t('common.no')}
                    </Button>
                    <Button 
                      variant="secondary" 
                      size="lg" 
                      onClick={() => submitAnswer('PEUT-ÊTRE')}
                      className="py-6 text-lg font-black uppercase tracking-widest bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20 border border-yellow-500/30 transition-all"
                    >
                      <HelpCircle className="w-6 h-6 mr-2" /> PEUT-ÊTRE
                    </Button>
                  </div>
                ) : showActualTargetInput ? (
                  <div className="flex flex-col gap-4 animate-fade-in">
                    <input
                      type="text"
                      value={actualTarget}
                      onChange={(e) => setActualTarget(e.target.value)}
                      className="w-full p-6 rounded-2xl bg-black/50 border-2 border-white/10 focus:border-yellow-400 outline-none font-bold text-xl text-center text-white placeholder-white/20 backdrop-blur-md transition-all"
                      placeholder="Nom exact du personnage..."
                      aria-label="Nom exact du personnage"
                      autoFocus
                    />
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                      <Button 
                        variant="primary" 
                        size="lg" 
                        onClick={() => submitConfirmation(false, actualTarget)}
                        disabled={!actualTarget.trim()}
                        className="py-5 font-black uppercase tracking-widest"
                      >
                        CONFIRMER LA VICTOIRE
                      </Button>
                      <Button 
                        variant="outline" 
                        size="lg" 
                        onClick={() => setShowActualTargetInput(false)}
                        className="py-5 font-black uppercase tracking-widest border-white/20 hover:bg-white/10 text-white"
                      >
                        Annuler
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 animate-fade-in">
                    <Button 
                      variant="primary" 
                      size="lg" 
                      onClick={() => submitConfirmation(true)}
                      className="py-6 bg-blue-600 hover:bg-blue-700 border-none font-black uppercase tracking-widest shadow-[0_0_30px_rgba(37,99,235,0.4)]"
                    >
                      C'EST BIEN ÇA !
                    </Button>
                    <Button 
                      variant="outline" 
                      size="lg" 
                      onClick={() => setShowActualTargetInput(true)}
                      className="py-6 border-2 border-red-500/50 text-red-400 hover:bg-red-500/10 font-black uppercase tracking-widest"
                    >
                      NON, L'IA S'EST TROMPÉE
                    </Button>
                  </div>
                )}
              </div>
              
            </div>
          </Card>
          
          <div className="flex justify-end">
            <Button 
                variant="outline" 
                onClick={restartGame}
                className="text-xs font-black uppercase tracking-widest border-white/10 text-white/50 hover:text-white hover:bg-white/5"
            >
                Recommencer une partie
            </Button>
          </div>

        </div>
      </div>
    </div>
  );
};

export default AkinetixPage;


