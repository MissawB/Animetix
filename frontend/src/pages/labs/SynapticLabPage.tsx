import React from 'react';
import { useTranslation } from 'react-i18next';
import { Activity, Loader2, Brain, Sparkles } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useSynapticLab } from '../../hooks/useSynapticLab';
import { SynapticConfigPanel } from '../../components/labs/SynapticConfigPanel';
import { SynapticWeightMatrix } from '../../components/labs/SynapticWeightMatrix';
import { SynapticSimulationPanel } from '../../components/labs/SynapticSimulationPanel';

const SynapticLabPage: React.FC = () => {
  const { t } = useTranslation();

  const {
    state,
    isLoading,
    isError,
    refetch,
    tauPlus, setTauPlus,
    tauMinus, setTauMinus,
    mode, setMode,
    manualArchetype, setManualArchetype,
    intensityMult, setIntensityMult,
    features, setFeatures,
    selectedSpikes,
    lr, setLr,
    plasticityResult,
    configMutation,
    plasticityMutation,
    handleApplyConfig,
    handleSimulate,
    toggleSpike
  } = useSynapticLab();

  if (isLoading) {
    return (
      <div className="min-h-screen w-full bg-[#0a0a12] flex flex-col items-center justify-center text-white">
        <Loader2 className="w-12 h-12 animate-spin text-red-500 mb-4" />
        <p className="text-sm font-black uppercase tracking-[0.2em] opacity-40">Loading Synaptic Matrix...</p>
      </div>
    );
  }

  if (isError || !state) {
    return (
      <div className="min-h-screen w-full bg-[#0a0a12] flex flex-col items-center justify-center text-white text-center">
        <Brain className="w-16 h-16 text-red-500 mb-6 animate-pulse" />
        <h2 className="text-3xl font-black italic manga-font uppercase mb-2">Desynchronisation Cognitive</h2>
        <p className="text-white/40 uppercase font-bold tracking-widest mb-6">Impossible de se connecter au lab de plasticité.</p>
        <Button onClick={() => refetch()} className="bg-red-600 hover:bg-red-500">Réessayer</Button>
      </div>
    );
  }

  const concepts = state.concepts || [
    'Shonen', 'Seinen', 'Cyberpunk', 'Mecha', 'Fantasy',
    'Magic', 'Ghibli', 'Romance', 'Comedy', 'Drama'
  ];

  const currentW = plasticityResult?.weights || state.weights;
  const currentLogs = plasticityResult?.stdp_log || [];

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pt-20 pb-16">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
          {/* Header */}
          <header className="mb-16 relative">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-red-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-red-400 mb-4">
                  <Activity className="w-3 h-3 animate-pulse" /> Dynamic Plasticity Dashboard
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                  {t('labs.plasticity.title', 'PLASTICITY').split(' ')[0]} <span className="text-red-500 text-glow">{t('labs.plasticity.title', 'LAB').split(' ')[1] || 'LAB'}</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  Configuration de la plasticité cognitive et ajustement du drift d'archétype.
              </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Configuration Column */}
              <div className="lg:col-span-4">
                  <SynapticConfigPanel
                    tauPlus={tauPlus}
                    setTauPlus={setTauPlus}
                    tauMinus={tauMinus}
                    setTauMinus={setTauMinus}
                    mode={mode}
                    setMode={setMode}
                    manualArchetype={manualArchetype}
                    setManualArchetype={setManualArchetype}
                    intensityMult={intensityMult}
                    setIntensityMult={setIntensityMult}
                    features={features}
                    setFeatures={setFeatures}
                    handleApplyConfig={handleApplyConfig}
                    isConfigPending={configMutation.isPending}
                  />
              </div>

              {/* Central Neural Matrix Core */}
              <div className="lg:col-span-5">
                  <SynapticWeightMatrix
                    concepts={concepts}
                    currentW={currentW}
                    lr={lr}
                    setLr={setLr}
                    handleSimulate={handleSimulate}
                    isSimulationPending={plasticityMutation.isPending}
                    selectedSpikes={selectedSpikes}
                  />
              </div>

              {/* Master State Profile & Logs */}
              <div className="lg:col-span-3 space-y-8">
                  {/* Dominant Archetype Aura Card */}
                  <Card padding="none" className="bg-black border-white/10 overflow-hidden rounded-[2.5rem] relative group shadow-2xl min-h-[220px]">
                      {/* Aura Ambient Blur */}
                      <div 
                          className="absolute inset-0 opacity-20 transition-opacity duration-700 group-hover:opacity-35"
                          style={{ 
                              background: `radial-gradient(circle at center, ${state.current_archetype.accent} 0%, transparent 70%)`,
                              filter: 'blur(30px)'
                          }} 
                      />
                      
                      <div className="relative z-10 p-8 text-center flex flex-col items-center justify-center">
                          <div className="w-24 h-24 mx-auto mb-4 relative">
                              <div 
                                  className="absolute inset-0 rounded-full animate-pulse opacity-40"
                                  style={{ boxShadow: `0 0 35px ${state.current_archetype.accent}` }}
                              />
                              <div className="w-full h-full bg-navy-950 border-2 border-white/15 rounded-full flex items-center justify-center relative overflow-hidden">
                                  <Brain className="w-10 h-10 text-white opacity-25" />
                                  <div 
                                      className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-red-600/10 to-transparent h-1/2 animate-scan"
                                  />
                              </div>
                          </div>

                          <Badge 
                              variant="primary" 
                              style={{ backgroundColor: state.current_archetype.accent }}
                              className="mb-3 text-[8px] font-black italic uppercase tracking-widest py-1 px-4 border-none text-white"
                          >
                              {state.current_archetype.id.replace('_', ' ')}
                          </Badge>
                          
                          <h2 className="text-xl font-black italic manga-font uppercase mb-1 tracking-tight">Active Persona</h2>
                          <p className="text-[8px] font-bold opacity-30 uppercase tracking-widest">
                              Aura: {state.current_archetype.aura_type} ({Math.round(state.current_archetype.intensity * 100)}%)
                          </p>
                      </div>
                  </Card>

                  {/* Trigger Grid & Logs */}
                  <SynapticSimulationPanel
                    concepts={concepts}
                    selectedSpikes={selectedSpikes}
                    toggleSpike={toggleSpike}
                    currentLogs={currentLogs}
                  />
              </div>
          </div>

          {/* Guide & Protocole */}
          <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card padding="lg" className="bg-black/40 border-red-500/20 shadow-[0_0_50px_rgba(239,68,68,0.1)] relative overflow-hidden group">
                  <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                      <Brain className="w-64 h-64 text-red-500" />
                  </div>
                  <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                      <Sparkles className="w-5 h-5 text-red-400" /> Guide de la Plasticité
                  </h4>
                  <div className="space-y-4 relative z-10">
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-red-400">La Matrice :</span> Chaque case de la grille montre la force du lien entre deux concepts (Shonen, Mecha, Romance...). Plus la case est lumineuse, plus l'association est forte.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-red-400">Les Spikes :</span> Sélectionnez des concepts puis cliquez sur "Simuler" : les liens entre les concepts activés ensemble se renforcent, comme des neurones qui apprennent par association.
                      </p>
                      <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                          <span className="text-red-400">Le Persona :</span> Les réglages de drift d'archétype (auto ou manuel, intensité, aura/accent/police) ajustent le thème visuel que l'application applique à votre profil.
                      </p>
                  </div>
              </Card>

              <div className="p-12 rounded-[4rem] bg-gradient-to-br from-red-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
                  <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-red-200/60">
                      Simulation de plasticité synaptique : règle de Hebb et STDP (Spike-Timing-Dependent Plasticity), avec constantes de temps τ+ / τ- à décroissance exponentielle et taux d'apprentissage η appliqués à la matrice de poids. <br />
                      Les paramètres et le drift d'archétype sont persistés côté serveur via l'endpoint singularity-lab ; la matrice affichée est l'état réel renvoyé par l'API.
                  </p>
              </div>
          </div>
        </div>
      </AnimatedPage>
    </div>
  );
};

export default SynapticLabPage;
