import React from 'react';
import { Cpu, Trophy, Zap, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import type { ComparisonModel } from '../transparencyData';

/** One model tile in the "our model vs open source" comparison grid. `isOurs`
 *  flips the styling to the highlighted champion variant (encre or); `index`
 *  staggers the entrance animation. */
export const ModelComparisonCard: React.FC<{ model: ComparisonModel; index: number }> = ({
  model,
  index,
}) => {
  const { t } = useTranslation();
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={model.isOurs ? 'md:col-span-2' : ''}
    >
      <div
        className={`overflow-hidden rounded-2xl border bg-[#0F1016] transition-colors ${
          model.isOurs ? 'border-[#FDB913]/60' : 'border-[#F4F1E8]/10 hover:border-[#5D7FD3]/40'
        }`}
      >
        <div className="p-6">
          <div className="mb-4 flex items-start justify-between">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                model.isOurs ? 'bg-[#FDB913]/15 text-[#FDB913]' : 'bg-[#5D7FD3]/10 text-[#5D7FD3]'
              }`}
            >
              <Cpu className="h-5 w-5" aria-hidden="true" />
            </div>
            <div className="flex items-center gap-2">
              {model.isOurs && (
                <span className="rounded-full bg-[#FDB913] px-2 py-0.5 text-[8px] font-black uppercase tracking-widest text-[#0B0C10]">
                  {t('social.transparency.our_model_badge', 'NOTRE MODÈLE DE BASE')}
                </span>
              )}
              <span className="rounded-full border border-[#F4F1E8]/15 px-2 py-0.5 text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
                OPEN SOURCE
              </span>
            </div>
          </div>
          <h3
            className="mb-1 truncate text-lg font-black uppercase italic text-[#F4F1E8]"
            title={model.model_id}
          >
            {model.model_id.split('/').pop()}
          </h3>
          <p className="mb-6 text-[10px] font-bold uppercase tracking-widest text-[#8F94A5]">
            {model.provider}
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3">
              <p className="mb-1 flex items-center gap-1 text-[8px] font-black uppercase text-[#8F94A5]">
                <Trophy className="h-2 w-2" aria-hidden="true" />{' '}
                {t('social.transparency.elo_label', 'ELO (ARENA)')}
              </p>
              <p
                className={`font-manga text-xl font-black italic ${
                  model.isOurs ? 'text-[#FDB913]' : 'text-[#F4F1E8]'
                }`}
              >
                {model.elo_score}
              </p>
            </div>
            <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3">
              <p className="mb-1 flex items-center gap-1 text-[8px] font-black uppercase text-[#8F94A5]">
                <Zap className="h-2 w-2" aria-hidden="true" /> MMLU
              </p>
              <p
                className={`font-manga text-xl font-black italic ${
                  model.isOurs ? 'text-[#FDB913]' : 'text-[#F4F1E8]'
                }`}
              >
                {model.mmlu_score}%
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between border-t border-[#F4F1E8]/10 bg-[#0B0C10]/60 p-4 text-[10px] font-black uppercase text-[#8F94A5]">
          <span className="flex items-center gap-1">
            <Activity className="h-2 w-2" aria-hidden="true" />{' '}
            {t('social.transparency.params_label', '{{params}} paramètres', {
              params: model.params,
            })}
          </span>
          <span>{model.license}</span>
        </div>
      </div>
    </motion.div>
  );
};
