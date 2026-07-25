import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import {
  Zap,
  History,
  TrendingUp,
  AlertCircle,
  Database,
  LayoutDashboard,
  Calendar,
  DollarSign,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { socialService } from '../../features/social/services/socialService';
import { AIUsageData } from '../../types';
import { LAB_CTA } from '../labs/components/shared/LabKit';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';

// The two charts here are simple 2D line/bar plots, so they use recharts
// (~100 KB) rather than plotly.js (~4.6 MB), which this account page would
// otherwise pull in just to draw a 7-day history.
const AXIS_TICK = { fill: '#8F94A5', fontSize: 10 } as const;
const CHART_MARGIN = { top: 10, right: 10, left: 10, bottom: 0 } as const;
const TOOLTIP_STYLE = {
  background: '#0B0C10',
  border: '1px solid rgba(244,241,232,0.15)',
  borderRadius: 8,
  fontSize: 12,
  color: '#F4F1E8',
} as const;

const PANEL = 'rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]';

const fmtDate = (val: string) => val.split('-').slice(1).reverse().join('/');

const AIUsagePage: React.FC = () => {
  const { t } = useTranslation();
  const [usageData, setUsageData] = useState<AIUsageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const data = await socialService.getAIUsage();
        setUsageData(data);
      } catch (err) {
        console.error('Failed to fetch AI usage:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchUsage();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0C10]">
        <div className="w-16 h-16 border-4 border-[#F4F1E8]/10 border-t-[#E8442B] rounded-full animate-spin" />
      </div>
    );
  }

  if (!usageData) {
    return (
      <div className="min-h-screen bg-[#0B0C10] p-20 text-center text-[#F4F1E8]">
        <AlertCircle className="w-12 h-12 text-[#E8442B] mx-auto mb-4" />
        <p className="font-bold">
          {t('auth.usage.load_error', "Impossible de charger les données d'utilisation.")}
        </p>
      </div>
    );
  }

  const { usage_today, limits, tier, history } = usageData;

  const chartData = history.map((h) => ({
    label: fmtDate(h.date),
    tokens: h.tokens,
    requests: h.requests,
  }));

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8] pb-20">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
            <div>
              <div className="relative mb-4 flex items-center gap-3">
                <span className="explore-stamp -rotate-2" aria-hidden>
                  量
                </span>
                <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                  Mesure · Consommation
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-black italic font-manga tracking-tighter uppercase flex items-center gap-3 text-[#F4F1E8]">
                <LayoutDashboard className="w-10 h-10 text-[#E8442B]" />{' '}
                {t('auth.usage.title_part1', 'QUOTAS')}{' '}
                <span className="text-[#E8442B]">{t('auth.usage.title_part2', 'IA')}</span>
              </h1>
              <p className="text-xs text-[#8F94A5] font-bold uppercase tracking-widest mt-2">
                {t(
                  'auth.usage.subtitle',
                  'Suivi en temps réel de votre consommation neuronale et budget sémantique.',
                )}
              </p>
            </div>
            <span className="rounded-xl border border-[#FDB913]/40 bg-[#FDB913]/10 py-2 px-6 text-sm font-black italic font-manga uppercase text-[#FDB913]">
              {t('auth.usage.status', { defaultValue: 'Statut: {{tier}}', tier })}
            </span>
          </div>

          {/* Today's Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <div className={`${PANEL} p-6 sm:p-8 relative overflow-hidden group`}>
              <div className="absolute top-0 right-0 p-4 opacity-[0.06]">
                <Zap className="w-20 h-20 text-[#FDB913]" />
              </div>
              <div className="relative z-10">
                <span className="text-[10px] font-black uppercase text-[#8F94A5] tracking-[0.2em] block mb-4">
                  {t('auth.usage.berrix_consumption', 'Consommation Berrix (Bx)')}
                </span>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-4xl font-black italic font-manga text-[#FDB913]">
                    {usage_today.tokens.toLocaleString()}
                  </span>
                  <span className="text-xs font-bold text-[#8F94A5]">
                    / {limits.daily_tokens.toLocaleString()}
                  </span>
                </div>
                <div className="w-full h-2 bg-[#0B0C10] rounded-full overflow-hidden mb-4">
                  <div
                    className="h-full bg-[#FDB913] transition-all duration-1000"
                    style={{ width: `${usage_today.tokens_percent}%` }}
                  />
                </div>
                <span className="text-[10px] font-bold text-[#FDB913] uppercase">
                  {t('auth.usage.percent_used_today', {
                    defaultValue: "{{percent}}% utilisé aujourd'hui",
                    percent: usage_today.tokens_percent,
                  })}
                </span>
              </div>
            </div>

            <div className={`${PANEL} p-6 sm:p-8 relative overflow-hidden group`}>
              <div className="absolute top-0 right-0 p-4 opacity-[0.06]">
                <TrendingUp className="w-20 h-20 text-[#F4F1E8]" />
              </div>
              <div className="relative z-10">
                <span className="text-[10px] font-black uppercase text-[#8F94A5] tracking-[0.2em] block mb-4">
                  {t('auth.usage.api_requests', 'Requêtes API')}
                </span>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-4xl font-black italic font-manga text-[#F4F1E8]">
                    {usage_today.requests.toLocaleString()}
                  </span>
                  <span className="text-xs font-bold text-[#8F94A5]">
                    / {limits.daily_requests.toLocaleString()}
                  </span>
                </div>
                <div className="w-full h-2 bg-[#0B0C10] rounded-full overflow-hidden mb-4">
                  <div
                    className="h-full bg-[#8F94A5] transition-all duration-1000"
                    style={{ width: `${usage_today.requests_percent}%` }}
                  />
                </div>
                <span className="text-[10px] font-bold text-[#8F94A5] uppercase">
                  {t('auth.usage.percent_calls_used', {
                    defaultValue: '{{percent}}% des appels consommés',
                    percent: usage_today.requests_percent,
                  })}
                </span>
              </div>
            </div>

            <div className={`${PANEL} p-6 sm:p-8 relative overflow-hidden group`}>
              <div className="absolute top-0 right-0 p-4 opacity-[0.06]">
                <DollarSign className="w-20 h-20 text-[#FDB913]" />
              </div>
              <div className="relative z-10">
                <span className="text-[10px] font-black uppercase text-[#8F94A5] tracking-[0.2em] block mb-4">
                  {t('auth.usage.estimated_cost', 'Coût Estimé (Valeur)')}
                </span>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-4xl font-black italic font-manga text-[#FDB913]">
                    ${usage_today.estimated_cost_usd.toFixed(4)}
                  </span>
                </div>
                <p className="text-[10px] font-bold text-[#8F94A5] leading-relaxed uppercase">
                  {t(
                    'auth.usage.cost_note',
                    'Estimation basée sur les tarifs H100 Cluster & VRAM. Entièrement couvert par votre attention publicitaire.',
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className={`${PANEL} p-6 sm:p-8`}>
              <h3 className="text-sm font-black uppercase tracking-widest mb-8 flex items-center gap-2 text-[#F4F1E8]">
                <History className="w-4 h-4 text-[#FDB913]" />{' '}
                {t('auth.usage.berrix_history', 'Historique des Berrix (7j)')}
              </h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={CHART_MARGIN}>
                    <XAxis dataKey="label" tick={AXIS_TICK} axisLine={false} tickLine={false} />
                    <YAxis hide />
                    <Tooltip
                      contentStyle={TOOLTIP_STYLE}
                      labelStyle={{ color: '#8F94A5' }}
                      cursor={{ stroke: '#FDB913', strokeOpacity: 0.25 }}
                      formatter={(value) => [`${Number(value).toLocaleString()} Bx`, '']}
                    />
                    <Area
                      type="monotone"
                      dataKey="tokens"
                      stroke="#FDB913"
                      strokeWidth={3}
                      fill="#FDB913"
                      fillOpacity={0.15}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className={`${PANEL} p-6 sm:p-8`}>
              <h3 className="text-sm font-black uppercase tracking-widest mb-8 flex items-center gap-2 text-[#F4F1E8]">
                <Database className="w-4 h-4 text-[#8F94A5]" />{' '}
                {t('auth.usage.api_calls_per_day', 'Appels API par Jour')}
              </h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={CHART_MARGIN}>
                    <XAxis dataKey="label" tick={AXIS_TICK} axisLine={false} tickLine={false} />
                    <YAxis hide />
                    <Tooltip
                      contentStyle={TOOLTIP_STYLE}
                      labelStyle={{ color: '#8F94A5' }}
                      cursor={{ fill: 'rgba(143,148,165,0.1)' }}
                      formatter={(value) => [
                        `${value} ${t('auth.usage.calls_unit', 'appels')}`,
                        '',
                      ]}
                    />
                    <Bar dataKey="requests" fill="#8F94A5" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Footer Info */}
          <div className="mt-12 p-8 rounded-2xl border border-[#E8442B]/25 bg-[#E8442B]/[0.05] flex flex-col md:flex-row items-center gap-8">
            <div className="w-16 h-16 bg-[#E8442B]/15 border border-[#E8442B]/25 rounded-2xl flex items-center justify-center shrink-0">
              <Calendar className="w-8 h-8 text-[#E8442B]" />
            </div>
            <div>
              <h4 className="text-lg font-black italic font-manga uppercase mb-1 text-[#F4F1E8]">
                {t('auth.usage.quota_reset_title', 'Réinitialisation des Quotas')}
              </h4>
              <p className="text-xs text-[#8F94A5] leading-relaxed uppercase font-bold">
                {t(
                  'auth.usage.quota_reset_desc',
                  "Vos quotas sont réinitialisés chaque jour à **minuit (UTC)**. En cas de dépassement, l'accès aux fonctionnalités IA (RAG, Génération, Forge) sera restreint jusqu'au prochain cycle ou recharge dans la Power Station.",
                )}
              </p>
            </div>
            <div className="flex-grow" />
            <Link
              to="/power-station/"
              className={`${LAB_CTA} md:w-auto px-8 whitespace-nowrap no-underline`}
            >
              {t('auth.usage.recharge_cta', 'RECHARGER MON ÉNERGIE')}
            </Link>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AIUsagePage;
