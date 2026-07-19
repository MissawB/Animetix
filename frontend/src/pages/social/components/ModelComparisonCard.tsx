import React from 'react';
import { Cpu, Trophy, Zap, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import type { ComparisonModel } from '../transparencyData';

/** One model tile in the "our model vs open source" comparison grid. `isOurs`
 *  flips the styling to the highlighted champion variant; `index` staggers the
 *  entrance animation. */
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
      <Card
        padding="none"
        className={`overflow-hidden group transition-all hover:scale-[1.02] ${
          model.isOurs
            ? '!bg-blue-950/40 border-2 !border-yellow-400/60 shadow-[0_0_40px_rgba(250,204,21,0.15)]'
            : '!bg-black !border-white/5 hover:!border-blue-500/30'
        }`}
      >
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center ${model.isOurs ? 'bg-yellow-400/15 text-yellow-400' : 'bg-blue-500/10 text-blue-500'}`}
            >
              <Cpu className="w-5 h-5" />
            </div>
            <div className="flex items-center gap-2">
              {/* !bg/!text : les classes du variant Badge gagneraient sinon (ordre CSS). */}
              {model.isOurs && (
                <Badge
                  variant="warning"
                  className="text-[8px] py-0.5 px-2 !bg-yellow-400 !text-black border-none"
                >
                  {t('social.transparency.our_model_badge', 'NOTRE MODÈLE DE BASE')}
                </Badge>
              )}
              <Badge variant="success" className="text-[8px] py-0.5 px-2">
                OPEN SOURCE
              </Badge>
            </div>
          </div>
          <h3 className="text-lg font-black italic uppercase truncate mb-1" title={model.model_id}>
            {model.model_id.split('/').pop()}
          </h3>
          <p className="text-[10px] font-bold opacity-30 uppercase mb-6 tracking-widest">
            {model.provider}
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
              <p className="text-[8px] font-black opacity-30 uppercase mb-1 flex items-center gap-1">
                <Trophy className="w-2 h-2" /> {t('social.transparency.elo_label', 'ELO (ARENA)')}
              </p>
              <p
                className={`text-xl font-black italic manga-font ${model.isOurs ? 'text-yellow-400' : 'text-emerald-500'}`}
              >
                {model.elo_score}
              </p>
            </div>
            <div className="p-3 bg-white/5 rounded-2xl border border-white/5">
              <p className="text-[8px] font-black opacity-30 uppercase mb-1 flex items-center gap-1">
                <Zap className="w-2 h-2" /> MMLU
              </p>
              <p
                className={`text-xl font-black italic manga-font ${model.isOurs ? 'text-yellow-400' : 'text-blue-500'}`}
              >
                {model.mmlu_score}%
              </p>
            </div>
          </div>
        </div>
        <div className="p-4 bg-white/5 border-t border-white/5 flex justify-between items-center text-[10px] font-black uppercase text-blue-400 opacity-60">
          <span className="flex items-center gap-1">
            <Activity className="w-2 h-2" />{' '}
            {t('social.transparency.params_label', '{{params}} paramètres', {
              params: model.params,
            })}
          </span>
          <span>{model.license}</span>
        </div>
      </Card>
    </motion.div>
  );
};
