import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Plot from '../../components/LazyPlot';
import type * as Plotly from 'plotly.js';
import {
  Activity,
  Zap,
  RefreshCw,
  TrendingUp,
  Layers,
  FlaskConical,
  Play,
  Settings,
  Brain,
  Sparkles,
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

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
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <header className="mb-16 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] font-black uppercase tracking-widest text-blue-500 mb-4">
            <FlaskConical className="w-3 h-3" /> {t('labs.liquid_nn.subtitle')}
          </div>
          <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4 text-glow">
            LIQUID <span className="text-blue-500">LAB</span>
          </h1>
          <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl mx-auto leading-relaxed">
            {t('labs.liquid_nn.title')}
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Control Panel */}
          <div className="lg:col-span-4 space-y-8">
            <Card padding="lg" className="bg-navy-950/50 border-white/5 shadow-2xl rounded-[3rem]">
              <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                <Settings className="w-4 h-4 text-blue-400" />{' '}
                {t('labs.liquid_nn.system_settings', 'Paramètres du Système')}
              </h3>

              <div className="space-y-6">
                <div>
                  <label
                    htmlFor="dt-slider"
                    className="text-[10px] font-black uppercase opacity-30 mb-2 block"
                  >
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
                    className="w-full h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                  <div className="flex justify-between mt-2 font-mono text-[10px] opacity-40">
                    <span>0.01s</span>
                    <span className="text-blue-500 font-bold">{dt}s</span>
                    <span>0.20s</span>
                  </div>
                </div>

                <div className="pt-4">
                  <Button
                    onClick={handleRandomSignal}
                    variant="outline"
                    className="w-full border-white/10 text-[10px] font-black uppercase tracking-widest py-4 rounded-2xl"
                  >
                    <Zap className="w-3 h-3 mr-2" />{' '}
                    {t('labs.liquid_nn.generate_signal', 'Générer Signal Aléatoire')}
                  </Button>
                </div>

                <Button
                  onClick={() => simulateMutation.mutate()}
                  disabled={simulateMutation.isPending}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white py-6 rounded-2xl font-black italic uppercase shadow-xl hover:scale-105 transition-all border-none"
                >
                  {simulateMutation.isPending ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : (
                    <Play className="w-5 h-5 mr-2" />
                  )}
                  {t('labs.liquid_nn.trigger_integration', "DÉCLENCHER L'INTÉGRATION")}
                </Button>
              </div>
            </Card>

            <Card padding="lg" className="bg-black border-white/5 shadow-2xl rounded-[2.5rem]">
              <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-500" /> Architecture LNN
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-white/5 rounded-2xl border border-white/5 text-center">
                  <p className="text-[8px] font-black opacity-30 uppercase mb-1">State Dim</p>
                  <p className="text-2xl font-black italic text-blue-500">4</p>
                </div>
                <div className="p-4 bg-white/5 rounded-2xl border border-white/5 text-center">
                  <p className="text-[8px] font-black opacity-30 uppercase mb-1">Input Dim</p>
                  <p className="text-2xl font-black italic text-emerald-500">2</p>
                </div>
              </div>
              <div className="mt-6 p-4 rounded-2xl bg-blue-500/5 border border-blue-500/10">
                <p className="text-[9px] font-bold leading-relaxed opacity-50 uppercase italic">
                  {t('labs.liquid_nn.system_resolves', 'Le système résout :')} <br />
                  <code className="text-blue-400 not-italic">dx/dt = -x/τ + f(Wx + Iu)(A - x)</code>
                </p>
              </div>
            </Card>
          </div>

          {/* Visualization Area */}
          <div className="lg:col-span-8 space-y-8">
            <Card
              padding="lg"
              className="bg-black border-white/5 overflow-hidden flex flex-col min-h-[500px]"
            >
              <header className="flex justify-between items-center mb-10">
                <h3 className="text-xl font-black italic manga-font uppercase flex items-center gap-3">
                  <TrendingUp className="w-5 h-5 text-blue-500" /> Continuous State Dynamics
                </h3>
                <Badge
                  variant="neutral"
                  className="bg-blue-500/10 text-blue-500 border-blue-500/20 text-[8px]"
                >
                  RK4 INTEGRATOR
                </Badge>
              </header>

              <div className="flex-grow relative">
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
                  <div className="h-full flex flex-col items-center justify-center opacity-10 text-center">
                    <Layers className="w-24 h-24 mb-6 animate-pulse" />
                    <p className="text-sm font-black uppercase tracking-[0.2em]">
                      {t(
                        'labs.liquid_nn.cluster_sync',
                        'Synchronisation du cluster neuromorphique...',
                      )}
                    </p>
                  </div>
                )}
              </div>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <h4 className="text-xs font-black uppercase opacity-40 mb-4 tracking-widest">
                  Inference Insights
                </h4>
                <p className="text-xs font-bold leading-relaxed opacity-60 italic">
                  {t(
                    'labs.liquid_nn.comparison_note',
                    "Contrairement aux réseaux classiques, les LNN traitent les données comme un flux continu, permettant une adaptation dynamique à la variabilité temporelle des signaux multimodaux d'Animetix.",
                  )}
                </p>
              </Card>
              <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <h4 className="text-xs font-black uppercase opacity-40 mb-4 tracking-widest">
                  ODE Solver
                </h4>
                <p className="text-xs font-bold leading-relaxed opacity-60 italic">
                  {t(
                    'labs.liquid_nn.solver_note',
                    "Le solveur utilise une intégration numérique de Runge-Kutta d'ordre 4 (RK4) pour garantir la stabilité des états neuronaux même avec des pas temporels (dt) élevés.",
                  )}
                </p>
              </Card>
            </div>
          </div>
        </div>

        {/* Guide & Protocole */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
          <Card
            padding="lg"
            className="bg-white dark:bg-black/40 border-blue-500/20 shadow-[0_0_50px_rgba(59,130,246,0.1)] relative overflow-hidden group"
          >
            <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
              <Brain className="w-64 h-64 text-blue-500" />
            </div>
            <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400" />{' '}
              {t('labs.liquid_nn.guide_title', 'Guide du Réseau Liquide')}
            </h4>
            <div className="space-y-4 relative z-10">
              <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                <span className="text-blue-600 dark:text-blue-400">
                  {t('labs.liquid_nn.guide_concept_title', 'Le Concept :')}
                </span>{' '}
                {t(
                  'labs.liquid_nn.guide_concept_desc',
                  'Contrairement à une IA classique qui traite l\'information par étapes figées, un réseau de neurones "liquide" évolue en continu dans le temps, comme de vrais neurones biologiques.',
                )}
              </p>
              <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                <span className="text-blue-600 dark:text-blue-400">
                  {t('labs.liquid_nn.guide_signal_title', 'Le Signal :')}
                </span>{' '}
                {t(
                  'labs.liquid_nn.guide_signal_desc',
                  "Générez un signal d'entrée aléatoire puis lancez l'intégration : chaque courbe du graphe montre comment l'activation d'un neurone réagit à ce signal au fil du temps.",
                )}
              </p>
              <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                <span className="text-blue-600 dark:text-blue-400">
                  {t('labs.liquid_nn.guide_step_title', 'Le Pas Temporel :')}
                </span>{' '}
                {t(
                  'labs.liquid_nn.guide_step_desc',
                  'Le curseur dt règle la finesse de la simulation. Un petit pas donne des courbes plus précises, un grand pas accélère le calcul au prix de la précision.',
                )}
              </p>
            </div>
          </Card>

          <div className="p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-black/5 dark:border-white/5 flex flex-col justify-center text-center">
            <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-blue-800/70 dark:text-blue-200/60">
              {t(
                'labs.liquid_nn.guide_footer_1',
                "Simulation d'un réseau de neurones liquide : l'état des 4 neurones suit l'équation différentielle dx/dt = -x/τ + f(Wx + Iu)(A - x), résolue par intégration numérique de Runge-Kutta d'ordre 4 (RK4).",
              )}{' '}
              <br />
              {t(
                'labs.liquid_nn.guide_footer_2',
                "Le graphe visualise la trajectoire d'états calculée côté serveur et renvoyée par l'endpoint liquid-nn.",
              )}
            </p>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default LiquidNeuralNetworkLabPage;
