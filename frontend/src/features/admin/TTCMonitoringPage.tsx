import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { Card } from '../../components/ui/Card';
import { Brain, ArrowLeft, AlertTriangle, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../../api';

// Create a small helper to fetch
const fetchTTCStats = async () => {
  const response = await api.get('/admin/ttc-monitoring/');
  return response.data;
};

const TTCMonitoringPage = () => {
    const { data, isLoading } = useQuery({
        queryKey: ['ttc-monitoring'],
        queryFn: fetchTTCStats,
        refetchInterval: 5000 // Rafraîchissement régulier
    });

    if (isLoading) return <div>Loading...</div>;

    const summary = data?.summary || { total_allocated: 0, total_consumed: 0, efficiency: 100 };
    const logs = data?.logs || [];

    return (
        <AnimatedPage>
            <div className="max-w-7xl mx-auto px-6 py-16">
                <Link to="/admin/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white mb-8">
                    <ArrowLeft className="w-4 h-4" /> Retour MLOps
                </Link>
                <h1 className="text-4xl font-black italic uppercase mb-8">Dynamic Budget TTC</h1>
                
                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                    <Card padding="lg" className="bg-gray-900 border-white/10">
                        <p className="text-xs uppercase opacity-50 mb-2">Budget Alloué (24h)</p>
                        <p className="text-4xl font-black">{summary.total_allocated}</p>
                    </Card>
                    <Card padding="lg" className="bg-gray-900 border-white/10">
                        <p className="text-xs uppercase opacity-50 mb-2">Consommation Réelle</p>
                        <p className="text-4xl font-black">{summary.total_consumed}</p>
                    </Card>
                    <Card padding="lg" className={`bg-gray-900 border-white/10 ${summary.efficiency > 100 ? 'text-red-500' : 'text-green-500'}`}>
                        <p className="text-xs uppercase opacity-50 mb-2 text-white">Efficacité Cognitive</p>
                        <p className="text-4xl font-black">{summary.efficiency}%</p>
                    </Card>
                </div>

                {/* Table */}
                <Card padding="none" className="bg-gray-900 border-white/10 overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-white/5 text-[10px] uppercase font-black">
                            <tr>
                                <th className="p-4">Engine</th>
                                <th className="p-4">Alloué</th>
                                <th className="p-4">Consommé</th>
                                <th className="p-4">Statut</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map((log: any) => {
                                const overBudget = log.consumed > log.allocated;
                                return (
                                    <tr key={log.id} className="border-t border-white/5 text-sm">
                                        <td className="p-4 font-mono text-xs">{log.engine}</td>
                                        <td className="p-4">{log.allocated}</td>
                                        <td className="p-4">{log.consumed}</td>
                                        <td className="p-4">
                                            {overBudget ? (
                                                <span className="flex items-center gap-1 text-red-500 text-xs font-bold"><AlertTriangle className="w-3 h-3"/> Dépassement</span>
                                            ) : (
                                                <span className="flex items-center gap-1 text-green-500 text-xs font-bold"><CheckCircle className="w-3 h-3"/> Optimal</span>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </Card>
            </div>
        </AnimatedPage>
    );
};

export default TTCMonitoringPage;
