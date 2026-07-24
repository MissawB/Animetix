import React from 'react';
import { useTranslation } from 'react-i18next';
import { LabPage, LabHeader } from './components/shared/LabKit';
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

/** Les clés i18n de section portent le nom complet ("FORGE CRÉATIVE") ;
 *  on encre le premier mot en papier et le reste en vermillon. */
const splitSectionTitle = (full: string): [string, string] => {
  const [first, ...rest] = full.split(' ');
  return [first, rest.join(' ')];
};

/** Indices des « unes » (col-span-2) choisis pour que la grille 3 colonnes
 *  tuile sans trou : (2+1) / (1+2) / (1+1+1) / (2+1). */
const FEATURED_INDICES = new Set([0, 3, 7]);

const LabHubPage: React.FC = () => {
  const { t } = useTranslation();
  const translatedLabs = useTranslatedLabs(labs);
  const translatedCreativeLabs = useTranslatedLabs(creativeLabs);
  const translatedCognitionLabs = useTranslatedLabs(cognitionLabs);
  const [creativeTitle, creativeAccent] = splitSectionTitle(
    t('lab_hub.section_creative', 'FORGE CRÉATIVE'),
  );
  const [cognitionTitle, cognitionAccent] = splitSectionTitle(
    t('lab_hub.section_cognition', 'COGNITION CORE'),
  );

  return (
    <LabPage>
      <LabHeader
        code="Annuaire · Protocoles"
        title="Singularity"
        accent="Labs"
        lede={t(
          'lab_hub.subtitle',
          "Explorez la frontière entre l'IA générative et la cognition pure.",
        )}
      />

      <div className="mb-24 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {translatedLabs.map((lab, idx) => (
          <LabHubCard key={lab.id} lab={lab} featured={FEATURED_INDICES.has(idx)} />
        ))}
      </div>

      {/* Section Forge créative */}
      <LabHubSectionHeader
        title={creativeTitle}
        accent={creativeAccent}
        hubUrl="/lab/forge-hub/"
        hubLabel={t('lab_hub.btn_creative_hub', 'ACCÉDER AU HUB COMPLET')}
        ink="kin"
      />

      <div className="mb-24 grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
        {translatedCreativeLabs.map((lab) => (
          <LabHubCompactCard key={lab.id} lab={lab} ink="kin" />
        ))}
      </div>

      {/* Section Cognition core */}
      <LabHubSectionHeader
        title={cognitionTitle}
        accent={cognitionAccent}
        hubUrl="/lab/cognition-hub/"
        hubLabel={t('lab_hub.btn_cognition_hub', 'ACCÉDER AU HUB COMPLET')}
        ink="ai"
      />

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
        {translatedCognitionLabs.map((lab) => (
          <LabHubCompactCard key={lab.id} lab={lab} ink="ai" />
        ))}
      </div>

      {/* Note de bas de page */}
      <footer className="mt-24 border-t border-[#F4F1E8]/10 pt-12 text-center">
        <p className="mx-auto max-w-3xl text-sm leading-relaxed text-[#8F94A5]">
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
    </LabPage>
  );
};

export default LabHubPage;
