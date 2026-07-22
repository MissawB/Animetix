import React from 'react';
import { Users, Volume2, Play, Loader2, Star, Sparkles, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
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
      <Card
        padding="none"
        className="bg-navy-950/40 border-white/5 hover:border-emerald-500/30 transition-all duration-500 overflow-hidden relative group"
      >
        <div className="p-10 flex flex-col md:flex-row gap-10">
          {/* Visual Indicator */}
          <div className="w-32 h-32 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform overflow-hidden relative">
            <Users className="w-12 h-12 text-white/10" />
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <span className="absolute bottom-2 right-2 text-[8px] font-black px-2 py-0.5 bg-black/60 rounded border border-white/10 uppercase">
              {seiyuu.language === 'japanese'
                ? '🇯🇵 JP'
                : seiyuu.language === 'french'
                  ? '🇫🇷 FR'
                  : '🌐'}
            </span>
          </div>

          <div className="flex-grow space-y-6">
            <header className="flex justify-between items-start">
              <div>
                <h3 className="text-3xl font-black italic manga-font uppercase text-white mb-1 group-hover:text-emerald-400 transition-colors">
                  {seiyuu.name}
                </h3>
                <div className="flex gap-2 items-center">
                  <Badge
                    variant="neutral"
                    className="bg-emerald-500/10 text-emerald-400 border-none text-[8px] italic font-black uppercase tracking-widest"
                  >
                    {seiyuu.origin === 'dataset'
                      ? t('labs.seiyuu.origin_dataset_full', 'Dataset Hugging Face')
                      : seiyuu.origin === 'youtube'
                        ? t('labs.seiyuu.origin_youtube_full', 'Ingestion YouTube')
                        : t('labs.seiyuu.origin_manual', 'Manuel')}
                  </Badge>
                </div>
              </div>
              <button
                onClick={() => onPlaySample(seiyuu.sample_url)}
                disabled={audioLoading === seiyuu.sample_url}
                className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all ${
                  activeAudio === seiyuu.sample_url
                    ? 'bg-emerald-500 text-white animate-pulse'
                    : 'bg-white/5 text-white hover:bg-emerald-600'
                }`}
              >
                {audioLoading === seiyuu.sample_url ? (
                  <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
                ) : activeAudio === seiyuu.sample_url ? (
                  <Volume2 className="w-6 h-6" />
                ) : (
                  <Play className="w-6 h-6 ml-1" />
                )}
              </button>
            </header>

            <p className="text-sm font-medium text-white/40 leading-relaxed italic">
              "
              {seiyuu.definition ||
                t('labs.seiyuu.no_desc', 'Pas de description supplémentaire pour cette voix.')}
              "
            </p>

            {seiyuu.roles && (
              <div className="space-y-4">
                <h4 className="text-[10px] font-black uppercase tracking-widest text-white/20 flex items-center gap-2">
                  <Star className="w-3 h-3" /> Iconic Roles
                </h4>
                <div className="flex flex-wrap gap-2">
                  {seiyuu.roles.split(',').map((role, idx) => (
                    <Badge
                      key={idx}
                      variant="neutral"
                      className="border-white/10 text-white/60 bg-white/5 px-3 py-1 rounded-lg text-[9px] font-bold uppercase"
                    >
                      {role.trim()}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-6 border-t border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-3 h-3 text-emerald-500" />
                <span className="text-[9px] font-black uppercase text-emerald-500/50">
                  Impact Score: {seiyuu.impact || 'Custom'}
                </span>
              </div>
              {seiyuu.origin_detail && seiyuu.origin_detail.startsWith('http') && (
                <a
                  href={seiyuu.origin_detail}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[9px] font-black uppercase tracking-widest text-white/30 hover:text-emerald-400 transition-colors flex items-center gap-1"
                >
                  {t('labs.seiyuu.original_source', 'Source Originale')}{' '}
                  <ChevronRight className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};
