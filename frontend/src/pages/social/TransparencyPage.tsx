import React from 'react';
import { Activity, Zap, Users, Database, Brain, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { useTranslation } from 'react-i18next';

import { TransparencyData } from '../../types';
import { MODEL_COMPARISON } from './transparencyData';
import { TransparencyKpiCard } from './components/TransparencyKpiCard';
import { TransparencyEvolutionChart } from './components/TransparencyEvolutionChart';
import { ModelComparisonCard } from './components/ModelComparisonCard';
import { DriftAuditCard } from './components/DriftAuditCard';
import { EthicsCommitmentsCard } from './components/EthicsCommitmentsCard';
import { SecurityAuditSection } from './components/SecurityAuditSection';
import { LabPage, LabHeader, LAB_BTN_GHOST, AI_INDIGO } from '../labs/components/shared/LabKit';

const TransparencyPage: React.FC = () => {
  const { t } = useTranslation();

  const { data, isLoading } = useQuery<TransparencyData>({
    queryKey: ['transparency'],
    queryFn: () => apiClient('/api/v1/transparency/'),
  });

  if (isLoading)
    return (
      // Même encre de nuit que la page : pas de flash clair pendant le chargement.
      <div className="flex min-h-screen w-full flex-col items-center justify-center bg-[#0B0C10] px-6">
        <div
          className="mb-8 h-16 w-16 animate-spin rounded-full border-4 border-t-transparent"
          style={{ borderColor: AI_INDIGO, borderTopColor: 'transparent' }}
          aria-hidden
        />
        <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#5D7FD3]">
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
    <LabPage>
      <LabHeader
        glyph="透"
        code="Registre · Colophon"
        title="Hub de"
        accent={`${t('social.transparency.title_accent', 'transparence')} IA`}
        lede={t(
          'social.transparency.subtitle',
          "Découvrez comment vos interactions façonnent le cerveau d'Animetix. Nous croyons en une intelligence artificielle ouverte, auditable et alignée sur sa communauté.",
        )}
      />

      {data.model_uptime != null && (
        <div className="-mt-6 mb-14">
          <span className="inline-flex items-center gap-2 rounded-full border border-[#5D7FD3]/30 bg-[#5D7FD3]/10 px-4 py-2 text-[10px] font-black uppercase tracking-[0.2em] text-[#5D7FD3]">
            <Activity className="h-3 w-3" aria-hidden="true" />
            {t(
              'social.transparency.uptime_badge',
              'Fiabilité du modèle : {{pct}}% (réponses sans hallucination)',
              { pct: data.model_uptime },
            )}
          </span>
        </div>
      )}

      <div className="space-y-20">
        {/* Key Performance Indicators */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <TransparencyKpiCard
            icon={<Users className="mb-4 h-8 w-8 text-[#5D7FD3]" aria-hidden="true" />}
            value={(metrics?.total_feedbacks || 0).toLocaleString()}
            label={t('social.transparency.kpi_feedbacks', 'Feedbacks Reçus')}
          />
          <TransparencyKpiCard
            icon={<Database className="mb-4 h-8 w-8 text-[#5D7FD3]" aria-hidden="true" />}
            value={(metrics?.knowledge_nodes || 0).toLocaleString()}
            label={t('social.transparency.kpi_engrams', 'Engrammes Indexés')}
          />
          <TransparencyKpiCard
            icon={<Brain className="mb-4 h-8 w-8 text-[#5D7FD3]" aria-hidden="true" />}
            value={`${(metrics?.community_satisfaction * 100).toFixed(0)}%`}
            label={t('social.transparency.kpi_satisfaction', 'Satisfaction IA')}
          />
          <TransparencyKpiCard
            icon={<Zap className="mb-4 h-8 w-8 text-[#5D7FD3]" aria-hidden="true" />}
            value={metrics?.model_version || 'Champion v2.4'}
            label={t('social.transparency.kpi_version', 'Version Actuelle')}
            valueClassName="text-2xl font-black italic mb-1 uppercase line-clamp-1"
          />
        </div>

        {/* Evolution Chart */}
        <TransparencyEvolutionChart timeline={timeline} />

        {/* SOTA Benchmarks & Embedding Drift */}
        <div className="grid grid-cols-1 gap-12 xl:grid-cols-3">
          <div className="space-y-10 xl:col-span-2">
            <header>
              <h2 className="font-manga text-2xl font-black uppercase italic tracking-tight text-[#F4F1E8] md:text-3xl">
                {t('social.transparency.vs_title_1', 'NOTRE MODÈLE')}{' '}
                <span className="text-[#5D7FD3]">
                  {t('social.transparency.vs_title_2', "VS L'OPEN SOURCE")}
                </span>
              </h2>
              <p className="mt-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#8F94A5]">
                {t(
                  'social.transparency.vs_subtitle',
                  "Le modèle de base d'Animetix face aux meilleurs LLM open source du marché",
                )}
              </p>
            </header>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {MODEL_COMPARISON.map((model, i) => (
                <ModelComparisonCard key={model.model_id} model={model} index={i} />
              ))}
            </div>

            <p className="text-[10px] font-bold uppercase leading-relaxed tracking-widest text-[#8F94A5]">
              {t(
                'social.transparency.vs_footnote',
                'Champion tourne sur Qwen3.5-9B : un modèle compact hébergé sur notre propre GPU, spécialisé anime/manga par fine-tuning DPO continu. Les géants ci-dessus dominent les benchmarks généralistes — notre pari est la spécialisation, pas la taille.',
              )}
            </p>
          </div>

          <div className="space-y-10">
            <header>
              <h2 className="font-manga text-2xl font-black uppercase italic tracking-tight text-[#F4F1E8] md:text-3xl">
                DRIFT <span className="text-[#5D7FD3]">AUDIT</span>
              </h2>
              <p className="mt-2 text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5]">
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

        <div className="grid grid-cols-1 gap-12 lg:grid-cols-2">
          <EthicsCommitmentsCard ethicsScore={data.ethics_score} />
          <SecurityAuditSection ethicsAudit={data.ethics_audit} />
        </div>

        {/* Participation CTA */}
        <section className="rounded-2xl border border-[#5D7FD3]/30 bg-[#5D7FD3]/[0.08] p-10 text-center sm:p-14">
          <h2 className="font-manga mb-6 text-3xl font-black uppercase italic tracking-tighter text-[#F4F1E8] md:text-5xl">
            {t('social.transparency.cta_title', 'Devenez Curateur du Nexus')}
          </h2>
          <p className="mx-auto mb-10 max-w-3xl text-sm leading-relaxed text-[#8F94A5]">
            {t(
              'social.transparency.cta_desc',
              "Chaque interaction avec l'IA renforce la base de connaissance commune. Grâce au protocole DPO (Direct Preference Optimization), vos choix guident l'apprentissage du modèle Champion.",
            )}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/lab/"
              className="font-manga inline-flex items-center justify-center rounded-xl bg-[#5D7FD3] px-8 py-4 text-base font-black uppercase italic text-[#0B0C10] no-underline transition-colors hover:bg-[#4a69b8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
            >
              {t('social.transparency.cta_lab', 'DÉCOUVRIR LE LAB')}
            </Link>
            <Link to="/research/papers/" className={`${LAB_BTN_GHOST} no-underline`}>
              {t('social.transparency.cta_research', 'LA RECHERCHE IA')}
            </Link>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="mt-24 border-t border-[#F4F1E8]/10 pt-10">
        <div className="flex items-center justify-center gap-3 text-[#8F94A5]">
          <Clock className="h-4 w-4" aria-hidden="true" />
          <span className="text-[10px] font-black uppercase tracking-widest">
            {metrics?.last_training
              ? t('social.transparency.last_eval', 'Dernière évaluation : {{date}}', {
                  date: metrics.last_training,
                })
              : t('social.transparency.no_eval', 'Aucune évaluation enregistrée pour le moment')}
          </span>
        </div>
      </footer>
    </LabPage>
  );
};

export default TransparencyPage;
