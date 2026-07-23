import React from 'react';
import { Users, Volume2, Play, Loader2, Star, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { SeiyuuResult } from '../../../features/labs/types/seiyuuTypes';

interface SeiyuuResultCardProps {
  seiyuu: SeiyuuResult;
  index: number;
  activeAudio: string | null;
  audioLoading: string | null;
  onPlaySample: (url: string) => void;
}

export const SeiyuuResultCard: React.FC<SeiyuuResultCardProps> = ({
  seiyuu,
  index,
  activeAudio,
  audioLoading,
  onPlaySample,
}) => {
  const { t } = useTranslation();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <div className="h-full rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] transition-colors hover:border-[#FDB913]/40">
        <div className="flex flex-col gap-8 p-8 md:flex-row">
          {/* Visual Indicator */}
          <div className="relative flex h-24 w-24 flex-none items-center justify-center rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]">
            <Users className="h-10 w-10 text-[#8F94A5]/50" aria-hidden="true" />
            <span className="absolute bottom-1.5 right-1.5 rounded border border-[#F4F1E8]/10 bg-[#0B0C10] px-1.5 py-0.5 text-[8px] font-black uppercase text-[#8F94A5]">
              {seiyuu.language === 'japanese'
                ? '🇯🇵 JP'
                : seiyuu.language === 'french'
                  ? '🇫🇷 FR'
                  : '🌐'}
            </span>
          </div>

          <div className="flex-grow space-y-5">
            <header className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]">
                  {seiyuu.name}
                </h3>
                <span className="mt-1 inline-block text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                  {seiyuu.origin === 'dataset'
                    ? t('labs.seiyuu.origin_dataset_full', 'Dataset Hugging Face')
                    : seiyuu.origin === 'youtube'
                      ? t('labs.seiyuu.origin_youtube_full', 'Ingestion YouTube')
                      : t('labs.seiyuu.origin_manual', 'Manuel')}
                </span>
              </div>
              <button
                type="button"
                onClick={() => onPlaySample(seiyuu.sample_url)}
                disabled={audioLoading === seiyuu.sample_url}
                aria-label="Écouter l'échantillon vocal"
                className={`flex h-12 w-12 flex-none cursor-pointer items-center justify-center rounded-xl border-none transition-colors disabled:cursor-not-allowed ${
                  activeAudio === seiyuu.sample_url
                    ? 'bg-[#FDB913] text-[#0B0C10]'
                    : 'bg-[#F4F1E8]/5 text-[#F4F1E8] hover:bg-[#E8442B]'
                }`}
              >
                {audioLoading === seiyuu.sample_url ? (
                  <Loader2 className="h-5 w-5 animate-spin text-[#FDB913]" aria-hidden="true" />
                ) : activeAudio === seiyuu.sample_url ? (
                  <Volume2 className="h-5 w-5" aria-hidden="true" />
                ) : (
                  <Play className="ml-0.5 h-5 w-5" aria-hidden="true" />
                )}
              </button>
            </header>

            <p className="text-sm italic leading-relaxed text-[#8F94A5]">
              «{' '}
              {seiyuu.definition ||
                t('labs.seiyuu.no_desc', 'Pas de description supplémentaire pour cette voix.')}{' '}
              »
            </p>

            {seiyuu.roles && (
              <div className="space-y-3">
                <h4 className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  <Star className="h-3 w-3" aria-hidden="true" /> Rôles emblématiques
                </h4>
                <div className="flex flex-wrap gap-2">
                  {seiyuu.roles.split(',').map((role, idx) => (
                    <span
                      key={idx}
                      className="rounded-lg border border-[#F4F1E8]/10 px-3 py-1 text-[9px] font-bold uppercase text-[#8F94A5]"
                    >
                      {role.trim()}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between border-t border-[#F4F1E8]/10 pt-5">
              <span className="text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                Impact : {seiyuu.impact || 'Custom'}
              </span>
              {seiyuu.origin_detail && seiyuu.origin_detail.startsWith('http') && (
                <a
                  href={seiyuu.origin_detail}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:text-[#FDB913]"
                >
                  {t('labs.seiyuu.original_source', 'Source Originale')}{' '}
                  <ChevronRight className="h-3 w-3" aria-hidden="true" />
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
