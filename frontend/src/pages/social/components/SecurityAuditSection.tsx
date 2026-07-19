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
  <div className="flex items-center justify-between group">
    <div className="flex items-center gap-4">
      <div className="p-3 bg-white/5 rounded-2xl group-hover:bg-purple-500/10 transition-colors">
        {icon}
      </div>
      <span className="text-[11px] font-black uppercase tracking-widest opacity-60">{label}</span>
    </div>
    <span className="font-black italic text-sm">
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
    <section className="p-10 rounded-[3rem] bg-navy-900/40 border border-white/5 space-y-10">
      <h3 className="text-2xl font-black italic uppercase manga-font tracking-tight flex items-center gap-3 text-purple-400">
        <Scale className="w-6 h-6" /> {t('social.transparency.security_audit', 'Audit de Sécurité')}
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
          icon={<Lock className="text-purple-400" />}
        />
        <AuditRow
          label={t('social.transparency.hallucination_rate', "Taux d'Hallucination")}
          value={
            ethicsAudit?.hallucination_rate != null
              ? (ethicsAudit.hallucination_rate * 100).toFixed(1)
              : t('social.transparency.insufficient_data', 'Données insuffisantes')
          }
          suffix={ethicsAudit?.hallucination_rate != null ? '%' : ''}
          icon={<AlertTriangle className="text-purple-400" />}
        />
      </div>

      <p className="pt-8 border-t border-white/5 text-[10px] font-bold opacity-30 uppercase tracking-widest leading-relaxed">
        {t(
          'social.transparency.audit_footnote',
          "Conformité = part des interactions évaluées non bloquées par le garde-fou. Hallucination = part des réponses signalées par l'évaluation automatique.",
        )}
      </p>
    </section>
  );
};
