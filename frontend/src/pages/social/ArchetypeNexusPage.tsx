import React from 'react';
import Plot from '../../components/LazyPlot';
import { Data } from 'plotly.js';
import { Layers, Clock, ChevronRight, Target, BarChart3, Cpu, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiClient } from '../../utils/apiClient';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { LabPage, LabHeader, LabPanel, LAB_BTN_GHOST } from '../labs/components/shared/LabKit';

/** Encre du module (synapse 型 du noyau cognitif) — accents de données. */
const NEXUS_INK = '#5D7FD3';

interface StatBarProps {
  label: string;
  value: number;
  color: string;
}

const StatBar: React.FC<StatBarProps> = ({ label, value, color }) => (
  <div className="space-y-2">
    <div className="flex items-end justify-between">
      <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
        {label}
      </span>
      <span className="text-xs font-black italic text-[#F4F1E8]">{Math.round(value * 100)}%</span>
    </div>
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#F4F1E8]/10">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${value * 100}%` }}
        transition={{ duration: 1, ease: 'easeOut' }}
        className={`h-full ${color}`}
      />
    </div>
  </div>
);

interface ArchetypeData {
  id: string;
  aura_type: string;
  intensity: number;
  accent: string;
}

interface CognitiveStats {
  shonen_affinity: number;
  seinen_affinity: number;
  logic_consistency: number;
  memory_depth: number;
}

interface RecentSignal {
  context: string;
  is_positive: boolean;
}

interface DriftHistoryEntry {
  date: string;
  shonen: number;
  seinen: number;
}

interface ArchetypeNexusResponse {
  archetype: ArchetypeData;
  logical_rules: string[];
  recent_signals: RecentSignal[];
  cognitive_stats: CognitiveStats;
  drift_history: DriftHistoryEntry[];
}

const ArchetypeNexusPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useQuery<ArchetypeNexusResponse>({
    queryKey: ['archetype-nexus'],
    queryFn: () => apiClient('/api/v1/cognition/archetype-nexus/'),
  });

  if (isLoading)
    return (
      <div className="flex min-h-screen w-full flex-col items-center justify-center bg-[#0B0C10]">
        <CardSkeleton />
        <div className="mt-12 grid w-full max-w-7xl grid-cols-1 gap-8 px-6 md:grid-cols-3">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );

  if (isError || !data)
    return (
      <div className="flex min-h-screen w-full flex-col items-center justify-center bg-[#0B0C10] text-center">
        <h2 className="font-manga text-3xl font-black uppercase italic text-[#E8442B]">
          {t('social.nexus.cognitive_failure', 'Défaillance Cognitive')}
        </h2>
        <p className="mt-4 text-sm leading-relaxed text-[#8F94A5]">
          {t('social.nexus.sync_error', 'Impossible de synchroniser le profil neuronal.')}
        </p>
      </div>
    );

  const { archetype, logical_rules, recent_signals, cognitive_stats, drift_history } = data;

  const driftPlotData =
    drift_history && drift_history.length > 0
      ? [
          {
            x: drift_history.map((h) => h.date),
            y: drift_history.map((h) => h.shonen),
            name: 'Shonen',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#FDB913', width: 3, shape: 'spline' },
            marker: { size: 8, color: '#FDB913' },
          },
          {
            x: drift_history.map((h) => h.date),
            y: drift_history.map((h) => h.seinen),
            name: 'Seinen',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: NEXUS_INK, width: 3, shape: 'spline' },
            marker: { size: 8, color: NEXUS_INK },
          },
        ]
      : [];

  return (
    <LabPage>
      <LabHeader
        glyph="型"
        code="Synapse · Archetype"
        title="Archetype"
        accent="Nexus"
        lede={t(
          'social.nexus.subtitle',
          "Visualisation de votre empreinte sémantique et de vos biais narratifs déduits par l'IA.",
        )}
      />

      <div className="mb-12 grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Colonne Gauche: Archétype Dominant & Aura */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title={t('social.nexus.master_archetype', 'Archétype Maître')}>
            <div className="text-center">
              <div
                className="mx-auto mb-6 flex h-28 w-28 items-center justify-center rounded-full border-2 bg-[#0B0C10] text-5xl font-bold leading-none"
                style={{ borderColor: `${NEXUS_INK}66`, color: NEXUS_INK }}
                aria-hidden
              >
                型
              </div>
              <p className="font-manga text-2xl font-black uppercase italic tracking-tighter text-[#F4F1E8]">
                {archetype.id.replace('_', ' ')}
              </p>
              <p className="mt-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                {t('social.nexus.aura_intensity', "Aura: {{type}} ({{percent}}% d'intensité)", {
                  type: archetype.aura_type,
                  percent: Math.round(archetype.intensity * 100),
                })}
              </p>
            </div>
            <div className="mt-8 grid grid-cols-2 gap-4 border-t border-[#F4F1E8]/10 pt-6">
              <div className="text-center">
                <p className="text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
                  {t('social.nexus.stability', 'Stabilité')}
                </p>
                <p
                  className="font-manga mt-1 text-xl font-black italic"
                  style={{ color: NEXUS_INK }}
                >
                  92%
                </p>
              </div>
              <div className="border-l border-[#F4F1E8]/10 text-center">
                <p className="text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
                  {t('social.nexus.convergence', 'Convergence')}
                </p>
                <p className="font-manga mt-1 text-xl font-black italic text-[#F4F1E8]">
                  {t('social.nexus.convergence_high', 'HAUTE')}
                </p>
              </div>
            </div>
          </LabPanel>

          <LabPanel
            title={t('social.nexus.neural_profile', 'Profil Neuronal')}
            corner={
              <span className="flex items-center gap-1.5">
                <BarChart3 className="h-3.5 w-3.5" aria-hidden="true" /> 4 axes
              </span>
            }
          >
            <div className="space-y-6">
              <StatBar
                label={t('social.nexus.shonen_affinity', 'Affinité Shonen')}
                value={cognitive_stats.shonen_affinity}
                color="bg-[#FDB913]"
              />
              <StatBar
                label={t('social.nexus.seinen_affinity', 'Complexité Seinen')}
                value={cognitive_stats.seinen_affinity}
                color="bg-[#5D7FD3]"
              />
              <StatBar
                label={t('social.nexus.logic_consistency', 'Cohérence Logique')}
                value={cognitive_stats.logic_consistency}
                color="bg-[#5D7FD3]"
              />
              <StatBar
                label={t('social.nexus.memory_depth', 'Profondeur Mémoire')}
                value={Math.min(cognitive_stats.memory_depth / 50, 1)}
                color="bg-[#5D7FD3]"
              />
            </div>
          </LabPanel>
        </div>

        {/* Colonne Droite: Graphique de Drift & Z3 Rules */}
        <div className="flex flex-col space-y-8 lg:col-span-8">
          {/* Archetype Drift Evolution (Le Graphique) */}
          <LabPanel
            title="Dérive d'archétype"
            corner={
              <span className="flex items-center gap-1.5">
                <TrendingUp className="h-3.5 w-3.5" aria-hidden="true" /> série temporelle · alpha
              </span>
            }
            className="flex flex-grow flex-col"
          >
            <div className="relative min-h-[300px] flex-grow">
              {drift_history && drift_history.length > 0 ? (
                <Plot
                  data={driftPlotData as unknown as Data[]}
                  layout={{
                    autosize: true,
                    height: 300,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    margin: { l: 40, r: 20, b: 40, t: 10 },
                    showlegend: true,
                    legend: { font: { color: '#8F94A5', size: 10 }, orientation: 'h', y: -0.2 },
                    xaxis: {
                      gridcolor: 'rgba(244,241,232,0.05)',
                      tickfont: { color: '#8F94A5', size: 8 },
                      showgrid: true,
                    },
                    yaxis: {
                      gridcolor: 'rgba(244,241,232,0.05)',
                      tickfont: { color: '#8F94A5', size: 8 },
                      range: [0, 1.1],
                      showgrid: true,
                    },
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  style={{ width: '100%' }}
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#F4F1E8]/15 text-center text-[#8F94A5]">
                  <TrendingUp className="mb-4 h-12 w-12 opacity-40" aria-hidden="true" />
                  <p className="text-[10px] font-black uppercase tracking-widest">
                    {t(
                      'social.nexus.insufficient_history',
                      'Historique insuffisant pour projection',
                    )}
                  </p>
                </div>
              )}
            </div>
          </LabPanel>

          {/* Z3 Deduced Rules */}
          <LabPanel
            title="Modèle logique SAT (Z3)"
            corner={
              <span className="flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5" aria-hidden="true" /> résolu
              </span>
            }
          >
            <div className="mb-6 flex items-center justify-between gap-4">
              <p className="text-xs leading-relaxed text-[#8F94A5]">
                {t('social.nexus.z3_desc', 'Contraintes formelles déduites de vos interactions.')}
              </p>
              <Link to="/social/neuro-memory/" className={`${LAB_BTN_GHOST} flex-none`}>
                {t('social.nexus.manage', 'Gérer')}{' '}
                <ChevronRight className="h-3 w-3" aria-hidden="true" />
              </Link>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {logical_rules.map((rule: string, i: number) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-center gap-4 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 transition-colors hover:border-[#5D7FD3]/40"
                >
                  <div
                    className="flex h-8 w-8 flex-none items-center justify-center rounded-lg font-mono text-[10px] font-black"
                    style={{ backgroundColor: `${NEXUS_INK}1a`, color: NEXUS_INK }}
                  >
                    {i + 1}
                  </div>
                  <code className="text-xs font-bold uppercase tracking-wider text-[#F4F1E8]/80">
                    {rule}
                  </code>
                </motion.div>
              ))}
            </div>
          </LabPanel>
        </div>
      </div>

      {/* Bottom Section: Signals */}
      <LabPanel
        title={t('social.nexus.episodic_memory', 'Signaux de Mémoire Épisodique')}
        corner={
          <span className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" aria-hidden="true" /> {recent_signals.length} signaux
          </span>
        }
      >
        <div className="relative space-y-6">
          <div className="absolute bottom-0 left-5 top-0 w-0.5 bg-[#F4F1E8]/10" aria-hidden />

          {recent_signals.map((sig, i) => (
            <div key={i} className="relative flex gap-6">
              <div
                className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
                  sig.is_positive
                    ? 'bg-[#FDB913]/15 text-[#FDB913]'
                    : 'bg-[#E8442B]/15 text-[#E8442B]'
                }`}
              >
                {sig.is_positive ? (
                  <Target className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <Layers className="h-5 w-5" aria-hidden="true" />
                )}
              </div>
              <div className="flex-grow pt-2">
                <div className="mb-1 flex items-center justify-between">
                  <p
                    className={`text-[10px] font-black uppercase tracking-widest ${
                      sig.is_positive ? 'text-[#FDB913]' : 'text-[#E8442B]'
                    }`}
                  >
                    {sig.is_positive
                      ? t('social.nexus.positive_signal', 'SIGNAL POSITIF')
                      : t('social.nexus.negative_signal', 'SIGNAL NÉGATIF')}
                  </p>
                  <span className="font-mono text-[8px] text-[#8F94A5]">
                    STEP_0{recent_signals.length - i}
                  </span>
                </div>
                <p className="text-sm font-bold italic text-[#F4F1E8]/80">"{sig.context}"</p>
              </div>
            </div>
          ))}

          {recent_signals.length === 0 && (
            <div className="py-12 text-center text-xs font-black uppercase tracking-widest text-[#8F94A5]">
              {t('social.nexus.no_signal', 'Aucun signal indexé')}
            </div>
          )}
        </div>
      </LabPanel>

      {/* Global Warning / Alpha Status */}
      <div className="mt-24 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 text-center">
        <p className="text-xs leading-relaxed text-[#8F94A5]">
          {t(
            'social.nexus.warning_1',
            'Avertissement : Les déductions neuro-symboliques sont basées sur des modèles stochastiques résolus en temps réel.',
          )}{' '}
          <br />
          {t(
            'social.nexus.warning_2',
            "Le drift d'archétype est recalculé après chaque session de forge ou de débat.",
          )}
        </p>
      </div>
    </LabPage>
  );
};

export default ArchetypeNexusPage;
