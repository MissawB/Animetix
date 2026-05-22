import React from 'react';
import { useAdminEval } from './hooks/useAdminEval';
import { useTranslation } from 'react-i18next';
import { Card } from '../../components/ui/Card';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { Brain, Activity, Target } from 'lucide-react';

interface Stats {
  total: number;
  avg_faith: number;
  avg_rel: number;
  avg_prec: number;
}

interface EvalResult {
  id: number;
  faithfulness: number;
  relevancy: number;
  precision: number;
  hallucination_detected: boolean;
  created_at: string;
}

const AdminEvalPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, loading } = useAdminEval();

  if (loading) return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );

  if (!data) return (
    <div className="flex justify-center items-center py-20 px-6">
      <Card className="text-center border-red-500/50 max-w-md">
        <h2 className="text-2xl font-black text-red-500 mb-4 italic uppercase">{t('common.error')}</h2>
        <p className="opacity-60 font-bold mb-6">{t('admin.eval.error')}</p>
      </Card>
    </div>
  );

  const { stats } = data as { stats: Stats };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-16">
          <div>
            <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase mb-2">
              IA <span className="text-blue-500">QUALITY</span> CONTROL
            </h1>
            <p className="text-xs font-black opacity-30 uppercase tracking-[0.3em]">
              {t('admin.eval.title')}
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-navy-900 px-6 py-3 rounded-2xl border border-gray-100 dark:border-white/5 shadow-inner">
            <span className="text-[10px] font-black opacity-40 uppercase tracking-widest block mb-1">Total Evals</span>
            <span className="text-2xl font-black italic">{stats.total}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            <StatCard 
              title={t('admin.eval.stats.faithfulness')} 
              value={stats.avg_faith} 
              icon={<Brain className="w-6 h-6" />}
              color="blue" 
            />
            <StatCard 
              title={t('admin.eval.stats.relevancy')} 
              value={stats.avg_rel} 
              icon={<Activity className="w-6 h-6" />}
              color="emerald" 
            />
            <StatCard 
              title={t('admin.eval.stats.precision')} 
              value={stats.avg_prec} 
              icon={<Target className="w-6 h-6" />}
              color="purple" 
            />
        </div>

        {/* Table/Details could go here in future */}
    </div>
  );
};

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'emerald' | 'purple';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => {
  const colors = {
    blue: 'text-blue-500 border-blue-500/20 bg-blue-500/5',
    emerald: 'text-emerald-500 border-emerald-500/20 bg-emerald-500/5',
    purple: 'text-purple-500 border-purple-500/20 bg-purple-500/5',
  };

  return (
    <Card padding="lg" className={`group hover:scale-[1.02] transition-all border-2 ${colors[color].split(' ')[1]} ${colors[color].split(' ')[2]}`}>
        <div className="flex justify-between items-start mb-6">
          <div className={`p-3 rounded-xl bg-white dark:bg-navy-800 shadow-lg ${colors[color].split(' ')[0]}`}>
            {icon}
          </div>
          <div className="text-[10px] font-black opacity-20 uppercase tracking-widest group-hover:opacity-40 transition-opacity">
            Score Moyen
          </div>
        </div>
        <h3 className="text-xs font-black uppercase opacity-60 mb-2 tracking-widest">{title}</h3>
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-black italic">{value.toFixed(3)}</span>
          <span className="text-sm font-black opacity-30">/ 1.000</span>
        </div>
        <div className="mt-6 w-full h-1 bg-gray-100 dark:bg-white/5 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full ${color === 'blue' ? 'bg-blue-500' : color === 'emerald' ? 'bg-emerald-500' : 'bg-purple-500'}`} 
            style={{ width: `${value * 100}%` }}
          />
        </div>
    </Card>
  );
};

export default AdminEvalPage;
