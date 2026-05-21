import React, { useState, useEffect } from 'react';

const AdminEvalPage = () => {
  const [stats, setStats] = useState({ total: 0, avg_faith: 0, avg_rel: 0, avg_prec: 0 });
  const [results, setResults] = useState([]);
  const [hallucinationCount, setHallucinationCount] = useState(0);

  useEffect(() => {
    // Dans une vraie implémentation, on ferait un appel API vers un nouvel endpoint admin
    // Pour l'instant, on simule ou on appelle une structure existante si disponible
    fetch('/api/v1/admin/ai_eval/data/')
      .then(res => res.json())
      .then(data => {
        setStats(data.stats);
        setResults(data.results);
        setHallucinationCount(data.hallucination_count);
      })
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="container mx-auto px-6 py-12 text-white">
        <h1 className="text-4xl mb-12">IA QUALITY CONTROL</h1>
        {/* Grilles de stats similaires au template */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <StatCard title="Faithfulness" value={stats.avg_faith} color="blue" />
            <StatCard title="Relevancy" value={stats.avg_rel} color="emerald" />
            <StatCard title="Precision" value={stats.avg_prec} color="purple" />
        </div>
        {/* Table ici... */}
    </div>
  );
};

const StatCard = ({ title, value, color }) => (
    <div className={`p-8 rounded-3xl border-2 border-${color}-500/20 bg-gray-900`}>
        <h3 className="text-lg mb-4">{title}</h3>
        <div className="text-5xl font-black">{value.toFixed(2)}</div>
    </div>
);

export default AdminEvalPage;
