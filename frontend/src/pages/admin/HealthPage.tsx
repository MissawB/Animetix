import React from 'react';
import { Cpu, Database, Settings, Server, Activity } from 'lucide-react';
import { useHealth } from '../../features/admin/hooks/useHealth';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Skeleton } from '../../../components/ui/Skeleton';
import { useTranslation } from 'react-i18next';

const HealthPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading } = useHealth();

  return (
    <div className="container mx-auto p-6 pt-24 text-white">
        <h1 className="text-4xl font-black italic manga-font mb-12 tracking-tighter flex items-center gap-4">
            <Activity className="w-10 h-10 text-cyan-400" /> {t('admin.health.title')}
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <HealthCard title="BRAIN API" status={isLoading ? '...' : data?.brain_status} Icon={Cpu} color="cyan" loading={isLoading} />
            <HealthCard title="REDIS CACHE" status={isLoading ? '...' : data?.cache_status} Icon={Database} color="amber" loading={isLoading} />
            <HealthCard title="CELERY" status={isLoading ? '...' : data?.celery_status} Icon={Settings} color="purple" loading={isLoading} />
            <HealthCard title="POSTGRES" status={isLoading ? '...' : "Connected"} Icon={Server} color="emerald" loading={isLoading} />
        </div>
    </div>
  );
};

interface HealthCardProps {
  title: string;
  status: string | undefined;
  Icon: React.ElementType;
  color: string;
  loading?: boolean;
}

const HealthCard: React.FC<HealthCardProps> = ({ title, status, Icon, color, loading }) => (
    <Card padding="md" className="border-2 border-white/5 bg-gray-900/50 backdrop-blur-md">
        <div className="flex justify-between items-center">
            <h2 className="text-xl font-black italic manga-font flex items-center gap-3">
                <Icon className={`text-${color}-400 w-6 h-6`} /> {title}
            </h2>
            {loading ? (
                <Skeleton variant="rectangular" className="w-20 h-6" />
            ) : (
                <Badge variant={status === 'Online' || status === 'Connected' ? 'success' : 'danger'}>
                    {status}
                </Badge>
            )}
        </div>
    </Card>
);

export default HealthPage;

