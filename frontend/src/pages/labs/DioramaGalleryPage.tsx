import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Maximize2,
  Trash2,
  Share2,
  ArrowLeft,
  Sparkles,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_BTN_GHOST,
} from './components/shared/LabKit';

interface Diorama {
  id: string;
  title: string;
  type: 'SGS' | 'DCS';
  preview_url: string;
  created_at: string;
  point_count: number;
  tags: string[];
}

const DioramaGalleryPage: React.FC = () => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');

  // Mock Data
  const mockDioramas: Diorama[] = [
    {
      id: '1',
      title: 'La Forge de Guts',
      type: 'SGS',
      preview_url:
        'https://images.unsplash.com/photo-1614850523296-d8c1af93d400?auto=format&fit=crop&q=80&w=800',
      created_at: '2026-06-10T14:30:00Z',
      point_count: 1250000,
      tags: ['Berserk', 'Architecture', 'Dark Fantasy'],
    },
    {
      id: '2',
      title: 'Neo-Tokyo Rooftop',
      type: 'DCS',
      preview_url:
        'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&q=80&w=800',
      created_at: '2026-06-11T09:15:00Z',
      point_count: 5400000,
      tags: ['Cyberpunk', 'Environment', 'Dynamic'],
    },
    {
      id: '3',
      title: 'Forêt de Totoro',
      type: 'SGS',
      preview_url:
        'https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?auto=format&fit=crop&q=80&w=800',
      created_at: '2026-06-12T18:45:00Z',
      point_count: 850000,
      tags: ['Ghibli', 'Nature', 'Atmospheric'],
    },
  ];

  const filteredDioramas = mockDioramas.filter(
    (d) =>
      d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase())),
  );

  return (
    <LabPage>
      <Link
        to="/lab/spatial/"
        className="group relative z-10 mb-6 inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8]"
      >
        <ArrowLeft
          className="h-3 w-3 transition-transform group-hover:-translate-x-1"
          aria-hidden="true"
        />
        {t('labs.diorama.back_to_spatial', 'Retour au Lab Spatial')}
      </Link>

      <LabHeader
        code="Protocole · Diorama"
        title={t('labs.diorama.gallery_title_part1', 'Galerie des')}
        accent={t('labs.diorama.gallery_title_part2', 'Dioramas')}
        lede={t(
          'labs.diorama.subtitle',
          'Visualisez vos reconstructions volumétriques 3D générées par IA',
        )}
      />

      {/* Barre de recherche */}
      <div className="mb-10 flex flex-col gap-2 sm:max-w-sm">
        <label htmlFor="diorama-search" className={LAB_LABEL}>
          Filtrer la galerie
        </label>
        <input
          id="diorama-search"
          type="text"
          placeholder={t('labs.diorama.search_placeholder', 'Rechercher par titre ou tag…')}
          aria-label={t('labs.diorama.search_aria', 'Rechercher une reconstruction')}
          className={LAB_INPUT}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Grille */}
      {filteredDioramas.length > 0 ? (
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          {filteredDioramas.map((diorama) => (
            <article
              key={diorama.id}
              className="group overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] transition-all duration-500 hover:-translate-y-1 hover:border-[#FDB913]/40"
            >
              {/* Aperçu */}
              <div className="relative aspect-video overflow-hidden">
                <img
                  src={diorama.preview_url}
                  alt={diorama.title}
                  className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
                  loading="lazy"
                  decoding="async"
                />
                <div
                  className="absolute inset-0 bg-gradient-to-t from-[#0B0C10] via-transparent to-transparent opacity-60"
                  aria-hidden
                />

                <span
                  className={`absolute left-4 top-4 rounded-full px-3 py-1 text-[10px] font-black uppercase tracking-widest ${
                    diorama.type === 'SGS'
                      ? 'bg-[#FDB913] text-[#0B0C10]'
                      : 'bg-[#E8442B] text-[#F4F1E8]'
                  }`}
                >
                  {diorama.type === 'SGS' ? 'Static' : 'Dynamic'}
                </span>

                <div className="absolute inset-0 flex items-center justify-center bg-[#0B0C10]/50 opacity-0 backdrop-blur-[2px] transition-opacity group-hover:opacity-100">
                  <button
                    type="button"
                    className="flex h-14 w-14 cursor-pointer items-center justify-center rounded-full border-none bg-[#E8442B] text-[#F4F1E8] transition-colors hover:bg-[#c93a24]"
                    aria-label={`Ouvrir ${diorama.title}`}
                  >
                    <Maximize2 className="h-6 w-6" aria-hidden="true" />
                  </button>
                </div>
              </div>

              {/* Contenu */}
              <div className="p-6">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <h3 className="font-manga line-clamp-1 text-xl font-black uppercase italic tracking-tighter text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
                    {diorama.title}
                  </h3>
                  <div className="flex flex-none items-center gap-1 text-[9px] font-black text-[#8F94A5]">
                    <Clock className="h-3 w-3" aria-hidden="true" />
                    {new Date(diorama.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="mb-6 flex flex-wrap gap-2">
                  {diorama.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded border border-[#F4F1E8]/10 px-2 py-1 text-[9px] font-black uppercase tracking-widest text-[#8F94A5]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-3 border-t border-[#F4F1E8]/10 pt-4">
                  <div className="flex flex-col">
                    <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                      {t('labs.diorama.complexity', 'Complexité')}
                    </span>
                    <span className="flex items-center gap-1 text-[10px] font-bold text-[#FDB913]">
                      <Sparkles className="h-3 w-3" aria-hidden="true" />
                      {(diorama.point_count / 1000000).toFixed(1)}M Points
                    </span>
                  </div>
                  <div className="flex items-center justify-end gap-2">
                    <button
                      className="cursor-pointer rounded-lg border-none bg-transparent p-2 text-[#8F94A5] transition-colors hover:bg-[#F4F1E8]/5 hover:text-[#F4F1E8]"
                      aria-label={`Partager ${diorama.title}`}
                    >
                      <Share2 className="h-4 w-4" aria-hidden="true" />
                    </button>
                    <button
                      className="cursor-pointer rounded-lg border-none bg-transparent p-2 text-[#8F94A5] transition-colors hover:bg-[#E8442B]/10 hover:text-[#E8442B]"
                      aria-label={`Supprimer ${diorama.title}`}
                    >
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="space-y-8">
          <LabEmpty
            icon={<Box className="h-20 w-20" aria-hidden="true" />}
            title={t('labs.diorama.no_creations_title', 'Aucune création trouvée')}
            hint={t(
              'labs.diorama.no_creations_desc',
              "Vous n'avez pas encore généré de dioramas dans le Nexus.",
            )}
          />
          <div className="flex justify-center">
            <Link to="/lab/spatial/" className={`${LAB_BTN_GHOST} no-underline`}>
              {t('labs.diorama.btn_create_first', 'Créer mon premier diorama')}
            </Link>
          </div>
        </div>
      )}

      {/* Export VR */}
      <div className="mt-16">
        <LabPanel title={t('labs.diorama.export_vr', 'Exporter en VR')} corner=".PLY / .USDZ">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <p className="max-w-xl text-sm leading-relaxed text-[#8F94A5]">
              {t(
                'labs.diorama.download_format_note',
                'Téléchargez vos modèles au format .PLY ou .USDZ pour visionnage externe.',
              )}
            </p>
            <button type="button" className={LAB_BTN_GHOST}>
              <ExternalLink className="h-4 w-4" aria-hidden="true" />{' '}
              {t('labs.diorama.btn_sdk_vr', 'Accéder au SDK VR')}
            </button>
          </div>
        </LabPanel>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Génère au Lab Spatial',
            body: 'Les dioramas naissent dans le Nexus spatial : lance une reconstruction là-bas, elle rejoint automatiquement cette galerie.',
          },
          {
            title: 'Parcours la galerie',
            body: 'Filtre par titre ou par tag. Chaque carte indique le type de splatting (static ou dynamic), la date et la densité de points de la scène.',
          },
          {
            title: 'Exporte en VR',
            body: 'Télécharge tes modèles au format .PLY ou .USDZ pour les visionner dans un casque ou les importer dans un moteur externe.',
          },
        ]}
        note="Chaque diorama est une reconstruction volumétrique générée par IA (Gaussian Splatting). Le nombre de points mesure la densité de la scène : plus il est élevé, plus la géométrie est fine — et plus le fichier exporté est lourd."
      />
    </LabPage>
  );
};

export default DioramaGalleryPage;
