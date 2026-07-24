import React from 'react';
import { useTranslation } from 'react-i18next';

/** One embedding-drift entry: status pill + KS-test p-value + sample size.
 *  Or = sain (voix données), vermillon = alerte, graphite = indéterminé. */
export const DriftAuditCard: React.FC<{
  name: string;
  info: { status: string; p_value?: number; sample_size?: number };
}> = ({ name, info }) => {
  const { t } = useTranslation();
  const statusClass =
    info.status === 'healthy'
      ? 'border-[#FDB913]/40 text-[#FDB913]'
      : info.status === 'alert'
        ? 'border-[#E8442B]/40 text-[#E8442B]'
        : 'border-[#F4F1E8]/15 text-[#8F94A5]';
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 transition-colors hover:border-[#5D7FD3]/40">
      <div className="flex items-center justify-between">
        <span className="text-xs font-black uppercase italic tracking-widest text-[#F4F1E8]">
          {name}
        </span>
        <span
          className={`rounded-full border px-2.5 py-0.5 text-[9px] font-black uppercase tracking-widest ${statusClass}`}
        >
          {info.status}
        </span>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="mb-1 text-[8px] font-black uppercase text-[#8F94A5]">P-Value (KS Test)</p>
          <p
            className={`font-manga text-2xl font-black italic ${
              info.p_value == null
                ? 'text-[#8F94A5]'
                : info.p_value < 0.05
                  ? 'text-[#E8442B]'
                  : 'text-[#FDB913]'
            }`}
          >
            {info.p_value != null ? info.p_value.toFixed(4) : 'N/A'}
          </p>
        </div>
        <div className="text-right">
          <p className="mb-1 text-[8px] font-black uppercase text-[#8F94A5]">
            {t('social.transparency.sample', 'Échantillon')}
          </p>
          <p className="text-sm font-bold uppercase tracking-tighter text-[#F4F1E8]">
            {info.sample_size != null ? `${info.sample_size} items` : '—'}
          </p>
        </div>
      </div>
    </div>
  );
};
