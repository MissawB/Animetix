import React from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, Image as ImageIcon, Heart, Share2, Film, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { SearchItem } from '../../types';
import { FusionResponse, FusionStatus } from '../../api';

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
    <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in zoom-in-95 duration-700">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
        <div className="lg:col-span-5 relative group">
          <div className="absolute -inset-4 bg-yellow-400/20 blur-3xl rounded-[4rem] opacity-50 group-hover:opacity-100 transition-opacity" />
          <div className="relative overflow-hidden rounded-[3.5rem] shadow-2xl border-8 border-white dark:border-anime-dark-card transform -rotate-1 hover:rotate-0 transition-transform duration-500">
            {status.image_url ? (
              <img
                src={status.image_url}
                className="w-full aspect-[3/4] object-cover scale-105 group-hover:scale-100 transition-transform duration-700"
                alt={t('games.forge.result_image_alt', 'Fusion')}
                loading="lazy"
                decoding="async"
              />
            ) : (
              <div className="w-full aspect-[3/4] bg-anime-dark-bg flex flex-col items-center justify-center gap-4">
                <ImageIcon className="w-20 h-20 text-white/10" />
                <p className="text-xs font-black opacity-20 uppercase tracking-widest">
                  {t('games.forge.image_not_generated', 'Image non générée')}
                </p>
              </div>
            )}

            <div className="absolute top-8 left-8 flex flex-col gap-2">
              <span className="bg-black/80 backdrop-blur-md text-white text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-tighter">
                {t('games.forge.style_label', 'Style:')} {artStyle}
              </span>
              <span className="bg-yellow-400 text-black text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-tighter shadow-lg">
                {t('games.forge.chaos_label', 'Chaos:')} {chaosLevel}%
              </span>
            </div>
          </div>

          <div className="absolute -bottom-8 -right-4 bg-white dark:bg-anime-dark-card p-6 rounded-3xl shadow-2xl border border-gray-100 dark:border-white/5 max-w-[280px] transform rotate-3">
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="w-5 h-5 text-yellow-400" />
              <span className="text-[10px] font-black opacity-40 uppercase tracking-widest">
                {t('games.forge.new_archetype', 'NOUVEL ARCHÉTYPE')}
              </span>
            </div>
            <h3 className="text-xl font-black italic manga-font leading-tight">
              {itemA?.title || itemA?.name} <span className="text-yellow-400 text-sm">×</span> {itemB?.title || itemB?.name}
            </h3>
          </div>
        </div>

        <div className="lg:col-span-7 space-y-10 pt-8 lg:pt-0">
          <div>
            <h1 className="text-7xl font-black italic manga-font leading-[0.8] tracking-tighter uppercase mb-4">
              {t('games.forge.result_title_part1', 'FUSION')}{' '}
              <span className="text-yellow-400">{t('games.forge.result_title_part2', 'RÉUSSIE')}</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.2em]">
              {t('games.forge.result_subtitle', 'Une nouvelle réalité a été forgée dans le nexus.')}
            </p>
          </div>

          <div className="bg-white/50 dark:bg-anime-dark-card/50 backdrop-blur-xl p-10 rounded-[3rem] shadow-xl border border-white dark:border-white/5 relative group">
            <div className="absolute -top-4 -left-4 bg-black text-white px-6 py-2 text-xs font-black uppercase tracking-widest rounded-2xl shadow-lg group-hover:-translate-y-1 transition-transform">
              {t('games.forge.synopsis_badge', "SYNOPSIS GÉNÉRÉ PAR L'IA")}
            </div>
            <div className="prose dark:prose-invert max-w-none">
              <p className="text-2xl leading-relaxed italic font-medium opacity-90 first-letter:text-5xl first-letter:font-black first-letter:text-yellow-400 first-letter:mr-3 first-letter:float-left whitespace-pre-wrap">
                {status.scenario}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => navigate(`/forge/vn/${fusionData?.fusion_id}/`)}
              className="flex-1 min-w-[200px] bg-yellow-400 text-black py-5 px-8 rounded-2xl font-black italic text-lg hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3 uppercase shadow-xl"
            >
              <Film className="w-6 h-6" />
              {t('games.forge.to_visual_novel', 'Transformer en Visual Novel')}
            </button>
            <button
              onClick={resetForge}
              className="flex-1 min-w-[200px] bg-black text-white dark:bg-white dark:text-black py-5 px-8 rounded-2xl font-black italic text-lg hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3 uppercase shadow-xl"
            >
              <RefreshCw className="w-6 h-6" />
              {t('games.forge.back_to_forge', 'Retourner à la Forge')}
            </button>
            <div className="flex gap-4">
              <button className="w-16 h-16 bg-white dark:bg-anime-dark-card flex items-center justify-center rounded-2xl shadow-lg hover:text-red-500 hover:scale-110 transition-all border border-black/5 dark:border-white/5">
                <Heart className="w-8 h-8" />
              </button>
              <button className="w-16 h-16 bg-white dark:bg-anime-dark-card flex items-center justify-center rounded-2xl shadow-lg hover:text-blue-500 hover:scale-110 transition-all border border-black/5 dark:border-white/5">
                <Share2 className="w-8 h-8" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
