import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, AlertTriangle } from 'lucide-react';
import { useNeuralDiagnostics } from '../../features/labs/hooks/useNeuralDiagnostics';
import EntropyBarChart from '../../features/labs/components/EntropyBarChart';
import LogitLensHeatmap from '../../features/labs/components/LogitLensHeatmap';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabStat,
  LabGuide,
  LAB_INPUT,
  LAB_CTA,
} from './components/shared/LabKit';

const NeuralDiagnosticsPage: React.FC = () => {
  const { t } = useTranslation();
  const [prompt, setPrompt] = useState('');
  const { runDiagnostic, loading, data, error } = useNeuralDiagnostics();

  const handleRunDiagnostic = async () => {
    if (!prompt.trim() || loading) return;
    try {
      await runDiagnostic(prompt);
    } catch (err) {
      console.error('Failed to run diagnostic:', err);
    }
  };

  const titleParts = t('labs.diagnostics.title').split(' ');

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Diagnostic"
        title={titleParts[0]}
        accent={titleParts.slice(1).join(' ') || undefined}
        lede={t('labs.diagnostics.subtitle')}
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Entrée & mesures */}
        <div className="flex flex-col gap-8 lg:col-span-4">
          <LabPanel title={t('labs.diagnostics.input_prompt')}>
            <div className="space-y-6">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={t('labs.diagnostics.placeholder')}
                aria-label={t('labs.diagnostics.input_prompt')}
                className={`${LAB_INPUT} h-40 resize-none`}
              />
              <button
                type="button"
                onClick={handleRunDiagnostic}
                disabled={loading || !prompt.trim()}
                className={LAB_CTA}
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#F4F1E8]/30 border-t-[#F4F1E8]" />
                    {t('labs.diagnostics.analyzing')}
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Send className="h-4 w-4" aria-hidden="true" />{' '}
                    {t('labs.diagnostics.run_diagnostic')}
                  </span>
                )}
              </button>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3 rounded-xl border border-[#E8442B]/25 bg-[#E8442B]/[0.06] p-4 text-xs font-bold text-[#E8442B]"
                >
                  <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
                  {t('labs.diagnostics.error')}
                </motion.div>
              )}
            </div>
          </LabPanel>

          <AnimatePresence>
            {data && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="grid grid-cols-2 gap-4"
              >
                <LabStat
                  label={t('labs.diagnostics.avg_entropy')}
                  value={data.avg_entropy?.toFixed(4) || '0.0000'}
                  tone="gold"
                  className="px-4 py-4"
                />
                <LabStat
                  label={t('labs.diagnostics.confidence')}
                  value={`${(data.confidence_score * 100).toFixed(1)}%`}
                  className="px-4 py-4"
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Visualisations */}
        <div className="grid grid-cols-1 gap-8 lg:col-span-8">
          <LabPanel title={t('labs.diagnostics.entropy_dist')}>
            <div className="relative flex min-h-[300px] items-center justify-center">
              {!data && !loading && (
                <p className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
                  {t('labs.diagnostics.waiting_data')}
                </p>
              )}
              {loading && (
                <div className="flex flex-col items-center gap-4">
                  <span className="h-8 w-8 animate-spin rounded-full border-2 border-[#FDB913]/30 border-t-[#FDB913]" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                    {t('labs.diagnostics.processing_layers')}
                  </span>
                </div>
              )}
              {data && (
                <div className="h-full w-full">
                  <EntropyBarChart data={data.per_token_diagnostics} />
                </div>
              )}
            </div>
          </LabPanel>

          <LabPanel title={t('labs.diagnostics.heatmap')}>
            <div className="relative flex min-h-[300px] items-center justify-center">
              {!data && !loading && (
                <p className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
                  {t('labs.diagnostics.synaptic_mapping')}
                </p>
              )}
              {loading && (
                <div className="flex flex-col items-center gap-4">
                  <span className="h-8 w-8 animate-spin rounded-full border-2 border-[#FDB913]/30 border-t-[#FDB913]" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                    {t('labs.diagnostics.mapping_synapses')}
                  </span>
                </div>
              )}
              {data && (
                <div className="h-full w-full">
                  <LogitLensHeatmap trajectory={data.logit_lens_trajectory} />
                </div>
              )}
            </div>
          </LabPanel>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Écris un prompt',
            body: "Tape une phrase et lance le diagnostic : le modèle de langage l'analyse token par token et montre ce qui se passe à l'intérieur pendant l'inférence.",
          },
          {
            title: "Lis l'entropie",
            body: "Chaque barre mesure l'hésitation du modèle sur un token. Une barre basse signifie qu'il est sûr de lui, une barre haute qu'il hésite entre plusieurs suites possibles.",
          },
          {
            title: 'Explore la heatmap',
            body: 'La carte « logit lens » montre comment la prédiction se précise couche après couche. Utile pour repérer des biais ou comprendre une sortie inattendue.',
          },
        ]}
        note="Diagnostic d'inférence réel : le prompt est envoyé à l'endpoint labs/diagnostics qui calcule l'entropie de la distribution de sortie par token, un score de confiance global et la trajectoire logit lens à travers les couches du modèle. Les graphiques visualisent ces métriques telles quelles, sans post-traitement."
      />
    </LabPage>
  );
};

export default NeuralDiagnosticsPage;
