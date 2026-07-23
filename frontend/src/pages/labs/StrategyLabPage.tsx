import React, { useState } from 'react';
import { Target, RefreshCw, BarChart3, TrendingDown } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { motion, AnimatePresence } from 'framer-motion';
import Plot from '../../components/LazyPlot';
import type * as Plotly from 'plotly.js';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabStat,
  LabEmpty,
  LabGuide,
  LAB_LABEL,
  LAB_CTA,
} from './components/shared/LabKit';

interface CFRResult {
  history: Array<{
    iteration: number;
    avg_strategy: number[];
    regrets: number[];
  }>;
  questions: string[];
  final_strategy: number[];
}

const StrategyLabPage: React.FC = () => {
  const [iterations, setIterations] = useState(100);
  const [result, setResult] = useState<CFRResult | null>(null);

  const mutation = useMutation<CFRResult, Error, { iterations: number }>({
    mutationFn: (data: { iterations: number }) =>
      apiClient('/api/v1/cognition/cfr-strategy-lab/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const runSimulation = () => {
    mutation.mutate({ iterations });
  };

  const getStrategyPlotData = () => {
    if (!result) return [];
    const traces: Array<Partial<Plotly.Data>> = [];
    const iterationsArr = result.history.map((step) => step.iteration);

    result.questions.forEach((q: string, idx: number) => {
      traces.push({
        x: iterationsArr,
        y: result.history.map((step) => step.avg_strategy[idx]),
        name: q,
        type: 'scatter',
        mode: 'lines',
        line: { width: 3 },
      } as unknown as Partial<Plotly.Data>);
    });
    return traces;
  };

  const getRegretPlotData = () => {
    if (!result) return [];
    const traces: Array<Partial<Plotly.Data>> = [];
    const iterationsArr = result.history.map((step) => step.iteration);

    result.questions.forEach((q: string, idx: number) => {
      traces.push({
        x: iterationsArr,
        y: result.history.map((step) => step.regrets[idx]),
        name: q,
        type: 'scatter',
        mode: 'lines',
        fill: 'tozeroy',
      } as unknown as Partial<Plotly.Data>);
    });
    return traces;
  };

  return (
    <LabPage>
      <LabHeader
        code="Protocole · CFR"
        title="Stratégie"
        accent="de Nash"
        lede="L'algorithme Counterfactual Regret Minimization cherche la meilleure question à poser dans un jeu de devinettes. Itération après itération, il mesure le regret de ne pas avoir choisi autrement et fait converger sa stratégie vers un équilibre de Nash."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Paramètres */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title="Paramètres du solveur">
            <div className="space-y-8">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label htmlFor="iter-slider" className={LAB_LABEL}>
                    Itérations de convergence
                  </label>
                  <span className="text-sm font-black text-[#FDB913]">{iterations}</span>
                </div>
                <input
                  id="iter-slider"
                  aria-label="Itérations de convergence"
                  type="range"
                  min="50"
                  max="500"
                  step="50"
                  value={iterations}
                  onChange={(e) => setIterations(parseInt(e.target.value))}
                  className="h-1 w-full appearance-none rounded-full bg-[#F4F1E8]/10 accent-[#E8442B]"
                />
              </div>

              <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-5">
                <h4 className={`${LAB_LABEL} mb-3 block`}>Algorithme</h4>
                <div className="flex items-center gap-3">
                  <span className="rounded-full border border-[#E8442B]/40 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-[#E8442B]">
                    CFR+
                  </span>
                  <span className="rounded-full border border-[#FDB913]/40 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                    Regret matching
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={runSimulation}
                disabled={mutation.isPending}
                className={LAB_CTA}
              >
                {mutation.isPending ? (
                  <RefreshCw className="h-6 w-6 animate-spin" />
                ) : (
                  'Lancer la résolution'
                )}
              </button>
            </div>
          </LabPanel>

          <LabPanel title="Qu'est-ce que le CFR ?">
            <p className="text-sm leading-relaxed text-[#8F94A5]">
              Le Counterfactual Regret Minimization est l'algorithme de référence pour résoudre les
              jeux à information incomplète. Il permet à l'IA d'apprendre de ses erreurs passées en
              calculant le « regret » de ne pas avoir posé une meilleure question.
            </p>
          </LabPanel>
        </div>

        {/* Visualisation */}
        <div className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {!result && !mutation.isPending && (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full"
              >
                <LabEmpty
                  icon={<Target className="h-20 w-20" aria-hidden="true" />}
                  title="Solveur en veille"
                  hint="Règle le nombre d'itérations puis lance la résolution : les courbes de convergence de la stratégie s'afficheront ici."
                />
              </motion.div>
            )}

            {mutation.isPending && (
              <motion.div
                key="pending"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex h-full min-h-[420px] flex-col items-center justify-center gap-8"
              >
                <div className="h-24 w-24 animate-spin rounded-full border-4 border-[#E8442B]/20 border-t-[#E8442B]" />
                <p className="text-xs font-black uppercase tracking-[0.3em] text-[#8F94A5]">
                  Minimisation du regret en cours…
                </p>
              </motion.div>
            )}

            {result && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                className="space-y-8"
              >
                <LabPanel
                  title="Convergence de Nash"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <BarChart3 className="h-3.5 w-3.5" aria-hidden="true" /> probabilité d'action
                    </span>
                  }
                >
                  <Plot
                    data={getStrategyPlotData() as Plotly.Data[]}
                    layout={{
                      autosize: true,
                      height: 400,
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      margin: { l: 40, r: 20, b: 40, t: 10 },
                      showlegend: true,
                      legend: {
                        font: { color: '#64748b', size: 10 },
                        orientation: 'h',
                        y: -0.2,
                      },
                      xaxis: {
                        title: 'Itérations',
                        gridcolor: 'rgba(255,255,255,0.05)',
                        tickfont: { color: '#475569', size: 10 },
                      },
                      yaxis: {
                        title: 'Probabilité',
                        gridcolor: 'rgba(255,255,255,0.05)',
                        tickfont: { color: '#475569', size: 10 },
                        range: [0, 1],
                      },
                    }}
                    config={{ responsive: true, displayModeBar: false }}
                    style={{ width: '100%', height: '100%' }}
                  />
                </LabPanel>

                <LabPanel
                  title="Regret matching"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <TrendingDown className="h-3.5 w-3.5" aria-hidden="true" /> évolution du
                      regret
                    </span>
                  }
                >
                  <Plot
                    data={getRegretPlotData() as Plotly.Data[]}
                    layout={{
                      autosize: true,
                      height: 300,
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      margin: { l: 40, r: 20, b: 40, t: 10 },
                      showlegend: false,
                      xaxis: {
                        title: 'Itérations',
                        gridcolor: 'rgba(255,255,255,0.05)',
                        tickfont: { color: '#475569', size: 10 },
                      },
                      yaxis: {
                        title: 'Regret',
                        gridcolor: 'rgba(255,255,255,0.05)',
                        tickfont: { color: '#475569', size: 10 },
                      },
                    }}
                    config={{ responsive: true, displayModeBar: false }}
                    style={{ width: '100%', height: '100%' }}
                  />
                </LabPanel>

                <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                  <LabPanel title="Meilleur chemin décidé">
                    <div className="space-y-3">
                      {result.questions.map((q: string, i: number) => (
                        <div
                          key={i}
                          className="flex items-center justify-between rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4"
                        >
                          <span className="max-w-[200px] truncate text-xs font-bold text-[#F4F1E8]">
                            {q}
                          </span>
                          <span className="text-xs font-black italic text-[#FDB913]">
                            {(result.final_strategy[i] * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </LabPanel>

                  <div className="flex flex-col gap-6">
                    <LabStat
                      label="Solution optimale"
                      value={
                        result.questions[
                          result.final_strategy.indexOf(Math.max(...result.final_strategy))
                        ]
                      }
                      tone="shu"
                      className="flex-1"
                    />
                    <LabStat
                      label="Confiance"
                      value={`${(Math.max(...result.final_strategy) * 100).toFixed(2)}%`}
                      tone="gold"
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Règle le solveur',
            body: "L'IA cherche la meilleure question à poser dans un jeu de devinettes. Choisis le nombre d'itérations avec le curseur, puis lance la résolution.",
          },
          {
            title: 'Le regret guide',
            body: "À chaque itération, l'algorithme mesure le regret de ne pas avoir choisi une autre option, puis ajuste sa stratégie pour le réduire.",
          },
          {
            title: 'La convergence tranche',
            body: "Quand les courbes se stabilisent, la stratégie n'évolue plus : l'IA a trouvé le meilleur dosage de probabilités entre les questions possibles.",
          },
        ]}
        note="Simulation de Counterfactual Regret Minimization (CFR+ avec regret matching) exécutée côté serveur : la stratégie moyenne converge vers un équilibre de Nash approché. Les graphiques tracent la probabilité de chaque action et l'évolution du regret au fil des itérations — une visualisation pédagogique de théorie des jeux."
      />
    </LabPage>
  );
};

export default StrategyLabPage;
