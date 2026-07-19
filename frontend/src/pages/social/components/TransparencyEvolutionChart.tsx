import React from 'react';
import { TrendingUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import Plot from '../../../components/LazyPlot';

/** Semantic-accuracy evolution chart. The Plotly chart (lazy-loaded) renders
 *  only from two data points on; otherwise a "not enough data" placeholder. */
export const TransparencyEvolutionChart: React.FC<{
  timeline: Array<{ date: string; accuracy: number }>;
}> = ({ timeline }) => {
  const { t } = useTranslation();
  return (
    <section>
      <div className="flex items-center justify-between mb-12">
        <h2 className="text-4xl font-black italic uppercase manga-font tracking-tighter flex items-center gap-4">
          <TrendingUp className="w-10 h-10 text-blue-500" />{' '}
          {t('social.transparency.evolution_title', 'Évolution du Modèle Expert')}
        </h2>
        <Badge
          variant="neutral"
          className="!bg-white/5 !border-white/10 uppercase text-[10px] py-2 px-4"
        >
          Metric: Semantic Accuracy
        </Badge>
      </div>

      <Card className="!bg-navy-900/20 !border-white/5 p-10 h-[450px]">
        {timeline.length >= 2 ? (
          <Plot
            data={[
              {
                x: timeline.map((d) => d.date),
                y: timeline.map((d) => d.accuracy),
                type: 'scatter',
                mode: 'lines',
                fill: 'tozeroy',
                line: { color: '#3b82f6', width: 4, shape: 'spline' },
                fillcolor: 'rgba(59,130,246,0.18)',
                hovertemplate: 'Accuracy: %{y:.0%}<extra></extra>',
              },
            ]}
            layout={{
              autosize: true,
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              margin: { l: 44, r: 20, t: 10, b: 36 },
              xaxis: {
                gridcolor: 'rgba(255,255,255,0.03)',
                tickfont: { color: '#ffffff33', size: 10 },
                showline: false,
                zeroline: false,
              },
              yaxis: {
                gridcolor: 'rgba(255,255,255,0.03)',
                tickfont: { color: '#ffffff33', size: 10 },
                showline: false,
                zeroline: false,
                tickformat: '.0%',
              },
              font: { family: 'Montserrat', color: '#fff' },
              hovermode: 'x unified',
              showlegend: false,
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
          />
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
            <TrendingUp className="w-12 h-12 mb-4" />
            <p className="text-xs font-black uppercase tracking-widest">
              {t('social.transparency.not_enough_data', "Pas encore assez de données d'évaluation")}
            </p>
            <p className="text-[10px] font-bold uppercase tracking-widest mt-1 opacity-60">
              {t(
                'social.transparency.chart_hint',
                "La courbe apparaîtra dès plusieurs cycles d'évaluation enregistrés.",
              )}
            </p>
          </div>
        )}
      </Card>
    </section>
  );
};
