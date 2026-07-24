import React from 'react';
import { Scale, Lock, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const AuditRow = ({
  label,
  value,
  suffix,
  icon,
}: {
  label: string;
  value: number | string;
  suffix: string;
  icon: React.ReactNode;
}) => (
  <div className="group flex items-center justify-between">
    <div className="flex items-center gap-4">
      <div className="rounded-xl bg-[#F4F1E8]/5 p-3 transition-colors group-hover:bg-[#5D7FD3]/10">
        {icon}
      </div>
      <span className="text-[11px] font-black uppercase tracking-widest text-[#8F94A5]">
        {label}
      </span>
    </div>
    <span className="text-sm font-black italic text-[#FDB913]">
      {typeof value === 'number' && value < 1 ? value.toFixed(3) : value}
      {suffix}
    </span>
  </div>
);

/** Safety-compliance and hallucination-rate audit panel. */
export const SecurityAuditSection: React.FC<{
  ethicsAudit?: { safety_compliance: number | null; hallucination_rate: number | null };
}> = ({ ethicsAudit }) => {
  const { t } = useTranslation();
  return (
    <section className="space-y-10 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 sm:p-10">
      <h3 className="font-manga flex items-center gap-3 text-2xl font-black uppercase italic tracking-tight text-[#5D7FD3]">
        <Scale className="h-6 w-6" aria-hidden="true" />{' '}
        {t('social.transparency.security_audit', 'Audit de Sécurité')}
      </h3>
      <div className="space-y-8">
        <AuditRow
          label={t('social.transparency.safety_compliance', 'Conformité Sécurité')}
          value={
            ethicsAudit?.safety_compliance != null
              ? (ethicsAudit.safety_compliance * 100).toFixed(1)
              : t('social.transparency.insufficient_data', 'Données insuffisantes')
          }
          suffix={ethicsAudit?.safety_compliance != null ? '%' : ''}
          icon={<Lock className="text-[#5D7FD3]" aria-hidden="true" />}
        />
        <AuditRow
          label={t('social.transparency.hallucination_rate', "Taux d'Hallucination")}
          value={
            ethicsAudit?.hallucination_rate != null
              ? (ethicsAudit.hallucination_rate * 100).toFixed(1)
              : t('social.transparency.insufficient_data', 'Données insuffisantes')
          }
          suffix={ethicsAudit?.hallucination_rate != null ? '%' : ''}
          icon={<AlertTriangle className="text-[#5D7FD3]" aria-hidden="true" />}
        />
      </div>

      <p className="border-t border-[#F4F1E8]/10 pt-8 text-[10px] font-bold uppercase leading-relaxed tracking-widest text-[#8F94A5]">
        {t(
          'social.transparency.audit_footnote',
          "Conformité = part des interactions évaluées non bloquées par le garde-fou. Hallucination = part des réponses signalées par l'évaluation automatique.",
        )}
      </p>
    </section>
  );
};
