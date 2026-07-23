import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Book, Frame, Headphones, FlaskConical as Flask } from 'lucide-react';
import { LabPage, LabHeader } from './components/shared/LabKit';
import { LabListOverlay } from '../../features/labs/components/LabListOverlay';

const categoryLabs: Record<string, { id: string; title: string; url: string; desc: string }[]> = {
  narrative: [
    {
      id: 'forge',
      title: 'Forge de Réalité',
      url: '/forge/',
      desc: 'Fusionnez univers et scénarios.',
    },
    {
      id: 'vsbattle',
      title: 'Arena Ultimatum',
      url: '/game/vsbattle/',
      desc: "Duels trans-dimensionnels arbitrés par l'IA.",
    },
  ],
  visual: [
    { id: 'manga', title: 'Manga Lab', url: '/lab/manga/', desc: 'Rendu Manga par IA.' },
    { id: 'video', title: 'Video Lab', url: '/lab/video/', desc: 'Analyse et indexation vidéo.' },
    {
      id: 'nexus',
      title: 'Visual Nexus',
      url: '/lab/visual-nexus/',
      desc: "Exploration d'embeddings visuels.",
    },
    {
      id: 'reconstruction',
      title: 'Cinematic Reconstruction',
      url: '/lab/cinematic/',
      desc: '3D de scènes animées.',
    },
  ],
  audio: [
    { id: 'audio', title: 'Audio Lab', url: '/lab/audio/', desc: 'Clonage vocal et synthèse.' },
    {
      id: 'soundscape',
      title: 'Soundscape Lab',
      url: '/lab/soundscape/',
      desc: "Génération d'ambiances sonores.",
    },
    {
      id: 'speech',
      title: 'Speech-to-Speech',
      url: '/lab/speech-to-speech/',
      desc: 'Transformation vocale temps-réel.',
    },
  ],
  experimental: [
    {
      id: 'singularity',
      title: 'Singularity Hub',
      url: '/lab/',
      desc: 'Accès aux modules de recherche Omega.',
    },
  ],
};

const ForgeHubPage: React.FC = () => {
  const { t } = useTranslation();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = [
    { id: 'narrative', icon: Book },
    { id: 'visual', icon: Frame },
    { id: 'audio', icon: Headphones },
    { id: 'experimental', icon: Flask },
  ];

  const translatedCategoryLabs = useMemo(() => {
    if (!selectedCategory) return [];
    const labs = categoryLabs[selectedCategory] || [];
    return labs.map((lab) => ({
      ...lab,
      title: t(`forge_hub.labs.${lab.id}.title`, lab.title),
      desc: t(`forge_hub.labs.${lab.id}.desc`, lab.desc),
    }));
  }, [selectedCategory, t]);

  return (
    <LabPage>
      <LabHeader
        code="Annuaire · Forge"
        title={t('forge_hub.title').split(' ')[0]}
        accent={t('forge_hub.title').split(' ').slice(1).join(' ')}
        lede={t('forge_hub.description')}
      />

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {categories.map((cat) => (
          <button
            key={cat.id}
            type="button"
            onClick={() => setSelectedCategory(cat.id)}
            aria-label={t(`forge_hub.categories.${cat.id}.title`)}
            className="group flex h-full cursor-pointer flex-col rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 text-left transition-all duration-300 hover:-translate-y-1 hover:border-[#FDB913]/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
          >
            <span className="mb-8 inline-flex w-fit rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3.5 text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
              <cat.icon className="h-7 w-7" aria-hidden="true" />
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#E8442B]">
              {t(`forge_hub.categories.${cat.id}.sub`)}
            </span>
            <h2 className="font-manga mt-2 text-2xl font-black uppercase italic tracking-tight text-[#F4F1E8]">
              {t(`forge_hub.categories.${cat.id}.title`)}
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-[#8F94A5]">
              {t(`forge_hub.categories.${cat.id}.desc`)}
            </p>
          </button>
        ))}
      </div>

      <LabListOverlay
        category={selectedCategory}
        labs={translatedCategoryLabs}
        onClose={() => setSelectedCategory(null)}
      />
    </LabPage>
  );
};

export default ForgeHubPage;
