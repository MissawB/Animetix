import React from 'react';
import { Thermometer, Activity, HardDrive } from 'lucide-react';
import { GpuInfo } from '../../../features/admin/types/clusterHealth';

export const GpuMiniBar: React.FC<{ gpu: GpuInfo }> = ({ gpu }) => {
  const tempColor =
    gpu.temperature_c > 75
      ? 'bg-red-500'
      : gpu.temperature_c > 55
        ? 'bg-amber-500'
        : 'bg-emerald-500';
  const utilColor =
    gpu.utilization_pct > 85
      ? 'bg-red-500'
      : gpu.utilization_pct > 50
        ? 'bg-cyan-500'
        : 'bg-emerald-500';
  const memPct = (gpu.memory_used_gb / gpu.memory_total_gb) * 100;

  return (
    <div className="flex items-center gap-3 py-1.5 px-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors group">
      <span className="text-[9px] font-black uppercase opacity-30 w-16 shrink-0 tracking-wider">
        {gpu.name}
      </span>

      {/* Temperature */}
      <div className="flex items-center gap-1.5 w-20">
        <Thermometer className="w-3 h-3 opacity-30" />
        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className={`h-full ${tempColor} transition-all duration-700`}
            style={{ width: `${Math.min(gpu.temperature_c, 100)}%` }}
          />
        </div>
        <span className="text-[9px] font-bold opacity-40 w-7 text-right">{gpu.temperature_c}°</span>
      </div>

      {/* Utilization */}
      <div className="flex items-center gap-1.5 w-20">
        <Activity className="w-3 h-3 opacity-30" />
        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className={`h-full ${utilColor} transition-all duration-700`}
            style={{ width: `${gpu.utilization_pct}%` }}
          />
        </div>
        <span className="text-[9px] font-bold opacity-40 w-7 text-right">
          {gpu.utilization_pct}%
        </span>
      </div>

      {/* Memory */}
      <div className="flex items-center gap-1.5 w-24">
        <HardDrive className="w-3 h-3 opacity-30" />
        <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full bg-violet-500 transition-all duration-700"
            style={{ width: `${memPct}%` }}
          />
        </div>
        <span className="text-[9px] font-bold opacity-40 w-14 text-right">
          {gpu.memory_used_gb}/{gpu.memory_total_gb}G
        </span>
      </div>
    </div>
  );
};
