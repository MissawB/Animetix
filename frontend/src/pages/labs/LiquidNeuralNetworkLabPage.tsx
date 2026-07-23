import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Plot from '../../components/LazyPlot';
import type * as Plotly from 'plotly.js';
import { Activity, Zap, RefreshCw, Layers, Play } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabStat,
  LabGuide,
  LAB_LABEL,
  LAB_CTA,
  LAB_BTN_GHOST,
} from './components/shared/LabKit';

interface LNNResult {
  state_history: number[][];
  state_dimension: number;
}

const LiquidNeuralNetworkLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [signal, setSignal] = useState<number[][]>([
    [0.5, 0.2],
    [0.8, 0.4],
    [0.3, 0.9],
    [0.6, 0.1],
    [0.9, 0.7],
  ]);
  const [dt, setDt] = useState(0.05);
  const [simulationResult, setSimulationResult] = useState<LNNResult | null>(null);

  const simulateMutation = useMutation<LNNResult, Error>({
    mutationFn: async () => {
      return apiClient('/api/v1/labs/liquid-nn/', {
        method: 'POST',
        body: JSON.stringify({ signal, dt }),
        headers: { 'Content-Type': 'application/json' },
      });
    },
    onSuccess: (data) => {
      setSimulationResult(data);
    },
  });

  useEffect(() => {
    // Auto-simulate on mount
    simulateMutation.mutate();
  }, [simulateMutation]);

  const handleRandomSignal = () => {
    const newSignal = Array.from({ length: 20 }, () => [Math.random(), Math.random()]);
    setSignal(newSignal);
  };

  const getPlotData = () => {
    if (!simulationResult) return [];
    const { state_history, state_dimension } = simulationResult;

    const traces: Array<Partial<Plotly.Data>> = [];
    for (let i = 0; i < state_dimension; i++) {
      traces.push({
        x: state_history.map((_, idx: number) => idx * dt),
        y: state_history.map((step: number[]) => step[i]),
        name: t('labs.liquid_nn.neuron_label', { num: i + 1, defaultValue: 'Neurone {{num}}' }),
        type: 'scatter',
        mode: 'lines',
        line: { width: 2, shape: 'spline' },
      } as unknown as Partial<Plotly.Data>);
    }
    return traces;
  };

  return (
    <LabPage>
      <LabHeader
        code="Protocole · LNN"
        title="Neurones"
        accent="liquides"
        lede="Un réseau de neurones à temps continu résout ses états par équation différentielle. Règle le pas temporel, injecte un signal aléatoire et observe les activations onduler au fil de l'intégration."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Paramètres */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title={t('labs.liquid_nn.system_settings', 'Paramètres du Système')}>
            <div className="space-y-6">
              <div>
                <label htmlFor="dt-slider" className={`${LAB_LABEL} mb-2 block`}>
                  {t('labs.liquid_nn.time_step', 'Pas temporel (dt)')}
                </label>
                <input
                  id="dt-slider"
                  aria-label={t('labs.liquid_nn.time_step', 'Pas temporel (dt)')}
                  type="range"
                  min="0.01"
                  max="0.2"
                  step="0.01"
                  value={dt}
                  onChange={(e) => setDt(parseFloat(e.target.value))}
                  className="h-1 w-full cursor-pointer appearance-none rounded-full bg-[#F4F1E8]/10 accent-[#E8442B]"
                />
                <div className="mt-2 flex justify-between font-mono text-[10px] text-[#8F94A5]">
                  <span>0.01s</span>
                  <span className="font-bold text-[#FDB913]">{dt}s</span>
                  <span>0.20s</span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleRandomSignal}
                className={`${LAB_BTN_GHOST} w-full justify-center`}
              >
                <Zap className="h-3.5 w-3.5" aria-hidden="true" />{' '}
                {t('labs.liquid_nn.generate_signal', 'Générer Signal Aléatoire')}
              </button>

              <button
                type="button"
                onClick={() => simulateMutation.mutate()}
                disabled={simulateMutation.isPending}
                className={LAB_CTA}
              >
                {simulateMutation.isPending ? (
                  <RefreshCw className="h-5 w-5 animate-spin" />
                ) : (
                  <Play className="h-5 w-5" aria-hidden="true" />
                )}
                {t('labs.liquid_nn.trigger_integration', "DÉCLENCHER L'INTÉGRATION")}
              </button>
            </div>
          </LabPanel>

          <LabPanel title="Architecture LNN">
            <div className="grid grid-cols-2 gap-4">
              <LabStat label="Dimension d'état" value="4" tone="gold" />
              <LabStat label="Dimension d'entrée" value="2" />
            </div>
            <div className="mt-6 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
              <p className="text-xs leading-relaxed text-[#8F94A5]">
                {t('labs.liquid_nn.system_resolves', 'Le système résout :')} <br />
                <code className="font-mono text-[#FDB913]">dx/dt = -x/τ + f(Wx + Iu)(A - x)</code>
              </p>
            </div>
          </LabPanel>
        </div>

        {/* Visualisation */}
        <div className="space-y-8 lg:col-span-8">
          <LabPanel
            title="Dynamique des états"
            corner={
              <span className="flex items-center gap-1.5">
                <Activity className="h-3.5 w-3.5" aria-hidden="true" /> intégrateur RK4
              </span>
            }
            className="flex min-h-[500px] flex-col"
          >
            <div className="relative flex-grow">
              {simulationResult ? (
                <Plot
                  data={getPlotData() as Plotly.Data[]}
                  layout={{
                    autosize: true,
                    height: 400,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    margin: { l: 40, r: 20, b: 40, t: 10 },
                    showlegend: true,
                    legend: { font: { color: '#64748b', size: 10 }, orientation: 'h', y: -0.2 },
                    xaxis: {
                      title: t('labs.liquid_nn.time_label', 'Temps (s)'),
                      gridcolor: 'rgba(255,255,255,0.05)',
                      tickfont: { color: '#475569', size: 10 },
                      showgrid: true,
                    },
                    yaxis: {
                      title: t('labs.liquid_nn.activation_label', 'Activation'),
                      gridcolor: 'rgba(255,255,255,0.05)',
                      tickfont: { color: '#475569', size: 10 },
                      showgrid: true,
                    },
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  style={{ width: '100%' }}
                />
              ) : (
                <div className="flex h-full flex-col items-center justify-center py-16 text-center">
                  <Layers
                    className="mb-6 h-20 w-20 animate-pulse text-[#8F94A5]/25"
                    aria-hidden="true"
                  />
                  <p className="text-xs font-black uppercase tracking-[0.2em] text-[#8F94A5]">
                    {t(
                      'labs.liquid_nn.cluster_sync',
                      'Synchronisation du cluster neuromorphique...',
                    )}
                  </p>
                </div>
              )}
            </div>
          </LabPanel>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            <LabPanel title="Flux continu">
              <p className="text-sm leading-relaxed text-[#8F94A5]">
                {t(
                  'labs.liquid_nn.comparison_note',
                  "Contrairement aux réseaux classiques, les LNN traitent les données comme un flux continu, permettant une adaptation dynamique à la variabilité temporelle des signaux multimodaux d'Animetix.",
                )}
              </p>
            </LabPanel>
            <LabPanel title="Solveur ODE">
              <p className="text-sm leading-relaxed text-[#8F94A5]">
                {t(
                  'labs.liquid_nn.solver_note',
                  "Le solveur utilise une intégration numérique de Runge-Kutta d'ordre 4 (RK4) pour garantir la stabilité des états neuronaux même avec des pas temporels (dt) élevés.",
                )}
              </p>
            </LabPanel>
          </div>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Le concept',
            body: t(
              'labs.liquid_nn.guide_concept_desc',
              'Contrairement à une IA classique qui traite l\'information par étapes figées, un réseau de neurones "liquide" évolue en continu dans le temps, comme de vrais neurones biologiques.',
            ),
          },
          {
            title: 'Le signal',
            body: t(
              'labs.liquid_nn.guide_signal_desc',
              "Générez un signal d'entrée aléatoire puis lancez l'intégration : chaque courbe du graphe montre comment l'activation d'un neurone réagit à ce signal au fil du temps.",
            ),
          },
          {
            title: 'Le pas temporel',
            body: t(
              'labs.liquid_nn.guide_step_desc',
              'Le curseur dt règle la finesse de la simulation. Un petit pas donne des courbes plus précises, un grand pas accélère le calcul au prix de la précision.',
            ),
          },
        ]}
        note={`${t(
          'labs.liquid_nn.guide_footer_1',
          "Simulation d'un réseau de neurones liquide : l'état des 4 neurones suit l'équation différentielle dx/dt = -x/τ + f(Wx + Iu)(A - x), résolue par intégration numérique de Runge-Kutta d'ordre 4 (RK4).",
        )} ${t(
          'labs.liquid_nn.guide_footer_2',
          "Le graphe visualise la trajectoire d'états calculée côté serveur et renvoyée par l'endpoint liquid-nn.",
        )}`}
      />
    </LabPage>
  );
};

export default LiquidNeuralNetworkLabPage;
