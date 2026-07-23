import React from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, Image as ImageIcon, Heart, Share2, Film, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { SearchItem } from '../../types';
import type { FusionResponse, FusionStatus } from '../../features/labs/services/forgeService';

interface ForgeResultDisplayProps {
  status: FusionStatus;
  fusionData: FusionResponse | null;
  itemA: SearchItem | null;
  itemB: SearchItem | null;
  artStyle: string;
  chaosLevel: number;
  resetForge: () => void;
}

export const ForgeResultDisplay: React.FC<ForgeResultDisplayProps> = ({
  status,
  fusionData,
  itemA,
  itemB,
  artStyle,
  chaosLevel,
  resetForge,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in zoom-in-95 duration-700">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          <div className="lg:col-span-5 relative group">
            <div className="absolute -inset-4 bg-gradient-to-br from-[#FDB913]/20 to-[#E8442B]/20 blur-3xl rounded-3xl opacity-60 group-hover:opacity-100 transition-opacity" />
            <div className="relative overflow-hidden rounded-2xl shadow-2xl ring-1 ring-[#F4F1E8]/15 transform -rotate-1 hover:rotate-0 transition-transform duration-500">
              <span
                className="absolute -inset-1 translate-x-3 translate-y-3 rounded-2xl border-2 border-[#E8442B]/50 pointer-events-none"
                aria-hidden
              />
              {status.image_url ? (
                <img
                  src={status.image_url}
                  className="w-full aspect-[3/4] object-cover scale-105 group-hover:scale-100 transition-transform duration-700"
                  alt={t('games.forge.result_image_alt', 'Fusion')}
                  loading="lazy"
                  decoding="async"
                />
              ) : (
                <div className="w-full aspect-[3/4] bg-[#0F1016] flex flex-col items-center justify-center gap-4">
                  <ImageIcon className="w-20 h-20 text-[#F4F1E8]/10" />
                  <p className="text-xs font-black text-[#8F94A5] uppercase tracking-widest">
                    {t('games.forge.image_not_generated', 'Image non générée')}
                  </p>
                </div>
              )}

              <div className="absolute top-8 left-8 flex flex-col gap-2">
                <span className="bg-black/80 backdrop-blur-md text-white text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-tighter">
                  {t('games.forge.style_label', 'Style:')} {artStyle}
                </span>
                <span className="bg-[#FDB913] text-black text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-tighter shadow-lg">
                  {t('games.forge.chaos_label', 'Chaos:')} {chaosLevel}%
                </span>
              </div>
            </div>

            <div className="absolute -bottom-8 -right-4 bg-[#0F1016] p-6 rounded-2xl shadow-2xl border border-[#F4F1E8]/10 max-w-[280px] transform rotate-3">
              <div className="flex items-center gap-3 mb-2">
                <Sparkles className="w-5 h-5 text-[#FDB913]" />
                <span className="text-[10px] font-black text-[#8F94A5] uppercase tracking-widest">
                  {t('games.forge.new_archetype', 'NOUVEL ARCHÉTYPE')}
                </span>
              </div>
              <h3 className="text-xl font-black italic manga-font leading-tight text-[#F4F1E8]">
                {itemA?.title || itemA?.name} <span className="text-[#FDB913] text-sm">×</span>{' '}
                {itemB?.title || itemB?.name}
              </h3>
            </div>
          </div>

          <div className="lg:col-span-7 space-y-10 pt-8 lg:pt-0">
            <div>
              <h1 className="text-6xl md:text-7xl font-black italic manga-font leading-[0.8] tracking-tighter uppercase mb-4">
                {t('games.forge.result_title_part1', 'FUSION')}{' '}
                <span className="bg-gradient-to-br from-[#FDB913] to-[#E8442B] bg-clip-text text-transparent">
                  {t('games.forge.result_title_part2', 'RÉUSSIE')}
                </span>
              </h1>
              <p className="text-base text-[#8F94A5]">
                {t(
                  'games.forge.result_subtitle',
                  'Une nouvelle réalité a été forgée dans le nexus.',
                )}
              </p>
            </div>

            <div className="bg-[#0F1016] p-10 rounded-2xl shadow-xl border border-[#F4F1E8]/10 relative group">
              <div className="absolute -top-4 -left-4 -rotate-2 border-2 border-[#E8442B] bg-[#0B0C10] text-[#E8442B] px-5 py-2 text-xs font-black uppercase tracking-widest rounded-[3px] shadow-lg group-hover:-translate-y-1 transition-transform">
                {t('games.forge.synopsis_badge', "SYNOPSIS GÉNÉRÉ PAR L'IA")}
              </div>
              <p className="text-xl md:text-2xl leading-relaxed italic font-medium text-[#F4F1E8]/90 first-letter:text-5xl first-letter:font-black first-letter:text-[#FDB913] first-letter:mr-3 first-letter:float-left whitespace-pre-wrap">
                {status.scenario}
              </p>
            </div>

            <div className="flex flex-wrap gap-4">
              <button
                onClick={() => navigate(`/forge/vn/${fusionData?.fusion_id}/`)}
                className="flex-1 min-w-[200px] bg-gradient-to-br from-[#FDB913] to-[#E8442B] text-[#0B0C10] py-5 px-8 rounded-2xl font-black italic text-lg hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3 uppercase shadow-xl border-none cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
              >
                <Film className="w-6 h-6" />
                {t('games.forge.to_visual_novel', 'Transformer en Visual Novel')}
              </button>
              <button
                onClick={resetForge}
                className="flex-1 min-w-[200px] bg-transparent border border-[#F4F1E8]/20 text-[#F4F1E8] py-5 px-8 rounded-2xl font-black italic text-lg hover:border-[#FDB913] hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3 uppercase shadow-xl cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
              >
                <RefreshCw className="w-6 h-6" />
                {t('games.forge.back_to_forge', 'Retourner à la Forge')}
              </button>
              <div className="flex gap-4">
                <button className="w-16 h-16 bg-[#0F1016] text-[#F4F1E8] flex items-center justify-center rounded-2xl shadow-lg hover:text-[#E8442B] hover:scale-110 transition-all border border-[#F4F1E8]/10 cursor-pointer">
                  <Heart className="w-8 h-8" />
                </button>
                <button className="w-16 h-16 bg-[#0F1016] text-[#F4F1E8] flex items-center justify-center rounded-2xl shadow-lg hover:text-[#FDB913] hover:scale-110 transition-all border border-[#F4F1E8]/10 cursor-pointer">
                  <Share2 className="w-8 h-8" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
