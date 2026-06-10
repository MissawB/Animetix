import React, { useState, useEffect } from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Loader2, Play, Pause, Square, List } from 'lucide-react';
import { apiClient } from "../../utils/apiClient";
import { useQuery, useMutation } from '@tanstack/react-query';

const MLOpsConsolePage: React.FC = () => {
  const [dpoStatus, setDpoStatus] = useState<string>('idle');
  const [metrics, setMetrics] = useState<any>({});
  const [adapters, setAdapters] = useState<any>({});

  // Fetch DPO status and metrics
  const dpoQuery = useQuery({
    queryKey: ['dpoStatus'],
    queryFn: () => apiClient('/api/mlops/dpo-loop/', { method: 'GET' }),
    // refetchInterval: 5000, // Polling toutes les 5 secondes
  });

  useEffect(() => {
    if (dpoQuery.data) {
      setDpoStatus(dpoQuery.data.status);
      setMetrics(dpoQuery.data.metrics);
    }
  }, [dpoQuery.data]);

  // Fetch adapters info
  const adaptersQuery = useQuery({
    queryKey: ['mlopsAdapters'],
    queryFn: () => apiClient('/api/mlops/adapters/', { method: 'GET' }),
    // refetchInterval: 10000, // Polling toutes les 10 secondes
  });

  useEffect(() => {
    if (adaptersQuery.data) {
      setAdapters(adaptersQuery.data);
    }
  }, [adaptersQuery.data]);

  // DPO loop actions
  const dpoMutation = useMutation({
    mutationFn: (action: 'start' | 'pause' | 'stop') => apiClient('/api/mlops/dpo-loop/', {
      method: 'POST',
      body: JSON.stringify({ action })
    }),
    onSuccess: () => dpoQuery.refetch(), // Recharger le statut après une action
  });

  return (
    <AnimatedPage>
      <div className="p-8 min-h-screen bg-[#0a0a12] text-white">
        <h1 className="text-3xl font-black italic manga-font uppercase mb-8">Console MLOps</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* DPO Feedback Loop */}
          <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-xl shadow-2xl">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><List className="w-5 h-5 text-purple-400" /> DPO Feedback Loop</h2>
            <p>Statut: <span className={`font-bold ${dpoStatus === 'running' ? 'text-green-500' : dpoStatus === 'paused' ? 'text-yellow-500' : 'text-gray-500'}`}>{dpoStatus.toUpperCase()}</span></p>
            <p>Last Loss: {metrics.last_loss?.toFixed(4) || 'N/A'}</p>
            <p>Last Accuracy: {metrics.last_accuracy?.toFixed(4) || 'N/A'}</p>

            <div className="flex gap-4 mt-4">
              <Button onClick={() => dpoMutation.mutate('start')} disabled={dpoMutation.isPending || dpoStatus === 'running'}>
                {dpoMutation.isPending && dpoMutation.variables === 'start' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Start
              </Button>
              <Button onClick={() => dpoMutation.mutate('pause')} disabled={dpoMutation.isPending || dpoStatus !== 'running'}>
                {dpoMutation.isPending && dpoMutation.variables === 'pause' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Pause className="w-4 h-4" />} Pause
              </Button>
              <Button onClick={() => dpoMutation.mutate('stop')} disabled={dpoMutation.isPending || dpoStatus === 'idle'}>
                {dpoMutation.isPending && dpoMutation.variables === 'stop' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />} Stop
              </Button>
            </div>
          </Card>

          {/* Adapters Management */}
          <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-xl shadow-2xl">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><List className="w-5 h-5 text-blue-400" /> Gestion des Adaptateurs</h2>
            {Object.entries(adapters).map(([type, adapterInfo]: [string, any]) => (
              <div key={type} className="mb-4">
                <h3 className="text-lg font-semibold capitalize">{type} Adapters:</h3>
                <p>Active: <span className="font-bold text-green-400">{adapterInfo.active}</span></p>
                <p>Available: {adapterInfo.available?.join(', ') || 'N/A'}</p>
              </div>
            ))}
          </Card>
        </div>

        {/* Placeholder for Logs */}
        <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-xl shadow-2xl mt-8">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><List className="w-5 h-5 text-yellow-400" /> Logs de Training</h2>
            <div className="h-64 bg-black p-4 rounded-md overflow-auto text-sm font-mono text-gray-300">
                <p>Log line 1...</p>
                <p>Log line 2...</p>
                <p>Log line 3...</p>
            </div>
        </Card>

      </div>
    </AnimatedPage>
  );
};
export default MLOpsConsolePage;
