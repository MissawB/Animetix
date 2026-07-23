import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Brain, Fingerprint, GitBranch, ArrowRight, Activity, Zap } from 'lucide-react';
import { LabPage, LabHeader } from './components/shared/LabKit';

const cognitiveModules = [
  {
    id: 'archetype',
    title: 'Archetype Nexus',
    sub: 'Convergence synaptique',
    desc: "Visualisez votre position dans l'espace latent des fans et la convergence de vos traits psychographiques.",
    icon: Brain,
    url: '/social/archetype-nexus/',
    badge: 'Latent Space',
  },
  {
    id: 'memory',
    title: 'Neuro-Memory',
    sub: 'Empreinte sémantique',
    desc: "Gérez l'empreinte sémantique que vous laissez sur l'IA et auditez vos vecteurs de préférence en temps réel.",
    icon: Fingerprint,
    url: '/social/neuro-memory/',
    badge: 'Cognitive Audit',
  },
  {
    id: 'simulator',
    title: 'Counterfactual Simulator',
    sub: 'Optimisation de timeline',
    desc: 'Explorez les mondes possibles de vos interactions et calculez le regret contrefactuel minimum.',
    icon: GitBranch,
    url: '/search/counterfactual/',
    badge: 'Game Theory',
  },
];

const CognitionHubPage: React.FC = () => {
  const { t } = useTranslation();

  const cognitiveStats = [
    {
      icon: Activity,
      label: 'Résolution CFR',
      value: t('labs.cognition.regret_version', 'Regret Minimizer v2'),
    },
    {
      icon: Brain,
      label: 'Cartographie latente',
      value: t('labs.cognition.high_dim_projection', 'High-Dim Projection'),
    },
    {
      icon: Zap,
      label: 'Synchronisation synaptique',
      value: t('labs.cognition.real_time_imprint', 'Real-time Imprint'),
    },
  ];

  return (
    <LabPage>
      <LabHeader
        code="Annuaire · Cognition"
        title="Cognition"
        accent="Core"
        lede={t(
          'labs.cognition.hero_title',
          "Fusion de l'identité numérique, de la mémoire artificielle et de la simulation de futurs possibles.",
        )}
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {cognitiveModules.map((module) => (
          <Link key={module.id} to={module.url} className="group block h-full no-underline">
            <article className="flex h-full flex-col justify-between rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 transition-all duration-300 group-hover:-translate-y-1 group-hover:border-[#FDB913]/60">
              <div>
                <div className="mb-8 flex items-start justify-between gap-4">
                  <span className="inline-flex rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3.5 text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
                    <module.icon className="h-7 w-7" aria-hidden="true" />
                  </span>
                  <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                    {module.badge}
                  </span>
                </div>
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#E8442B]">
                  {module.sub}
                </p>
                <h3 className="font-manga mt-2 text-2xl font-black uppercase italic tracking-tight text-[#F4F1E8]">
                  {module.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-[#8F94A5]">
                  {t(`labs.cognition.${module.id}_desc`, module.desc)}
                </p>
              </div>

              <div className="mt-8 border-t border-[#F4F1E8]/10 pt-5">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#FDB913] opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                  Ouvrir le protocole{' '}
                  <ArrowRight className="ml-1.5 inline h-3 w-3" aria-hidden="true" />
                </span>
              </div>
            </article>
          </Link>
        ))}
      </div>

      {/* Mesures cognitives */}
      <div className="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {cognitiveStats.map((stat) => (
          <div
            key={stat.label}
            className="flex items-center gap-6 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] px-6 py-5"
          >
            <span className="inline-flex rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3.5 text-[#FDB913]">
              <stat.icon className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <p className="text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
                {stat.label}
              </p>
              <p className="font-manga mt-1.5 text-lg font-black uppercase italic leading-none text-[#F4F1E8]">
                {stat.value}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Note de bas de page */}
      <footer className="mt-24 border-t border-[#F4F1E8]/10 pt-12 text-center">
        <p className="mx-auto max-w-3xl text-sm leading-relaxed text-[#8F94A5]">
          {t(
            'labs.cognition.guide_footer_1',
            "Le Cognition Hub unifie les vecteurs d'identité et de décision.",
          )}{' '}
          <br />
          {t(
            'labs.cognition.guide_footer_2',
            "Les données traitées ici servent à affiner les modèles de recommandation neuro-symboliques sans compromettre l'étanchéité de la vie privée numérique.",
          )}
        </p>
      </footer>
    </LabPage>
  );
};

export default CognitionHubPage;
