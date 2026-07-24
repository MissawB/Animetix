import React from 'react';
import { TrendingUp } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Plot from '../../../components/LazyPlot';
import { LabPanel } from '../../labs/components/shared/LabKit';

/** Semantic-accuracy evolution chart. The Plotly chart (lazy-loaded) renders
 *  only from two data points on; otherwise a "not enough data" placeholder. */
export const TransparencyEvolutionChart: React.FC<{
  timeline: Array<{ date: string; accuracy: number }>;
}> = ({ timeline }) => {
  const { t } = useTranslation();
  return (
    <LabPanel
      title={t('social.transparency.evolution_title', 'Évolution du Modèle Expert')}
      corner={
        <span className="flex items-center gap-1.5">
          <TrendingUp className="h-3.5 w-3.5" aria-hidden="true" /> Metric: Semantic Accuracy
        </span>
      }
    >
      <div className="h-[420px]">
        {timeline.length >= 2 ? (
          <Plot
            data={[
              {
                x: timeline.map((d) => d.date),
                y: timeline.map((d) => d.accuracy),
                type: 'scatter',
                mode: 'lines',
                fill: 'tozeroy',
                line: { color: '#FDB913', width: 4, shape: 'spline' },
                fillcolor: 'rgba(253,185,19,0.15)',
                hovertemplate: 'Accuracy: %{y:.0%}<extra></extra>',
              },
            ]}
            layout={{
              autosize: true,
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              margin: { l: 44, r: 20, t: 10, b: 36 },
              xaxis: {
                gridcolor: 'rgba(244,241,232,0.05)',
                tickfont: { color: '#8F94A5', size: 10 },
                showline: false,
                zeroline: false,
              },
              yaxis: {
                gridcolor: 'rgba(244,241,232,0.05)',
                tickfont: { color: '#8F94A5', size: 10 },
                showline: false,
                zeroline: false,
                tickformat: '.0%',
              },
              font: { family: 'Montserrat', color: '#F4F1E8' },
              hovermode: 'x unified',
              showlegend: false,
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center text-center text-[#8F94A5]">
            <TrendingUp className="mb-4 h-12 w-12 opacity-40" aria-hidden="true" />
            <p className="text-xs font-black uppercase tracking-widest">
              {t('social.transparency.not_enough_data', "Pas encore assez de données d'évaluation")}
            </p>
            <p className="mt-1 text-[10px] font-bold uppercase tracking-widest text-[#8F94A5]/70">
              {t(
                'social.transparency.chart_hint',
                "La courbe apparaîtra dès plusieurs cycles d'évaluation enregistrés.",
              )}
            </p>
          </div>
        )}
      </div>
    </LabPanel>
  );
};
