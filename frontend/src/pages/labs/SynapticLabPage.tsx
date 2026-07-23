import React from 'react';
import { Loader2, Brain } from 'lucide-react';
import { useSynapticLab } from '../../hooks/useSynapticLab';
import { SynapticConfigPanel } from '../../components/labs/SynapticConfigPanel';
import { SynapticWeightMatrix } from '../../components/labs/SynapticWeightMatrix';
import { SynapticSimulationPanel } from '../../components/labs/SynapticSimulationPanel';
import { LabPage, LabHeader, LabPanel, LabGuide, LAB_BTN_GHOST } from './components/shared/LabKit';

const SynapticLabPage: React.FC = () => {
  const {
    state,
    isLoading,
    isError,
    refetch,
    tauPlus,
    setTauPlus,
    tauMinus,
    setTauMinus,
    mode,
    setMode,
    manualArchetype,
    setManualArchetype,
    intensityMult,
    setIntensityMult,
    features,
    setFeatures,
    selectedSpikes,
    lr,
    setLr,
    plasticityResult,
    configMutation,
    plasticityMutation,
    handleApplyConfig,
    handleSimulate,
    toggleSpike,
  } = useSynapticLab();

  if (isLoading) {
    return (
      <div className="flex min-h-screen w-full flex-col items-center justify-center bg-[#0B0C10] text-[#F4F1E8]">
        <Loader2 className="mb-4 h-12 w-12 animate-spin text-[#FDB913]" />
        <p className="text-sm font-black uppercase tracking-[0.2em] text-[#8F94A5]">
          Chargement de la matrice synaptique…
        </p>
      </div>
    );
  }

  if (isError || !state) {
    return (
      <div className="flex min-h-screen w-full flex-col items-center justify-center bg-[#0B0C10] px-6 text-center text-[#F4F1E8]">
        <Brain className="mb-6 h-16 w-16 text-[#E8442B]" aria-hidden="true" />
        <h2 className="font-manga mb-2 text-3xl font-black uppercase italic">
          Désynchronisation cognitive
        </h2>
        <p className="mb-6 text-sm leading-relaxed text-[#8F94A5]">
          Impossible de se connecter au lab de plasticité.
        </p>
        <button type="button" onClick={() => refetch()} className={LAB_BTN_GHOST}>
          Réessayer
        </button>
      </div>
    );
  }

  const concepts = state.concepts || [
    'Shonen',
    'Seinen',
    'Cyberpunk',
    'Mecha',
    'Fantasy',
    'Magic',
    'Ghibli',
    'Romance',
    'Comedy',
    'Drama',
  ];

  const currentW = plasticityResult?.weights || state.weights;
  const currentLogs = plasticityResult?.stdp_log || [];

  return (
    <LabPage wide>
      <LabHeader
        code="Protocole · Synapse"
        title="Plasticité"
        accent="synaptique"
        lede="Une matrice de poids relie les concepts de ton profil. Active des spikes et simule la règle de Hebb : les liens entre concepts co-activés se renforcent, et le drift d'archétype ajuste ton persona."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Configuration */}
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

        {/* Matrice de poids */}
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

        {/* Persona & journaux */}
        <div className="space-y-8 lg:col-span-3">
          <LabPanel title="Persona actif" corner={state.current_archetype.aura_type}>
            <div className="flex items-center gap-4">
              <span
                className="h-12 w-12 flex-none rounded-full border border-[#F4F1E8]/15"
                style={{ backgroundColor: state.current_archetype.accent }}
                aria-hidden
              />
              <div className="min-w-0">
                <p className="font-manga truncate text-xl font-black uppercase italic leading-tight text-[#F4F1E8]">
                  {state.current_archetype.id.replace('_', ' ')}
                </p>
                <p className="mt-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  Intensité {Math.round(state.current_archetype.intensity * 100)} %
                </p>
              </div>
            </div>
            <p className="mt-4 text-xs leading-relaxed text-[#8F94A5]">
              L'archétype dominant colore le thème visuel appliqué à ton profil ; son accent est la
              pastille ci-dessus.
            </p>
          </LabPanel>

          <SynapticSimulationPanel
            concepts={concepts}
            selectedSpikes={selectedSpikes}
            toggleSpike={toggleSpike}
            currentLogs={currentLogs}
          />
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Lis la matrice',
            body: "Chaque case montre la force du lien entre deux concepts (Shonen, Mecha, Romance…). Plus la case est lumineuse, plus l'association est forte.",
          },
          {
            title: 'Active des spikes',
            body: 'Sélectionne des concepts puis clique sur « Simuler » : les liens entre les concepts activés ensemble se renforcent, comme des neurones qui apprennent par association.',
          },
          {
            title: 'Ajuste le persona',
            body: "Les réglages de drift d'archétype (auto ou manuel, intensité, aura, accent, police) pilotent le thème visuel que l'application applique à ton profil.",
          },
        ]}
        note="Simulation de plasticité synaptique : règle de Hebb et STDP (Spike-Timing-Dependent Plasticity), avec constantes de temps τ+ / τ- à décroissance exponentielle et taux d'apprentissage η appliqués à la matrice de poids. Les paramètres et le drift d'archétype sont persistés côté serveur via l'endpoint singularity-lab ; la matrice affichée est l'état réel renvoyé par l'API."
      />
    </LabPage>
  );
};

export default SynapticLabPage;
