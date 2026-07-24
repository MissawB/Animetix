import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { RefreshCw, Split } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../../utils/apiClient';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_CTA,
} from '../labs/components/shared/LabKit';

interface CounterfactualResult {
  what_if: string;
  analysis: string;
  butterfly_effect: string[];
  what_if_query: string;
  counterfactual_regret: number;
  actual_utility: number;
  alternative_utility: number;
  alternative_response: string;
}

const CounterfactualSimulatorPage: React.FC = () => {
  const { t } = useTranslation();
  const [whatIf, setWhatIf] = useState('');
  const [actualContext] = useState<string>(t('labs.counterfactual_simulator.initial_context'));
  const [result, setResult] = useState<CounterfactualResult | null>(null);

  const simulateMutation = useMutation<CounterfactualResult, Error>({
    mutationFn: async () => {
      return apiClient('/api/v1/cognition/counterfactual/', {
        method: 'POST',
        body: JSON.stringify({
          what_if: whatIf,
          actual_context: [{ role: 'user', content: actualContext }],
        }),
        headers: { 'Content-Type': 'application/json' },
      });
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!whatIf.trim()) return;
    simulateMutation.mutate();
  };

  return (
    <LabPage>
      <LabHeader
        glyph="時"
        code="Synapse · Timeline"
        title={t('labs.counterfactual_simulator.title_part1')}
        accent={t('labs.counterfactual_simulator.title_part2')}
        lede="Décris une décision alternative : le simulateur projette la timeline correspondante, la compare à la réalité actuelle et chiffre le regret contrefactuel entre les deux trajectoires."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Colonne de saisie */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title={t('labs.counterfactual_simulator.current_reality')}>
            <div className="space-y-4">
              <p className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 text-xs italic leading-relaxed text-[#F4F1E8]/80">
                "{actualContext}"
              </p>
              <p className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                {t('labs.counterfactual_simulator.timeline_analysis')}
              </p>
            </div>
          </LabPanel>

          <LabPanel title={t('labs.counterfactual_simulator.what_if_scenario')}>
            <form onSubmit={onSubmit} className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="what-if-scenario" className={LAB_LABEL}>
                  {t('labs.counterfactual_simulator.what_if_scenario')}
                </label>
                <textarea
                  id="what-if-scenario"
                  aria-label={t('labs.counterfactual_simulator.what_if_scenario')}
                  value={whatIf}
                  onChange={(e) => setWhatIf(e.target.value)}
                  placeholder={t('labs.counterfactual_simulator.what_if_placeholder')}
                  className={`${LAB_INPUT} min-h-[120px] resize-none`}
                />
              </div>
              <button
                type="submit"
                disabled={simulateMutation.isPending || !whatIf.trim()}
                className={LAB_CTA}
              >
                {simulateMutation.isPending ? (
                  <RefreshCw className="h-5 w-5 animate-spin" aria-hidden="true" />
                ) : (
                  t('labs.counterfactual_simulator.branch_timeline')
                )}
              </button>
            </form>
          </LabPanel>
        </div>

        {/* Colonne de résultats */}
        <div className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="space-y-8"
              >
                {/* Regret contrefactuel */}
                <LabPanel title={t('labs.counterfactual_simulator.regret_calculation')}>
                  <div className="flex flex-wrap items-end justify-between gap-8">
                    <div className="flex items-end gap-4">
                      <span
                        className={`font-manga text-6xl font-black italic leading-none ${
                          result.counterfactual_regret > 0 ? 'text-[#E8442B]' : 'text-[#FDB913]'
                        }`}
                      >
                        {result.counterfactual_regret > 0 ? '+' : ''}
                        {(result.counterfactual_regret * 100).toFixed(1)}%
                      </span>
                      <span
                        className={`mb-1 rounded-full border px-3 py-1 text-[9px] font-black uppercase tracking-widest ${
                          result.counterfactual_regret > 0
                            ? 'border-[#E8442B]/40 text-[#E8442B]'
                            : 'border-[#FDB913]/40 text-[#FDB913]'
                        }`}
                      >
                        {result.counterfactual_regret > 0
                          ? t('labs.counterfactual_simulator.optimized_timeline')
                          : t('labs.counterfactual_simulator.superior_reality')}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="mb-3 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {t('labs.counterfactual_simulator.alternative_utility')}
                      </p>
                      <div className="h-2 w-32 overflow-hidden rounded-full bg-[#F4F1E8]/10">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${result.alternative_utility * 100}%` }}
                          className="h-full bg-[#FDB913]"
                        />
                      </div>
                    </div>
                  </div>
                </LabPanel>

                {/* Comparaison des timelines */}
                <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                  <LabPanel title={t('labs.counterfactual_simulator.current_reality_title')}>
                    <p className="text-sm italic leading-relaxed text-[#8F94A5]">
                      {t('labs.counterfactual_simulator.current_reality_desc', {
                        actualUtility: (result.actual_utility * 100).toFixed(0),
                      })}
                    </p>
                  </LabPanel>
                  <LabPanel
                    title={t('labs.counterfactual_simulator.alternative_timeline_title')}
                    className="border-[#FDB913]/30"
                  >
                    <p className="text-sm italic leading-relaxed text-[#F4F1E8]/80">
                      "{result.alternative_response}"
                    </p>
                  </LabPanel>
                </div>

                {/* Analyse de l'inférence */}
                <LabPanel title={t('labs.counterfactual_simulator.inference_analysis_title')}>
                  <p className="mb-8 text-sm leading-relaxed text-[#F4F1E8]/80">
                    {t('labs.counterfactual_simulator.inference_analysis_desc', {
                      whatIfQuery: result.what_if_query,
                      regretCondition:
                        result.counterfactual_regret > 0
                          ? t('labs.counterfactual_simulator.inference_analysis_more_corr')
                          : t('labs.counterfactual_simulator.inference_analysis_less_eff'),
                    })}
                  </p>
                  <div className="flex flex-wrap items-center gap-4">
                    <div className="flex items-center gap-3 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
                      <span className="rounded-full border border-[#E8442B]/40 px-2.5 py-0.5 text-[9px] font-black uppercase tracking-widest text-[#E8442B]">
                        Z3 SOLVER
                      </span>
                      <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {t('labs.counterfactual_simulator.decision_logic_resolved')}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
                      <span className="rounded-full border border-[#FDB913]/40 px-2.5 py-0.5 text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                        RAG TRAJECTORY
                      </span>
                      <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {t('labs.counterfactual_simulator.path_distance', { pathDistance: 0.42 })}
                      </span>
                    </div>
                  </div>
                </LabPanel>
              </motion.div>
            ) : (
              <LabEmpty
                icon={<Split className="h-20 w-20" aria-hidden="true" />}
                title={t('labs.counterfactual_simulator.timelines_unloaded_title')}
                hint={t('labs.counterfactual_simulator.timelines_unloaded_desc')}
              />
            )}
          </AnimatePresence>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Décris le scénario alternatif',
            body: t('labs.counterfactual_simulator.explainer_text_card1'),
          },
          {
            title: 'Compare les deux timelines',
            body: t('labs.counterfactual_simulator.explainer_text_card2'),
          },
          {
            title: 'Interprète le score de regret',
            body: `${t('labs.counterfactual_simulator.warning_text_part1')} ${t('labs.counterfactual_simulator.warning_text_part2')}`,
          },
        ]}
        note={t('labs.counterfactual_simulator.protocol_text')}
      />
    </LabPage>
  );
};

export default CounterfactualSimulatorPage;
