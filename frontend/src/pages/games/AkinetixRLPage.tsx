import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import {
  Brain,
  Zap,
  History,
  Loader2,
  Sparkles,
  Check,
  Info,
  LayoutDashboard,
  Target,
  Cpu,
  TrendingUp,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { apiClient } from '../../utils/apiClient';

interface RLState {
  current_q: string;
  history: { q: string; a: string }[];
  game_over: boolean;
  ai_guess: string | null;
  pool_size: number;
  steps: number;
}

const AkinetixRLPage: React.FC = () => {
  const { t } = useTranslation();
  const [state, setState] = useState<RLState | null>(null);
  const [, setError] = useState<string | null>(null);
  const [showDashboard, setShowDashboard] = useState(() => {
    return !localStorage.getItem('akinetix_rl_onboarding');
  });

  const startMutation = useMutation<RLState, Error, string | undefined>({
    mutationFn: (mediaType = 'Anime') =>
      apiClient('/api/v1/game/akinetix-rl/start/', {
        method: 'POST',
        body: JSON.stringify({ media_type: mediaType }),
      }),
    onSuccess: (data) => {
      setState(data);
      setShowDashboard(false);
      setError(null);
    },
    onError: () => {
      setError(t('games.akinetix.rl.error_init', "Échec de l'initialisation du cerveau RL."));
    },
  });

  const answerMutation = useMutation<RLState, Error, string>({
    mutationFn: (answer: string) =>
      apiClient('/api/v1/game/akinetix-rl/answer/', {
        method: 'POST',
        body: JSON.stringify({ answer }),
      }),
    onSuccess: (data) => {
      setState(data);
      setError(null);
    },
    onError: () => {
      setError(
        t('games.akinetix.rl.error_connection', 'Perte de connexion avec le réseau neuronal.'),
      );
    },
  });

  const loading = startMutation.isPending || answerMutation.isPending;

  const startRLGame = useCallback(
    (mediaType = 'Anime') => {
      startMutation.mutate(mediaType);
    },
    [startMutation],
  );

  const submitAnswer = (answer: string) => {
    answerMutation.mutate(answer);
  };

  useEffect(() => {
    let isMounted = true;
    const hasSeenOnboarding = localStorage.getItem('akinetix_rl_onboarding');
    if (!hasSeenOnboarding) {
      localStorage.setItem('akinetix_rl_onboarding', 'true');
    } else if (!state && !loading && isMounted) {
      startRLGame();
    }
    return () => {
      isMounted = false;
    };
  }, [startRLGame, state, loading]);

  if (showDashboard) {
    return (
      <AnimatedPage>
        <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
          <div className="max-w-5xl mx-auto px-6 py-16">
            <header className="mb-16 text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#E8442B]/25 text-[#E8442B] text-[10px] font-black uppercase tracking-[0.3em] mb-4">
                <Cpu className="w-3 h-3" /> Reinforcement Learning Module
              </div>
              <h1 className="text-7xl font-black italic font-manga tracking-tighter uppercase mb-2 leading-none text-[#F4F1E8]">
                AKINETIX <span className="text-[#E8442B]">EXPERT</span>
              </h1>
              <p className="text-xl font-bold text-[#8F94A5] uppercase tracking-[0.3em] max-w-2xl mx-auto leading-relaxed">
                {t(
                  'games.akinetix.rl.intro',
                  "Vous n'allez pas seulement jouer, vous allez entraîner une intelligence artificielle.",
                )}
              </p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 text-center">
                <Target className="w-12 h-12 text-[#FDB913] mx-auto mb-6" />
                <h3 className="text-xl font-black italic font-manga uppercase mb-4 text-[#F4F1E8]">
                  {t('games.akinetix.rl.objective', 'Objectif')}
                </h3>
                <p className="text-[10px] font-bold text-[#8F94A5] uppercase leading-relaxed tracking-wider">
                  {t(
                    'games.akinetix.rl.objective_desc',
                    "L'IA doit deviner votre personnage en un minimum de questions en explorant l'espace latent du Lore.",
                  )}
                </p>
              </div>
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 text-center">
                <Brain className="w-12 h-12 text-[#E8442B] mx-auto mb-6" />
                <h3 className="text-xl font-black italic font-manga uppercase mb-4 text-[#F4F1E8]">
                  {t('games.akinetix.rl.training', 'Entraînement')}
                </h3>
                <p className="text-[10px] font-bold text-[#8F94A5] uppercase leading-relaxed tracking-wider">
                  {t(
                    'games.akinetix.rl.training_desc',
                    "Chaque réponse que vous donnez affine les poids neuronaux de l'agent RL (Reinforcement Learning).",
                  )}
                </p>
              </div>
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 text-center">
                <TrendingUp className="w-12 h-12 text-[#FDB913] mx-auto mb-6" />
                <h3 className="text-xl font-black italic font-manga uppercase mb-4 text-[#F4F1E8]">
                  {t('games.akinetix.rl.progression', 'Progression')}
                </h3>
                <p className="text-[10px] font-bold text-[#8F94A5] uppercase leading-relaxed tracking-wider">
                  {t(
                    'games.akinetix.rl.progression_desc',
                    "Plus vous jouez, plus l'agent devient efficace pour réduire l'entropie de recherche.",
                  )}
                </p>
              </div>
            </div>

            <div className="bg-[#0F1016] p-12 rounded-2xl border border-[#E8442B]/25 flex flex-col items-center">
              <h4 className="text-2xl font-black italic font-manga uppercase mb-8 text-[#F4F1E8]">
                {t('games.akinetix.rl.ready', "Prêt pour l'initiation ?")}
              </h4>
              <Button
                onClick={() => startRLGame()}
                variant="primary"
                className="!bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8] border-none py-8 px-20 text-2xl rounded-xl transition-colors"
              >
                {t('games.akinetix.rl.deploy', "DÉPLOYER L'AGENT")}
              </Button>
            </div>
          </div>
        </div>
      </AnimatedPage>
    );
  }

  if (!state && loading) {
    return (
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8] flex flex-col items-center justify-center">
        <Loader2 className="w-16 h-16 text-[#FDB913] animate-spin mb-4" />
        <span className="font-black italic font-manga animate-pulse">
          {t('games.akinetix.rl.syncing', 'SYNCHRONISATION DU CERVEAU RL...')}
        </span>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-5xl mx-auto px-6 py-16">
          <div className="flex items-center justify-between mb-12">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#E8442B] rounded-xl flex items-center justify-center">
                <Brain className="w-7 h-7 text-[#F4F1E8]" />
              </div>
              <div>
                <h1 className="text-4xl font-black italic font-manga tracking-tighter uppercase leading-none text-[#F4F1E8]">
                  AKINETIX <span className="text-[#E8442B]">EXPERT</span>
                </h1>
                <p className="text-[10px] font-bold text-[#8F94A5] uppercase tracking-[0.3em]">
                  Neural Engine Active
                </p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <button
                onClick={() => setShowDashboard(true)}
                className="p-3 bg-[#F4F1E8]/5 rounded-xl border border-[#F4F1E8]/10 text-[#8F94A5] hover:text-[#FDB913] transition-colors"
                title="Dashboard RL"
              >
                <LayoutDashboard className="w-5 h-5" />
              </button>
              <div className="text-right hidden sm:block">
                <div className="text-[10px] font-black text-[#8F94A5] uppercase mb-1 text-right">
                  {t('games.akinetix.rl.semantic_efficiency', 'Efficacité Sémantique')}
                </div>
                <div className="flex gap-1 justify-end">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`h-1.5 w-6 rounded-full ${i <= 5 - (state?.steps || 0) / 4 ? 'bg-[#FDB913]' : 'bg-[#F4F1E8]/10'}`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            {/* Main Interaction */}
            <div className="lg:col-span-8 space-y-8">
              <div className="bg-[#0F1016] border border-[#F4F1E8]/10 relative overflow-hidden rounded-2xl">
                <div className="absolute top-0 right-0 p-8 opacity-[0.04]">
                  <Zap className="w-40 h-40 text-[#E8442B]" />
                </div>

                <div className="p-12">
                  {!state?.game_over ? (
                    <>
                      <div className="mb-12">
                        <Badge
                          variant="primary"
                          className="!bg-[#E8442B]/15 !text-[#E8442B] !border-[#E8442B]/30 mb-6 font-black italic uppercase tracking-widest"
                        >
                          {t('games.akinetix.rl.inference_num', {
                            defaultValue: 'Inférence #{{num}}',
                            num: state?.steps || 0,
                          })}
                        </Badge>
                        <h2 className="text-4xl font-black italic font-manga leading-tight text-[#F4F1E8] uppercase tracking-tighter">
                          {state?.current_q ||
                            t(
                              'games.akinetix.rl.computing',
                              'Calcul de la trajectoire optimale...',
                            )}
                        </h2>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {[
                          { value: 'OUI', label: t('common.yes', 'OUI') },
                          { value: 'NON', label: t('common.no', 'NON') },
                          { value: 'PEUT-ÊTRE', label: t('games.akinetix.rl.maybe', 'PEUT-ÊTRE') },
                          {
                            value: 'PROBABLEMENT PAS',
                            label: t('games.akinetix.rl.probably_not', 'PROBABLEMENT PAS'),
                          },
                        ].map((ans) => (
                          <button
                            key={ans.value}
                            onClick={() => submitAnswer(ans.value)}
                            disabled={loading}
                            className="py-6 rounded-xl font-black italic uppercase transition-colors active:scale-95 bg-[#0B0C10] text-[#F4F1E8] border border-[#F4F1E8]/10 hover:border-[#FDB913]/50 hover:bg-[#FDB913]/5"
                          >
                            {ans.label}
                          </button>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8 animate-fade-in">
                      <Sparkles className="w-20 h-20 text-[#FDB913] mx-auto mb-8 animate-bounce" />
                      <h2 className="text-6xl font-black italic font-manga mb-6 uppercase tracking-tighter text-[#F4F1E8]">
                        {t('games.akinetix.rl.verdict', 'VERDICT IA')}
                      </h2>
                      <div className="bg-[#FDB913]/[0.06] border border-[#FDB913]/30 p-12 rounded-2xl mb-12">
                        <p className="text-sm font-black text-[#8F94A5] uppercase mb-4 tracking-[0.3em]">
                          {t(
                            'games.akinetix.rl.prediction',
                            "L'agent RL prédit avec 98.4% de certitude :",
                          )}
                        </p>
                        <h3 className="text-5xl font-black italic font-manga text-[#FDB913] uppercase tracking-tighter">
                          {state.ai_guess}
                        </h3>
                      </div>
                      <div className="flex flex-col sm:flex-row gap-6 w-full max-w-xl mx-auto">
                        <Button
                          onClick={() => startRLGame()}
                          variant="primary"
                          className="flex-1 py-8 text-xl rounded-xl border-none !bg-[#E8442B] hover:!bg-[#c93a24] !text-[#F4F1E8] font-black uppercase italic transition-colors"
                        >
                          REBOOT AGENT
                        </Button>
                        <Button
                          variant="outline"
                          className="p-8 !border-[#F4F1E8]/10 rounded-xl hover:!bg-[#FDB913]/10 hover:!text-[#FDB913] transition-colors"
                        >
                          <Check className="w-10 h-10" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* AI Reasoning Log */}
              <div className="bg-[#0F1016] rounded-2xl p-8 border border-[#F4F1E8]/10">
                <h4 className="text-[10px] font-black uppercase text-[#8F94A5] tracking-[0.4em] mb-6 flex items-center gap-2">
                  <Info className="w-3 h-3 text-[#FDB913]" /> Neural Network Debug Stream
                </h4>
                <div className="font-mono text-[10px] space-y-2 text-[#8F94A5]">
                  <p className="text-[#FDB913]">{`> POOL_SIZE: ${state?.pool_size || 0} candidates`}</p>
                  <p className="flex justify-between">
                    <span>{`> ENTROPY_MINIMIZATION:`}</span>{' '}
                    <span className="text-[#FDB913]">ACTIVE</span>
                  </p>
                  <p className="flex justify-between">
                    <span>{`> CURRENT_POLICY:`}</span>{' '}
                    <span className="text-[#FDB913]">GreedyInformationGain</span>
                  </p>
                  <p className="flex justify-between">
                    <span>{`> INFERENCE_STATUS:`}</span>{' '}
                    <span className="text-[#E8442B]">OPTIMIZING_NODE_{state?.steps || 0}</span>
                  </p>
                </div>
              </div>
            </div>

            {/* Sidebar History */}
            <div className="lg:col-span-4 flex flex-col">
              <div className="bg-[#0F1016] rounded-2xl p-8 border border-[#F4F1E8]/10 flex-grow">
                <h3 className="text-xs font-black uppercase text-[#8F94A5] mb-8 tracking-widest flex items-center gap-2">
                  <History className="w-4 h-4 text-[#FDB913]" /> Memory Trace
                </h3>
                <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 no-scrollbar">
                  {state?.history.map((h, i) => (
                    <div
                      key={i}
                      className="p-5 bg-[#0B0C10] rounded-xl border border-[#F4F1E8]/5 hover:border-[#F4F1E8]/10 transition-colors animate-fade-in group"
                    >
                      <p className="text-[9px] font-black text-[#8F94A5] uppercase mb-2 tracking-widest group-hover:text-[#FDB913] transition-colors">
                        Inf #{i + 1}
                      </p>
                      <p className="text-xs font-bold text-[#8F94A5] mb-2 leading-relaxed uppercase italic">
                        "{h.q}"
                      </p>
                      <div className="flex justify-end">
                        <Badge
                          variant="neutral"
                          className="!bg-[#F4F1E8]/5 !border-[#F4F1E8]/10 !text-[#F4F1E8] font-black italic"
                        >
                          {h.a}
                        </Badge>
                      </div>
                    </div>
                  ))}
                  {!state?.history.length && (
                    <div className="text-center py-32 text-[#8F94A5]/30 flex flex-col items-center gap-4">
                      <Zap className="w-12 h-12" />
                      <p className="text-[10px] font-black uppercase tracking-[0.3em]">
                        No memory found
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AkinetixRLPage;
