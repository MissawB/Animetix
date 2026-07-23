import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Plot from '../../components/LazyPlot';
import type * as Plotly from 'plotly.js';
import { Link } from 'react-router-dom';
import { Box, Info, Globe, ArrowRight, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';
import { LabGuide, LAB_LABEL, LAB_CTA } from './components/shared/LabKit';

import { PlotlyEvent } from '../../types';

const LATENT_SELECT =
  'w-full cursor-pointer rounded-lg border border-[#F4F1E8]/15 bg-[#0F1016] px-3 py-2 text-[10px] font-black uppercase text-[#F4F1E8] outline-none transition-colors focus:border-[#FDB913]';

interface LatentPoint {
  x: number;
  y: number;
  z: number;
  title?: string;
  name?: string;
  cluster?: number;
  image?: string;
  category?: string;
  year?: string;
  description?: string;
}

const LatentSpacePage: React.FC = () => {
  const { t } = useTranslation();
  const [media, setMedia] = useState<string>('anime');
  const [type, setType] = useState<string>('thematic');
  const [selectedItem, setSelectedItem] = useState<LatentPoint | null>(null);

  const { data, isLoading } = useQuery<LatentPoint[]>({
    queryKey: ['latent-space', media, type],
    queryFn: () => apiClient(`/api/v1/latent-space/?media=${media}&type=${type}`),
  });

  const handlePointClick = (event: PlotlyEvent) => {
    if (event.points && event.points[0]) {
      const item = event.points[0].customdata as LatentPoint;
      if (item) {
        setSelectedItem(item);
      } else {
        const pointIndex = event.points[0].pointNumber;
        if (data && data[pointIndex]) {
          setSelectedItem(data[pointIndex]);
        }
      }
    }
  };

  const uniqueCategories = data
    ? Array.from(new Set(data.map((d) => d.category || d.cluster || 'Unknown')))
    : [];
  const getCategoryIndex = (category: string | number | undefined) =>
    uniqueCategories.indexOf(category || 'Unknown');

  const plotData: Array<Partial<Plotly.Data>> = data
    ? [
        {
          x: data.map((d) => d.x),
          y: data.map((d) => d.y),
          z: data.map((d) => d.z),
          customdata: data,
          mode: 'markers',
          type: 'scatter3d',
          text: data.map((d) => d.title || d.name),
          hoverinfo: 'text',
          marker: {
            size: 4,
            color: data.map((d) => getCategoryIndex(d.category || d.cluster)),
            cmin: 0,
            cmax: Math.max(1, uniqueCategories.length - 1),
            colorscale: 'Plasma', // More galactic colorscale (dark purple to bright yellow)
            opacity: 0.85,
            line: {
              color: 'rgba(255, 255, 255, 0.3)',
              width: 0.5,
            },
          },
        } as unknown as Partial<Plotly.Data>,
      ]
    : [];

  return (
    <AnimatedPage>
      <div className="relative flex h-[calc(100vh-64px)] w-full flex-col overflow-hidden bg-[#0B0C10] text-[#F4F1E8] lg:flex-row">
        {/* LEFT PANEL: 3D PLOT (Takes full remaining space) */}
        <div className="relative h-full flex-grow overflow-hidden bg-[#0B0C10]">
          {/* OVERLAY CONTROLS (Top Left) */}
          <div className="pointer-events-none absolute left-6 top-6 z-20">
            <div className="pointer-events-auto max-w-[220px] rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10]/85 p-5 backdrop-blur-md">
              <p className="text-[9px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                Protocole · Latent
              </p>
              <h1 className="font-manga mt-2 text-2xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8]">
                Espace <span className="text-[#E8442B]">latent</span>
              </h1>

              <div className="mt-6 flex flex-col gap-3">
                <div className="flex flex-col gap-1.5">
                  <span className={LAB_LABEL}>{t('labs.latent.domain', 'Domaine')}</span>
                  <select
                    value={media}
                    onChange={(e) => {
                      setMedia(e.target.value);
                      setSelectedItem(null);
                    }}
                    className={LATENT_SELECT}
                  >
                    <option value="anime">Anime</option>
                    <option value="manga">Manga</option>
                    <option value="character">{t('labs.latent.characters', 'Personnages')}</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <span className={LAB_LABEL}>
                    {t('labs.latent.analysis_axis', "Axe d'analyse")}
                  </span>
                  <select
                    value={type}
                    onChange={(e) => {
                      setType(e.target.value);
                      setSelectedItem(null);
                    }}
                    className={LATENT_SELECT}
                  >
                    <option value="thematic">{t('labs.latent.thematic', 'Thématique')}</option>
                    <option value="visual">{t('labs.latent.visual', 'Visuel')}</option>
                    <option value="scenario">{t('labs.latent.scenario', 'Scénario')}</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* LOADING STATE */}
          {isLoading && (
            <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-[#0B0C10]/85 backdrop-blur-sm">
              <Loader2 className="mb-6 h-12 w-12 animate-spin text-[#FDB913]" aria-hidden="true" />
              <span className="text-xs font-black uppercase tracking-[0.3em] text-[#8F94A5]">
                {t('labs.latent.loading_projection', 'Projection Dimensionnelle...')}
              </span>
            </div>
          )}

          {/* PLOT CONTAINER */}
          <div className="h-full w-full cursor-crosshair">
            <Plot
              data={plotData as Plotly.Data[]}
              onClick={handlePointClick}
              layout={{
                autosize: true,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                scene: {
                  xaxis: { visible: false },
                  yaxis: { visible: false },
                  zaxis: { visible: false },
                  camera: {
                    eye: { x: 1.8, y: 1.8, z: 1.8 },
                  },
                },
                margin: { l: 0, r: 0, b: 0, t: 0 },
                hovermode: 'closest',
                font: { family: 'Montserrat', color: '#fff' },
              }}
              config={{
                responsive: true,
                displayModeBar: false,
                scrollZoom: true,
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>

        {/* RIGHT PANEL: ANALYSIS CARD (Docked to the right) */}
        <div className="relative z-20 flex h-full flex-col border-l border-[#F4F1E8]/10 bg-[#0F1016] lg:w-[400px]">
          <AnimatePresence mode="wait">
            {selectedItem ? (
              <motion.div
                key={selectedItem.title || selectedItem.name}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex h-full flex-col"
              >
                {/* Item Image Header */}
                <div className="relative h-64 w-full shrink-0 overflow-hidden bg-[#0B0C10]">
                  {selectedItem.image ? (
                    <img
                      src={selectedItem.image}
                      alt={selectedItem.title || selectedItem.name}
                      className="h-full w-full object-cover opacity-60"
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center">
                      <Box className="h-12 w-12 text-[#8F94A5]" aria-hidden="true" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-[#0F1016] via-[#0F1016]/40 to-transparent"></div>

                  <div className="absolute bottom-6 left-6 right-6">
                    <span className="mb-3 inline-block rounded-full bg-[#E8442B] px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[#F4F1E8]">
                      {selectedItem.category || t('labs.latent.ia_vector', 'Vecteur IA')}
                    </span>
                    <h2 className="font-manga text-2xl font-black uppercase italic leading-tight tracking-tighter text-[#F4F1E8]">
                      {selectedItem.title || selectedItem.name}
                    </h2>
                  </div>
                </div>

                {/* Analysis Content */}
                <div className="custom-scrollbar flex-grow overflow-y-auto p-6 text-[#F4F1E8]">
                  <div className="mb-6 grid grid-cols-2 gap-4">
                    <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 text-center">
                      <span className="mb-1 block text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {t('labs.latent.year', 'Année')}
                      </span>
                      <span className="font-manga text-sm font-black italic text-[#FDB913]">
                        {selectedItem.year || 'N/A'}
                      </span>
                    </div>
                    <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 text-center">
                      <span className="mb-1 block text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {t('labs.latent.cluster_id', 'Cluster ID')}
                      </span>
                      <span className="font-manga text-sm font-black italic text-[#FDB913]">
                        #{selectedItem.cluster || getCategoryIndex(selectedItem.category)}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h4 className="mb-4 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-[#FDB913]">
                        <Info className="h-3 w-3" aria-hidden="true" />{' '}
                        {t('labs.latent.proximity_analysis', 'Analyse de Proximité')}
                      </h4>
                      <p className="text-sm leading-relaxed text-[#8F94A5]">
                        {t(
                          'labs.latent.proximity_desc',
                          "Cette œuvre est positionnée dans l'espace selon ses caractéristiques {{type}}. Sa position vectorielle indique une forte affinité sémantique avec les clusters environnants.",
                          { type: type },
                        )}
                      </p>
                    </div>

                    <div className="border-t border-[#F4F1E8]/10 pt-6">
                      <Link
                        to={`/search/?q=${encodeURIComponent(selectedItem.title || selectedItem.name || '')}`}
                        className={`${LAB_CTA} no-underline`}
                      >
                        {t('labs.latent.explore_relations', 'Explorer les Relations')}{' '}
                        <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
                      </Link>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="flex h-full flex-col items-center justify-center p-10 text-center">
                <div className="mb-8 flex h-24 w-24 items-center justify-center rounded-full border border-[#F4F1E8]/10 bg-[#0B0C10]">
                  <Globe className="h-10 w-10 text-[#FDB913]" aria-hidden="true" />
                </div>
                <h3 className="font-manga mb-4 text-xl font-black uppercase italic tracking-tighter text-[#F4F1E8]">
                  {t('labs.latent.ready_explore', "Prêt pour l'exploration ?")}
                </h3>
                <p className="max-w-xs text-sm leading-relaxed text-[#8F94A5]">
                  {t(
                    'labs.latent.click_prompt',
                    "Cliquez sur un point lumineux dans l'espace pour l'analyser",
                  )}
                </p>
              </div>
            )}
          </AnimatePresence>

          {/* Bottom Footer Info */}
          <div className="mt-auto border-t border-[#F4F1E8]/10 bg-[#0B0C10] p-6">
            <Link
              to="/graph/map/"
              className="flex items-center justify-center gap-3 text-[9px] font-black uppercase tracking-[0.2em] text-[#8F94A5] no-underline transition-colors hover:text-[#FDB913]"
            >
              <Globe className="h-3 w-3" aria-hidden="true" />{' '}
              {t('labs.latent.toggle_atlas', 'Basculer vers la Vue Atlas')}
            </Link>
          </div>
        </div>
      </div>

      {/* Guide & Protocole */}
      <div className="bg-[#0B0C10] px-4 pb-16 text-[#F4F1E8] sm:px-6">
        <div className="mx-auto max-w-7xl">
          <LabGuide
            steps={[
              {
                title: 'Repère les points',
                body: t(
                  'labs.latent.guide_concept_desc',
                  "Chaque point lumineux est un anime, un manga ou un personnage. Sa position reflète la façon dont l'IA comprend l'œuvre : deux points proches se ressemblent.",
                ),
              },
              {
                title: "Navigue dans l'espace",
                body: t(
                  'labs.latent.guide_nav_desc',
                  "Faites pivoter la carte à la souris, zoomez à la molette, puis cliquez sur un point pour ouvrir sa fiche d'analyse dans le panneau de droite.",
                ),
              },
              {
                title: "Change d'angle",
                body: t(
                  'labs.latent.guide_filters_desc',
                  "Changez le domaine (anime, manga, personnages) et l'axe d'analyse (thématique, visuel, scénario) pour recharger la carte sous un autre angle.",
                ),
              },
            ]}
            note={`${t(
              'labs.latent.guide_footer_1',
              'Visualisation exploratoire du catalogue : des embeddings haute dimension sont projetés en 3 dimensions puis rendus en nuage de points interactif (Plotly scatter3d).',
            )} ${t(
              'labs.latent.guide_footer_2',
              'La proximité spatiale traduit la similarité sémantique des vecteurs ; les couleurs regroupent les clusters ou catégories détectés.',
            )}`}
          />
        </div>
      </div>
    </AnimatedPage>
  );
};

export default LatentSpacePage;
