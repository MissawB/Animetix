import React from 'react';
import { statusConfig } from '../../../features/admin/types/clusterHealth';

export const StatusDot: React.FC<{ status: string; size?: 'sm' | 'md' }> = ({
  status,
  size = 'sm',
}) => {
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.offline;
  const sizeClass = size === 'md' ? 'w-3 h-3' : 'w-2 h-2';
  return (
    <span className="relative flex items-center">
      <span className={`${sizeClass} rounded-full ${config.bg} ${config.border} border`} />
      {status === 'online' && (
        <span
          className={`absolute ${sizeClass} rounded-full bg-emerald-400 animate-ping opacity-30`}
        />
      )}
    </span>
  );
};
