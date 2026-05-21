import React, { useState, useEffect } from 'react';
import { Cpu, Database, Settings, Server } from 'lucide-react';

const HealthPage = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch('/api/v1/admin/health/')
      .then(res => res.json())
      .then(setData)
      .catch(err => console.error(err));
  }, []);

  if (!data) return <div className="text-white">Chargement...</div>;

  return (
    <div className="container mx-auto p-6 pt-24 text-white">
        <h1 className="text-3xl mb-8 font-bold text-cyan-400">HEALTH DASHBOARD</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <HealthCard title="BRAIN API" status={data.brain_status} Icon={Cpu} color="cyan" />
            <HealthCard title="REDIS CACHE" status={data.cache_status} Icon={Database} color="amber" />
            <HealthCard title="CELERY" status={data.celery_status} Icon={Settings} color="purple" />
            <HealthCard title="POSTGRES" status="Connected" Icon={Server} color="emerald" />
        </div>
    </div>
  );
};

const HealthCard = ({ title, status, Icon, color }) => (
    <div className={`bg-gray-800 p-6 rounded-2xl border-2 border-gray-700`}>
        <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold flex items-center">
                <Icon className={`mr-2 text-${color}-400`} /> {title}
            </h2>
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${status === 'Online' || status === 'Connected' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                {status}
            </span>
        </div>
    </div>
);

export default HealthPage;
