import React from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { labs, creativeLabs, cognitionLabs, type LabEntry } from './labHubData';
import { LabHubCard } from './components/LabHubCard';
import { LabHubCompactCard } from './components/LabHubCompactCard';
import { LabHubSectionHeader } from './components/LabHubSectionHeader';

/** Overrides each entry's title/desc with its i18n translation (falling back to
 *  the bundled French copy), memoised against the active language. */
const useTranslatedLabs = (entries: LabEntry[]): LabEntry[] => {
  const { t } = useTranslation();
  return React.useMemo(
    () =>
      entries.map((lab) => ({
        ...lab,
        title: t(`lab_hub.labs.${lab.id}.title`, lab.title),
        desc: t(`lab_hub.labs.${lab.id}.desc`, lab.desc),
      })),
    [entries, t],
  );
};

const LabHubPage: React.FC = () => {
  const { t } = useTranslation();
  const translatedLabs = useTranslatedLabs(labs);
  const translatedCreativeLabs = useTranslatedLabs(creativeLabs);
  const translatedCognitionLabs = useTranslatedLabs(cognitionLabs);

  return (
    <div className="min-h-screen w-full bg-[#0a0a12] text-white pb-20">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 py-16 relative z-10">
          {/* Header Ultra-Moderne */}
          <header className="mb-24 relative">
            <div className="absolute -top-32 -left-32 w-[600px] h-[600px] bg-red-600/5 blur-[150px] rounded-full -z-10" />

            <div className="flex flex-col md:flex-row justify-between items-end gap-12">
              <div className="max-w-3xl">
                <h1 className="text-8xl font-black italic manga-font tracking-tighter uppercase mb-6 leading-[0.9]">
                  SINGULARITY <span className="text-red-600 text-glow">LABS</span>
                </h1>
                <p className="text-2xl font-bold opacity-30 uppercase tracking-[0.2em] leading-relaxed">
                  {t(
                    'lab_hub.subtitle',
                    "Explorez la frontière entre l'IA générative et la cognition pure.",
                  )}
                </p>
              </div>
            </div>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-24">
            {translatedLabs.map((lab) => (
              <LabHubCard key={lab.id} lab={lab} />
            ))}
          </div>

          {/* Creative Forge Section */}
          <LabHubSectionHeader
            title="FORGE"
            accent={t('lab_hub.section_creative', 'CRÉATIVE')}
            accentColor="text-orange-500"
            dividerFrom="from-orange-500/50"
            hubUrl="/forge-hub/"
            hubLabel={t('lab_hub.btn_creative_hub', 'ACCÉDER AU HUB COMPLET')}
            hubLinkColor="text-orange-500"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-24">
            {translatedCreativeLabs.map((lab) => (
              <LabHubCompactCard
                key={lab.id}
                lab={lab}
                hoverBorderClass="hover:border-orange-500/30"
              />
            ))}
          </div>

          {/* Cognition Core Section */}
          <LabHubSectionHeader
            title="COGNITION"
            accent={t('lab_hub.section_cognition', 'CORE')}
            accentColor="text-purple-600"
            dividerFrom="from-purple-600/50"
            hubUrl="/cognition-hub/"
            hubLabel={t('lab_hub.btn_cognition_hub', 'ACCÉDER AU HUB COMPLET')}
            hubLinkColor="text-purple-400"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-24">
            {translatedCognitionLabs.map((lab) => (
              <LabHubCompactCard
                key={lab.id}
                lab={lab}
                hoverBorderClass="hover:border-purple-600/30"
              />
            ))}
          </div>

          {/* Alpha Footer */}
          <footer className="mt-32 pt-16 border-t border-white/5 text-center">
            <p className="text-sm font-bold uppercase tracking-[0.15em] opacity-70 italic max-w-4xl mx-auto leading-relaxed">
              {t(
                'lab_hub.footer_1',
                "Les Singularity Labs regroupent les fonctionnalités expérimentales d'Animetix : des outils d'IA générative et cognitive appliqués à l'univers anime & manga.",
              )}{' '}
              <br />
              {t(
                'lab_hub.footer_2',
                'Génération de lore, doublage et synthèse vocale, analyse vidéo, reconstruction 3D, moteurs de raisonnement — chaque module est un prototype de recherche en évolution constante.',
              )}
            </p>
          </footer>
        </div>
      </AnimatedPage>
    </div>
  );
};

export default LabHubPage;
