import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Brain, BarChart3, Grid3X3, Send, AlertTriangle, Sparkles } from 'lucide-react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { useNeuralDiagnostics } from '../../features/labs/hooks/useNeuralDiagnostics';
import EntropyBarChart from '../../features/labs/components/EntropyBarChart';
import LogitLensHeatmap from '../../features/labs/components/LogitLensHeatmap';

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

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#0a0a12] text-white p-6 flex flex-col gap-6">
        {/* Header Section */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Brain className="w-6 h-6 text-blue-500" />
            </div>
            <h1 className="text-3xl font-black italic manga-font uppercase tracking-tighter">
              {t('labs.diagnostics.title').split(' ')[0]} <span className="text-blue-500">{t('labs.diagnostics.title').split(' ')[1]}</span>
            </h1>
          </div>
          <p className="text-gray-400 text-sm font-medium italic">
            {t('labs.diagnostics.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-grow">
          {/* Left Column: Input & Controls */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            <Card className="p-6 bg-[#12121e] border-white/5 flex flex-col gap-4">
              <h2 className="text-xs font-black uppercase tracking-[0.2em] text-blue-500 flex items-center gap-2">
                <Activity className="w-3 h-3" /> {t('labs.diagnostics.input_prompt')}
              </h2>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={t('labs.diagnostics.placeholder')}
                aria-label={t('labs.diagnostics.input_prompt')}
                className="w-full h-40 bg-black/40 border border-white/10 rounded-xl p-4 text-sm font-medium focus:border-blue-500/50 outline-none transition-colors resize-none"
              />
              <Button
                onClick={handleRunDiagnostic}
                disabled={loading || !prompt.trim()}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-black italic uppercase tracking-widest text-xs py-6 rounded-xl shadow-[0_0_20px_rgba(59,130,246,0.2)]"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    {t('labs.diagnostics.analyzing')}
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Send className="w-4 h-4" /> {t('labs.diagnostics.run_diagnostic')}
                  </span>
                )}
              </Button>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400 text-xs font-bold italic"
                >
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  {t('labs.diagnostics.error')}
                </motion.div>
              )}
            </Card>

            {/* Global Metrics Display */}
            <AnimatePresence>
              {data && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="grid grid-cols-2 gap-4"
                >
                  <Card className="p-4 bg-[#12121e] border-white/5 text-center">
                    <span className="block text-[8px] font-black uppercase text-gray-500 mb-1 tracking-widest">{t('labs.diagnostics.avg_entropy')}</span>
                    <span className="text-xl font-black italic manga-font text-blue-500">
                      {data.avg_entropy?.toFixed(4) || '0.0000'}
                    </span>
                  </Card>
                  <Card className="p-4 bg-[#12121e] border-white/5 text-center">
                    <span className="block text-[8px] font-black uppercase text-gray-500 mb-1 tracking-widest">{t('labs.diagnostics.confidence')}</span>
                    <span className="text-xl font-black italic manga-font text-purple-500">
                      {(data.confidence_score * 100).toFixed(1)}%
                    </span>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right Column: Visualizations */}
          <div className="lg:col-span-8 grid grid-cols-1 gap-6">
            {/* Entropy Distribution Placeholder */}
            <Card className="bg-[#12121e] border-white/5 overflow-hidden flex flex-col">
              <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 flex items-center gap-2">
                  <BarChart3 className="w-3 h-3 text-blue-500" /> {t('labs.diagnostics.entropy_dist')}
                </h3>
              </div>
              <div className="flex-grow min-h-[300px] flex items-center justify-center relative">
                {!data && !loading && (
                  <div className="text-gray-600 font-black italic uppercase text-xs tracking-widest opacity-20">
                    {t('labs.diagnostics.waiting_data')}
                  </div>
                )}
                {loading && (
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-blue-500/50">{t('labs.diagnostics.processing_layers')}</span>
                  </div>
                )}
                {data && (
                  <div className="w-full h-full">
                    <EntropyBarChart data={data.per_token_diagnostics} />
                  </div>
                )}
              </div>
            </Card>

            {/* Activation Heatmap Placeholder */}
            <Card className="bg-[#12121e] border-white/5 overflow-hidden flex flex-col">
              <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 flex items-center gap-2">
                  <Grid3X3 className="w-3 h-3 text-purple-500" /> {t('labs.diagnostics.heatmap')}
                </h3>
              </div>
              <div className="flex-grow min-h-[300px] flex items-center justify-center relative">
                {!data && !loading && (
                  <div className="text-gray-600 font-black italic uppercase text-xs tracking-widest opacity-20">
                    {t('labs.diagnostics.synaptic_mapping')}
                  </div>
                )}
                {loading && (
                   <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
                    <span className="text-[10px] font-black uppercase tracking-widest text-purple-500/50">{t('labs.diagnostics.mapping_synapses')}</span>
                  </div>
                )}
                {data && (
                   <div className="w-full h-full">
                    <LogitLensHeatmap trajectory={data.logit_lens_trajectory} />
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>

        {/* Guide & Protocole */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
          <Card padding="lg" className="bg-black/40 border-blue-500/20 shadow-[0_0_50px_rgba(59,130,246,0.1)] relative overflow-hidden group">
            <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
              <Brain className="w-64 h-64 text-blue-500" />
            </div>
            <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-blue-400" /> Guide des Diagnostics
            </h4>
            <div className="space-y-4 relative z-10">
              <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                <span className="text-blue-400">Le Prompt :</span> Tapez une phrase et lancez le diagnostic : le modèle de langage l'analyse token par token et vous montre ce qui se passe à l'intérieur pendant l'inférence.
              </p>
              <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                <span className="text-blue-400">L'Entropie :</span> Chaque barre mesure l'hésitation du modèle sur un token. Une barre basse signifie qu'il est sûr de lui, une barre haute qu'il hésite entre plusieurs suites possibles.
              </p>
              <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                <span className="text-blue-400">La Heatmap :</span> La carte "logit lens" montre comment la prédiction se précise couche après couche. Utile pour repérer des biais ou comprendre une sortie inattendue.
              </p>
            </div>
          </Card>

          <div className="p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
            <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-blue-200/60">
              Diagnostic d'inférence réel : le prompt est envoyé à l'endpoint labs/diagnostics qui calcule l'entropie de la distribution de sortie par token, un score de confiance global et la trajectoire logit lens à travers les couches du modèle. <br />
              Les graphiques visualisent ces métriques telles quelles, sans post-traitement.
            </p>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default NeuralDiagnosticsPage;