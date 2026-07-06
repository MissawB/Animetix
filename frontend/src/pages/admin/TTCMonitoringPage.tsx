import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Card } from "../../components/ui/Card";
import { ArrowLeft, AlertTriangle, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from "../../utils/apiClient";

interface TTCLog {
    id: number;
    engine: string;
    allocated: number;
    consumed: number;
}

interface TTCMonitoringData {
    summary: {
        total_allocated: number;
        total_consumed: number;
        efficiency: number;
    };
    logs: TTCLog[];
}

// Create a small helper to fetch
const fetchTTCStats = async (): Promise<TTCMonitoringData> => {
  return apiClient('/api/v1/admin/ttc-monitoring/');
};

const TTCMonitoringPage: React.FC = () => {
    const { t } = useTranslation();
    const { data, isLoading } = useQuery<TTCMonitoringData>({
        queryKey: ['ttc-monitoring'],
        queryFn: fetchTTCStats,
        refetchInterval: 5000 // Rafraîchissement régulier
    });

    if (isLoading) return (
        <div className="max-w-7xl mx-auto px-6 py-32 flex justify-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );

    const summary = data?.summary || { total_allocated: 0, total_consumed: 0, efficiency: 100 };
    const logs = data?.logs || [];

    return (
        <AnimatedPage>
            <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay">
                <div className="max-w-7xl mx-auto px-6 py-16">
                    <Link to="/admin/dashboard/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-black dark:hover:text-white mb-8 no-underline">
                        <ArrowLeft className="w-4 h-4" /> {t('admin.common.back_admin', 'Retour Administration')}
                    </Link>
                    <h1 className="text-4xl font-black italic manga-font uppercase mb-12 text-black dark:text-white">
                      DYNAMIC <span className="text-blue-500">BUDGET</span> TTC
                    </h1>
                    
                    {/* KPI Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12 text-black dark:text-white">
                        <Card padding="lg" className="bg-white dark:bg-[#0f0f1a] border-none shadow-xl">
                            <p className="text-[10px] font-black uppercase opacity-40 mb-2">{t('admin.ttc.budget_allocated', 'Budget Alloué (24h)')}</p>
                            <p className="text-4xl font-black italic">{summary.total_allocated}</p>
                        </Card>
                        <Card padding="lg" className="bg-white dark:bg-[#0f0f1a] border-none shadow-xl">
                            <p className="text-[10px] font-black uppercase opacity-40 mb-2">{t('admin.ttc.actual_consumed', 'Consommation Réelle')}</p>
                            <p className="text-4xl font-black italic">{summary.total_consumed}</p>
                        </Card>
                        <Card padding="lg" className={`bg-white dark:bg-[#0f0f1a] border-none shadow-xl ${summary.efficiency > 100 ? 'text-red-500' : 'text-emerald-500'}`}>
                            <p className="text-[10px] font-black uppercase opacity-40 mb-2 text-black dark:text-white">{t('admin.ttc.cognitive_efficiency', 'Efficacité Cognitive')}</p>
                            <p className="text-4xl font-black italic">{summary.efficiency}%</p>
                        </Card>
                    </div>

                    {/* Table */}
                    <Card padding="none" className="bg-white dark:bg-[#0f0f1a] border-none shadow-2xl overflow-hidden">
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-black dark:text-white">
                              <thead className="bg-gray-50 dark:bg-black/40 text-[10px] uppercase font-black text-gray-400 border-b border-black/5 dark:border-white/5">
                                  <tr>
                                      <th className="p-6">Inference Engine</th>
                                      <th className="p-6">{t('admin.ttc.allocated', 'Alloué')}</th>
                                      <th className="p-6">{t('admin.ttc.consumed', 'Consommé')}</th>
                                      <th className="p-6 text-right">{t('common.status', 'Statut')}</th>
                                  </tr>
                              </thead>
                              <tbody className="divide-y divide-black/5 dark:divide-white/5">
                                  {logs.map((log: TTCLog) => {
                                      const overBudget = log.consumed > log.allocated;
                                      return (
                                          <tr key={log.id} className="hover:bg-gray-50/50 dark:hover:bg-white/5 transition-colors">
                                              <td className="p-6 font-mono text-[10px] font-black uppercase text-blue-500">{log.engine}</td>
                                              <td className="p-6 font-black italic">{log.allocated}</td>
                                              <td className="p-6 font-black italic">{log.consumed}</td>
                                              <td className="p-6 text-right">
                                                  {overBudget ? (
                                                      <span className="inline-flex items-center gap-2 bg-red-500/10 text-red-500 px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest border border-red-500/20"><AlertTriangle className="w-3 h-3"/> Over Budget</span>
                                                  ) : (
                                                      <span className="inline-flex items-center gap-2 bg-emerald-500/10 text-emerald-500 px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest border border-emerald-500/20"><CheckCircle className="w-3 h-3"/> Optimal</span>
                                                  )}
                                              </td>
                                          </tr>
                                      );
                                  })}
                              </tbody>
                          </table>
                        </div>
                    </Card>
                </div>
            </div>
        </AnimatedPage>
    );
};

export default TTCMonitoringPage;
