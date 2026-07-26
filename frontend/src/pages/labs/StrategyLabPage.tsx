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
        code="Le meilleur coup"
        title="Stratégie"
        accent="gagnante"
        lede="Comme à Akinator, l'IA cherche la meilleure question à poser pour deviner le plus vite possible. Elle rejoue des milliers de parties contre elle-même : à chaque essai, elle retient ce qu'elle « regrette » de ne pas avoir demandé, jusqu'à trouver le meilleur dosage de questions."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Paramètres */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title="Réglages">
            <div className="space-y-8">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label htmlFor="iter-slider" className={LAB_LABEL}>
                    Nombre de parties d'entraînement
                  </label>
                  <span className="text-sm font-black text-[#FDB913]">{iterations}</span>
                </div>
                <input
                  id="iter-slider"
                  aria-label="Nombre de parties d'entraînement"
                  type="range"
                  min="50"
                  max="500"
                  step="50"
                  value={iterations}
                  onChange={(e) => setIterations(parseInt(e.target.value))}
                  className="h-1 w-full appearance-none rounded-full bg-[#F4F1E8]/10 accent-[#E8442B]"
                />
                <p className="text-[11px] leading-relaxed text-[#8F94A5]/70">
                  Plus l'IA s'entraîne, plus sa stratégie se précise.
                </p>
              </div>

              <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-5">
                <h4 className={`${LAB_LABEL} mb-3 block`}>Sous le capot</h4>
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
                  "Lancer l'entraînement"
                )}
              </button>
            </div>
          </LabPanel>

          <LabPanel title="Comment ça marche ?">
            <p className="text-sm leading-relaxed text-[#8F94A5]">
              L'IA joue un jeu de devinettes contre elle-même, encore et encore. Après chaque
              partie, elle se demande : « quelle question aurait mieux marché ? » — c'est son «
              regret ». En réduisant ce regret à chaque fois, elle finit par savoir quelles
              questions poser, et à quelle fréquence, pour gagner le plus souvent.
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
                  title="Prêt à s'entraîner"
                  hint="Choisis le nombre de parties d'entraînement puis lance-le : les courbes montrant comment l'IA affine sa stratégie s'afficheront ici."
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
                  Entraînement en cours…
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
                  title="Quelle question l'IA choisit"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <BarChart3 className="h-3.5 w-3.5" aria-hidden="true" /> chances de la poser
                    </span>
                  }
                >
                  <p className="mb-4 text-xs leading-relaxed text-[#8F94A5]">
                    Chaque courbe est une question. Sa hauteur = la probabilité que l'IA la pose. Au
                    fil de l'entraînement, les courbes se stabilisent : l'IA a trouvé son dosage.
                  </p>
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
                        font: { color: '#8F94A5', size: 10 },
                        orientation: 'h',
                        y: -0.2,
                      },
                      hoverlabel: {
                        bgcolor: '#0F1016',
                        bordercolor: 'rgba(244,241,232,0.15)',
                        font: { color: '#F4F1E8', size: 12 },
                      },
                      xaxis: {
                        title: "Parties d'entraînement",
                        gridcolor: 'rgba(255,255,255,0.05)',
                        tickfont: { color: '#8F94A5', size: 10 },
                      },
                      yaxis: {
                        title: 'Chances de la poser',
                        tickformat: '.0%',
                        gridcolor: 'rgba(255,255,255,0.05)',
                        tickfont: { color: '#8F94A5', size: 10 },
                        range: [0, 1],
                      },
                    }}
                    config={{ responsive: true, displayModeBar: false }}
                    style={{ width: '100%', height: '100%' }}
                  />
                </LabPanel>

                <LabPanel
                  title="Ses regrets diminuent"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <TrendingDown className="h-3.5 w-3.5" aria-hidden="true" /> moins d'erreurs
                    </span>
                  }
                >
                  <p className="mb-4 text-xs leading-relaxed text-[#8F94A5]">
                    Le « regret » mesure à quel point l'IA aurait pu mieux jouer. Plus il descend,
                    plus sa stratégie est bonne.
                  </p>
                  <Plot
                    data={getRegretPlotData() as Plotly.Data[]}
                    layout={{
                      autosize: true,
                      height: 300,
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      margin: { l: 40, r: 20, b: 40, t: 10 },
                      showlegend: false,
                      hoverlabel: {
                        bgcolor: '#0F1016',
                        bordercolor: 'rgba(244,241,232,0.15)',
                        font: { color: '#F4F1E8', size: 12 },
                      },
                      xaxis: {
                        title: "Parties d'entraînement",
                        gridcolor: 'rgba(255,255,255,0.05)',
                        tickfont: { color: '#8F94A5', size: 10 },
                      },
                      yaxis: {
                        title: 'Regret (erreur)',
                        gridcolor: 'rgba(255,255,255,0.05)',
                        tickfont: { color: '#8F94A5', size: 10 },
                      },
                    }}
                    config={{ responsive: true, displayModeBar: false }}
                    style={{ width: '100%', height: '100%' }}
                  />
                </LabPanel>

                <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                  <LabPanel title="Les questions retenues">
                    <p className="mb-4 text-xs leading-relaxed text-[#8F94A5]">
                      À quelle fréquence l'IA choisit de poser chaque question.
                    </p>
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
                      label="Meilleure question"
                      value={
                        result.questions[
                          result.final_strategy.indexOf(Math.max(...result.final_strategy))
                        ]
                      }
                      tone="shu"
                      className="flex-1"
                    />
                    <LabStat
                      label="Fréquence de choix"
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
            title: "Choisis l'entraînement",
            body: "L'IA cherche la meilleure question à poser dans un jeu de devinettes (façon Akinator). Règle le nombre de parties d'entraînement, puis lance-le.",
          },
          {
            title: 'Le regret la guide',
            body: "Après chaque partie, l'IA regarde quelle question aurait mieux marché — son « regret » — et ajuste sa stratégie pour se tromper moins la fois suivante.",
          },
          {
            title: 'La stratégie se fige',
            body: "Quand les courbes se stabilisent, la stratégie n'évolue plus : l'IA a trouvé le meilleur dosage entre les questions à poser.",
          },
        ]}
        note="Sous le capot : un algorithme de théorie des jeux (Counterfactual Regret Minimization, CFR+) tourné côté serveur. La stratégie apprise s'approche d'un « équilibre de Nash » — le point où aucune autre façon de jouer ne ferait mieux. Les graphiques montrent, essai après essai, quelles questions l'IA privilégie et comment ses erreurs diminuent."
      />
    </LabPage>
  );
};

export default StrategyLabPage;
