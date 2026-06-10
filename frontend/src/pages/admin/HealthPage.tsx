import React from 'react';
import { Cpu, Database, Settings, Server, Activity } from 'lucide-react';
import { useHealth } from '../../features/admin/hooks/useHealth';
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Skeleton } from "../../components/ui/Skeleton";
import { useTranslation } from 'react-i18next';

import { AnimatedPage } from "../../components/ui/AnimatedPage";

const HealthPage: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading } = useHealth();

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay">
        <div className="max-w-7xl mx-auto px-6 py-12 text-black dark:text-white">
            <h1 className="text-4xl md:text-5xl font-black italic manga-font mb-16 tracking-tighter flex items-center gap-4">
                <Activity className="w-10 h-10 text-blue-500" /> {t('admin.health.title')}
            </h1>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <HealthCard title="BRAIN API" status={isLoading ? '...' : data?.brain_status} Icon={Cpu} color="blue" loading={isLoading} />
                <HealthCard title="REDIS CACHE" status={isLoading ? '...' : data?.cache_status} Icon={Database} color="amber" loading={isLoading} />
                <HealthCard title="CELERY" status={isLoading ? '...' : data?.celery_status} Icon={Settings} color="purple" loading={isLoading} />
                <HealthCard title="POSTGRES" status={isLoading ? '...' : "Connected"} Icon={Server} color="emerald" loading={isLoading} />
            </div>
        </div>
      </div>
    </AnimatedPage>
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
    <Card padding="lg" className="border-none shadow-xl bg-white dark:bg-[#0f0f1a]">
        <div className="flex justify-between items-center">
            <h2 className="text-xl font-black italic manga-font flex items-center gap-3">
                <Icon className={`text-${color}-500 w-6 h-6`} /> {title}
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


