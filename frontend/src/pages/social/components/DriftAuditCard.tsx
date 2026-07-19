import React from 'react';
import { useTranslation } from 'react-i18next';
import { Badge } from '../../../components/ui/Badge';

/** One embedding-drift entry: status badge + KS-test p-value + sample size. */
export const DriftAuditCard: React.FC<{
  name: string;
  info: { status: string; p_value?: number; sample_size?: number };
}> = ({ name, info }) => {
  const { t } = useTranslation();
  return (
    <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex flex-col gap-4 group hover:bg-white/10 transition-all">
      <div className="flex justify-between items-center">
        <span className="font-black italic uppercase text-xs tracking-widest">{name}</span>
        <Badge
          variant={
            info.status === 'healthy' ? 'success' : info.status === 'alert' ? 'danger' : 'neutral'
          }
        >
          {info.status}
        </Badge>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-[8px] font-black opacity-30 uppercase mb-1">P-Value (KS Test)</p>
          <p
            className={`text-2xl font-black italic manga-font ${info.p_value == null ? 'text-gray-500' : info.p_value < 0.05 ? 'text-red-500' : 'text-emerald-500'}`}
          >
            {info.p_value != null ? info.p_value.toFixed(4) : 'N/A'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[8px] font-black opacity-30 uppercase mb-1">
            {t('social.transparency.sample', 'Échantillon')}
          </p>
          <p className="text-sm font-bold uppercase tracking-tighter">
            {info.sample_size != null ? `${info.sample_size} items` : '—'}
          </p>
        </div>
      </div>
    </div>
  );
};
