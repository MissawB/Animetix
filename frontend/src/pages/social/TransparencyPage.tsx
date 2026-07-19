import React from 'react';
import { Activity, Zap, Users, Database, Brain, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Button } from '../../components/ui/Button';
import { useTranslation } from 'react-i18next';

import { TransparencyData } from '../../types';
import { MODEL_COMPARISON } from './transparencyData';
import { TransparencyKpiCard } from './components/TransparencyKpiCard';
import { TransparencyEvolutionChart } from './components/TransparencyEvolutionChart';
import { ModelComparisonCard } from './components/ModelComparisonCard';
import { DriftAuditCard } from './components/DriftAuditCard';
import { EthicsCommitmentsCard } from './components/EthicsCommitmentsCard';
import { SecurityAuditSection } from './components/SecurityAuditSection';

const TransparencyPage: React.FC = () => {
  const { t } = useTranslation();

  const { data, isLoading } = useQuery<TransparencyData>({
    queryKey: ['transparency'],
    queryFn: () => apiClient('/api/v1/transparency/'),
  });

  if (isLoading)
    return (
      // Même contexte sombre forcé que la page : pas de flash clair pendant le chargement.
      <div
        data-bs-theme="dark"
        className="min-h-screen bg-[#05050a] px-6 py-32 flex flex-col items-center justify-center"
      >
        <div className="w-20 h-20 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-8" />
        <p className="text-blue-500 font-black italic uppercase tracking-[0.3em] animate-pulse">
          {t('social.transparency.loading', 'Synchronisation avec le Nexus...')}
        </p>
      </div>
    );

  if (!data) return null;

  const metrics = data.global_metrics;

  // Timeline réelle (précision d'évaluation par mois). Le graphe n'est affiché
  // qu'à partir de deux points, sinon il ne serait pas lisible.
  const timeline = data.evolution_timeline || [];

  return (
    // Page volontairement toujours sombre : data-bs-theme force les tokens
    // (bg-surface-card…) et les variantes dark: du sous-arbre, sinon les Cards
    // deviennent blanches en thème clair alors que le texte hérite text-white.
    <div data-bs-theme="dark" className="min-h-screen bg-[#05050a] text-white">
      {/* Hero Section with Live Pulse */}
      <section className="relative py-24 overflow-hidden border-b border-white/5">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-600/10 to-transparent" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-500/5 blur-[120px] rounded-full animate-pulse" />

        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          {data.model_uptime != null && (
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-black uppercase tracking-[0.2em] mb-8">
              <Activity className="w-3 h-3 animate-pulse" />{' '}
              {t(
                'social.transparency.uptime_badge',
                'Fiabilité du modèle : {{pct}}% (réponses sans hallucination)',
                { pct: data.model_uptime },
              )}
            </div>
          )}
          <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-6 leading-tight">
            HUB DE{' '}
            <span className="text-blue-500">
              {t('social.transparency.title_accent', 'transparence')}
            </span>{' '}
            IA
          </h1>
          <p className="max-w-3xl mx-auto text-gray-500 font-bold uppercase tracking-widest leading-relaxed">
            {t(
              'social.transparency.subtitle',
              "Découvrez comment vos interactions façonnent le cerveau d'Animetix. Nous croyons en une intelligence artificielle ouverte, auditable et alignée sur sa communauté.",
            )}
          </p>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-6 py-20 space-y-24">
        {/* Key Performance Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <TransparencyKpiCard
            icon={<Users className="w-8 h-8 text-blue-500 mb-4" />}
            value={(metrics?.total_feedbacks || 0).toLocaleString()}
            label={t('social.transparency.kpi_feedbacks', 'Feedbacks Reçus')}
          />
          <TransparencyKpiCard
            icon={<Database className="w-8 h-8 text-emerald-500 mb-4" />}
            value={(metrics?.knowledge_nodes || 0).toLocaleString()}
            label={t('social.transparency.kpi_engrams', 'Engrammes Indexés')}
          />
          <TransparencyKpiCard
            icon={<Brain className="w-8 h-8 text-purple-500 mb-4" />}
            value={`${(metrics?.community_satisfaction * 100).toFixed(0)}%`}
            label={t('social.transparency.kpi_satisfaction', 'Satisfaction IA')}
          />
          <TransparencyKpiCard
            icon={<Zap className="w-8 h-8 text-yellow-500 mb-4" />}
            value={metrics?.model_version || 'Champion v2.4'}
            label={t('social.transparency.kpi_version', 'Version Actuelle')}
            valueClassName="text-2xl font-black italic mb-1 uppercase line-clamp-1"
          />
        </div>

        {/* Evolution Chart */}
        <TransparencyEvolutionChart timeline={timeline} />

        {/* SOTA Benchmarks & Embedding Drift */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-12">
          <div className="xl:col-span-2 space-y-12">
            <header>
              <h2 className="text-3xl font-black italic manga-font uppercase mb-1">
                {t('social.transparency.vs_title_1', 'NOTRE MODÈLE')}{' '}
                <span className="text-blue-500">
                  {t('social.transparency.vs_title_2', "VS L'OPEN SOURCE")}
                </span>
              </h2>
              <p className="text-[10px] font-bold opacity-30 uppercase tracking-[0.3em]">
                {t(
                  'social.transparency.vs_subtitle',
                  "Le modèle de base d'Animetix face aux meilleurs LLM open source du marché",
                )}
              </p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {MODEL_COMPARISON.map((model, i) => (
                <ModelComparisonCard key={model.model_id} model={model} index={i} />
              ))}
            </div>

            <p className="text-[10px] font-bold opacity-30 uppercase tracking-widest leading-relaxed">
              {t(
                'social.transparency.vs_footnote',
                'Champion tourne sur Qwen3.5-9B : un modèle compact hébergé sur notre propre GPU, spécialisé anime/manga par fine-tuning DPO continu. Les géants ci-dessus dominent les benchmarks généralistes — notre pari est la spécialisation, pas la taille.',
              )}
            </p>
          </div>

          <div className="space-y-12">
            <header>
              <h2 className="text-3xl font-black italic manga-font uppercase mb-1">
                DRIFT <span className="text-blue-500">AUDIT</span>
              </h2>
              <p className="text-[10px] font-bold opacity-30 uppercase tracking-[0.2em]">
                {t('social.transparency.vector_base', 'Base Vectorielle')}
              </p>
            </header>

            <div className="space-y-4">
              {data.embedding_drift &&
                Object.entries(data.embedding_drift).map(([key, info]) => (
                  <DriftAuditCard key={key} name={key} info={info} />
                ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <EthicsCommitmentsCard ethicsScore={data.ethics_score} />
          <SecurityAuditSection ethicsAudit={data.ethics_audit} />
        </div>

        {/* Participation CTA */}
        <section className="p-20 rounded-[4rem] bg-gradient-to-br from-blue-600 to-indigo-700 flex flex-col items-center text-center shadow-[0_0_60px_rgba(37,99,235,0.4)] relative overflow-hidden group">
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10" />
          <h2 className="text-6xl font-black italic manga-font uppercase mb-8 tracking-tighter relative z-10">
            {t('social.transparency.cta_title', 'Devenez Curateur du Nexus')}
          </h2>
          <p className="max-w-3xl text-blue-100 font-bold uppercase tracking-widest text-xs mb-12 leading-relaxed relative z-10 opacity-80">
            {t(
              'social.transparency.cta_desc',
              "Chaque interaction avec l'IA renforce la base de connaissance commune. Grâce au protocole DPO (Direct Preference Optimization), vos choix guident l'apprentissage du modèle Champion.",
            )}
          </p>
          <div className="flex flex-wrap gap-6 justify-center relative z-10">
            {/* !important : le variant primary impose text-white, qui gagnerait sur text-blue-600 (bouton blanc → texte invisible). */}
            <Button
              as={Link}
              to="/lab/"
              variant="primary"
              className="!bg-white !text-blue-600 px-12 py-7 rounded-2xl border-none shadow-xl hover:scale-105 transition-transform font-black italic uppercase no-underline"
            >
              {t('social.transparency.cta_lab', 'DÉCOUVRIR LE LAB')}
            </Button>
            {/* !important : le variant outline impose border/text/hover en surface-text, qui gagneraient sinon. */}
            <Button
              as={Link}
              to="/research/papers/"
              variant="outline"
              className="!border-white/30 !text-white hover:!bg-white/10 px-12 py-7 rounded-2xl font-black italic uppercase no-underline"
            >
              {t('social.transparency.cta_research', 'LA RECHERCHE IA')}
            </Button>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5 bg-black/40">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-center gap-4 opacity-30">
          <Clock className="w-5 h-5" />
          <span className="text-[10px] font-black uppercase tracking-widest">
            {metrics?.last_training
              ? t('social.transparency.last_eval', 'Dernière évaluation : {{date}}', {
                  date: metrics.last_training,
                })
              : t('social.transparency.no_eval', 'Aucune évaluation enregistrée pour le moment')}
          </span>
        </div>
      </footer>
    </div>
  );
};

export default TransparencyPage;
