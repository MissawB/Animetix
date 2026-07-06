import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { 
  Zap, 
  History, 
  TrendingUp, 
  AlertCircle, 
  Database, 
  LayoutDashboard,
  Calendar,
  DollarSign
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { getAIUsage, AIUsageData } from '../../api';
import _Plot from 'react-plotly.js';

const Plot =
  (_Plot as unknown as { default?: React.ComponentType<Record<string, unknown>> }).default ??
  (_Plot as unknown as React.ComponentType<Record<string, unknown>>);

const chartLayout = {
  autosize: true,
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  margin: { l: 10, r: 10, t: 10, b: 30 },
  xaxis: { tickfont: { color: '#888', size: 10 }, showgrid: false, zeroline: false, showline: false },
  yaxis: { visible: false },
  font: { family: 'Montserrat' },
  hovermode: 'x' as const,
  showlegend: false,
};

const fmtDate = (val: string) => val.split('-').slice(1).reverse().join('/');

const AIUsagePage: React.FC = () => {
  const { t } = useTranslation();
  const [usageData, setUsageData] = useState<AIUsageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const data = await getAIUsage();
        setUsageData(data);
      } catch (err) {
        console.error("Failed to fetch AI usage:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchUsage();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#fffcf0] dark:bg-[#0f0f1a]">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!usageData) {
    return (
      <div className="p-20 text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="font-bold">{t('auth.usage.load_error', "Impossible de charger les données d'utilisation.")}</p>
      </div>
    );
  }

  const { usage_today, limits, tier, history } = usageData;

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#fffcf0] dark:bg-[#0f0f1a] transition-colors duration-500 bg-manga-overlay pb-20">
        <div className="max-w-6xl mx-auto px-6 py-16">
          
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
            <div>
              <h1 className="text-4xl md:text-5xl font-black italic manga-font tracking-tighter uppercase flex items-center gap-3 text-black dark:text-white">
                <LayoutDashboard className="w-10 h-10 text-blue-500" /> {t('auth.usage.title_part1', 'QUOTAS')} <span className="text-blue-500">{t('auth.usage.title_part2', 'IA')}</span>
              </h1>
              <p className="text-xs text-gray-500 font-bold uppercase tracking-widest mt-2">
                {t('auth.usage.subtitle', 'Suivi en temps réel de votre consommation neuronale et budget sémantique.')}
              </p>
            </div>
            <Badge variant="primary" className="py-2 px-6 text-sm font-black italic manga-font uppercase shadow-lg">
              {t('auth.usage.status', { defaultValue: 'Statut: {{tier}}', tier })}
            </Badge>
          </div>

          {/* Today's Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            
            <Card padding="lg" className="bg-white dark:bg-[#161625] border-none shadow-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <Zap className="w-20 h-20 text-blue-500" />
              </div>
              <div className="relative z-10">
                <span className="text-[10px] font-black uppercase text-gray-400 tracking-[0.2em] block mb-4">{t('auth.usage.berrix_consumption', 'Consommation Berrix (Bx)')}</span>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-4xl font-black italic manga-font text-black dark:text-white">{usage_today.tokens.toLocaleString()}</span>
                  <span className="text-xs font-bold text-gray-400">/ {limits.daily_tokens.toLocaleString()}</span>
                </div>
                <div className="w-full h-2 bg-gray-100 dark:bg-black/40 rounded-full overflow-hidden mb-4">
                  <div 
                    className="h-full bg-blue-500 transition-all duration-1000"
                    style={{ width: `${usage_today.tokens_percent}%` }}
                  />
                </div>
                <span className="text-[10px] font-bold text-blue-500 uppercase">{t('auth.usage.percent_used_today', { defaultValue: "{{percent}}% utilisé aujourd'hui", percent: usage_today.tokens_percent })}</span>
              </div>
            </Card>

            <Card padding="lg" className="bg-white dark:bg-[#161625] border-none shadow-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <TrendingUp className="w-20 h-20 text-emerald-500" />
              </div>
              <div className="relative z-10">
                <span className="text-[10px] font-black uppercase text-gray-400 tracking-[0.2em] block mb-4">{t('auth.usage.api_requests', 'Requêtes API')}</span>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-4xl font-black italic manga-font text-black dark:text-white">{usage_today.requests.toLocaleString()}</span>
                  <span className="text-xs font-bold text-gray-400">/ {limits.daily_requests.toLocaleString()}</span>
                </div>
                <div className="w-full h-2 bg-gray-100 dark:bg-black/40 rounded-full overflow-hidden mb-4">
                  <div 
                    className="h-full bg-emerald-500 transition-all duration-1000"
                    style={{ width: `${usage_today.requests_percent}%` }}
                  />
                </div>
                <span className="text-[10px] font-bold text-emerald-500 uppercase">{t('auth.usage.percent_calls_used', { defaultValue: '{{percent}}% des appels consommés', percent: usage_today.requests_percent })}</span>
              </div>
            </Card>

            <Card padding="lg" className="bg-white dark:bg-[#161625] border-none shadow-xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <DollarSign className="w-20 h-20 text-yellow-500" />
              </div>
              <div className="relative z-10">
                <span className="text-[10px] font-black uppercase text-gray-400 tracking-[0.2em] block mb-4">{t('auth.usage.estimated_cost', 'Coût Estimé (Valeur)')}</span>
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-4xl font-black italic manga-font text-black dark:text-white">${usage_today.estimated_cost_usd.toFixed(4)}</span>
                </div>
                <p className="text-[10px] font-bold text-gray-400 leading-relaxed uppercase">
                  {t('auth.usage.cost_note', 'Estimation basée sur les tarifs H100 Cluster & VRAM. Entièrement couvert par votre attention publicitaire.')}
                </p>
              </div>
            </Card>

          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            <Card padding="lg" className="bg-white dark:bg-[#161625] border-none shadow-xl">
              <h3 className="text-sm font-black uppercase tracking-widest mb-8 flex items-center gap-2 text-black dark:text-white">
                <History className="w-4 h-4 text-blue-500" /> {t('auth.usage.berrix_history', 'Historique des Berrix (7j)')}
              </h3>
              <div className="h-64 w-full">
                <Plot
                  data={[{
                    x: history.map((h) => fmtDate(h.date)),
                    y: history.map((h) => h.tokens),
                    type: 'scatter',
                    mode: 'lines',
                    fill: 'tozeroy',
                    line: { color: '#3b82f6', width: 3, shape: 'spline' },
                    fillcolor: 'rgba(59,130,246,0.18)',
                    hovertemplate: '%{y:,} Bx<extra></extra>',
                  }]}
                  layout={chartLayout}
                  config={{ responsive: true, displayModeBar: false }}
                  style={{ width: '100%', height: '100%' }}
                  useResizeHandler
                />
              </div>
            </Card>

            <Card padding="lg" className="bg-white dark:bg-[#161625] border-none shadow-xl">
              <h3 className="text-sm font-black uppercase tracking-widest mb-8 flex items-center gap-2 text-black dark:text-white">
                <Database className="w-4 h-4 text-emerald-500" /> {t('auth.usage.api_calls_per_day', 'Appels API par Jour')}
              </h3>
              <div className="h-64 w-full">
                <Plot
                  data={[{
                    x: history.map((h) => fmtDate(h.date)),
                    y: history.map((h) => h.requests),
                    type: 'bar',
                    marker: { color: '#10b981' },
                    hovertemplate: t('auth.usage.calls_tooltip', '%{y} appels<extra></extra>'),
                  }]}
                  layout={chartLayout}
                  config={{ responsive: true, displayModeBar: false }}
                  style={{ width: '100%', height: '100%' }}
                  useResizeHandler
                />
              </div>
            </Card>

          </div>

          {/* Footer Info */}
          <div className="mt-12 p-8 rounded-[2rem] bg-blue-500/5 border border-blue-500/10 flex flex-col md:flex-row items-center gap-8">
            <div className="w-16 h-16 bg-blue-500/20 rounded-3xl flex items-center justify-center shrink-0">
              <Calendar className="w-8 h-8 text-blue-500" />
            </div>
            <div>
              <h4 className="text-lg font-black italic manga-font uppercase mb-1 text-black dark:text-white">{t('auth.usage.quota_reset_title', 'Réinitialisation des Quotas')}</h4>
              <p className="text-xs text-gray-500 leading-relaxed uppercase font-bold">
                {t('auth.usage.quota_reset_desc', "Vos quotas sont réinitialisés chaque jour à **minuit (UTC)**. En cas de dépassement, l'accès aux fonctionnalités IA (RAG, Génération, Forge) sera restreint jusqu'au prochain cycle ou recharge dans la Power Station.")}
              </p>
            </div>
            <div className="flex-grow" />
            <Link 
              to="/power-station/" 
              className="bg-blue-500 hover:bg-blue-600 text-white font-black italic manga-font px-8 py-4 rounded-xl shadow-lg transition-all no-underline whitespace-nowrap"
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
