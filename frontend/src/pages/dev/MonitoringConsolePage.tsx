import React from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Button } from "../../components/ui/Button";
import { apiClient } from "../../utils/apiClient";
import { useTranslation } from 'react-i18next';

const MonitoringConsolePage: React.FC = () => {
  const { t } = useTranslation();
  const triggerAction = async (action: string) => {
    try {
      // apiClient injects the CSRF token + Firebase auth header.
      await apiClient(`/api/monitoring/${action}/`, { method: 'POST', skipToast: true });
      alert(t('dev.monitoring.action_success', 'Action {{action}} triggered successfully', { action }));
    } catch {
      alert(t('dev.monitoring.action_error', 'Error triggering action'));
    }
  };

  return (
    <AnimatedPage>
      <div className="p-8">
        <h1 className="text-2xl font-black uppercase">{t('dev.monitoring.title', 'Console Pipeline')}</h1>
        <div className="flex gap-4 mt-6">
          <Button onClick={() => triggerAction('run_scraper')}>{t('dev.monitoring.run_scrapers_btn', 'Lancer Scrapers')}</Button>
          <Button onClick={() => triggerAction('sync_neo4j')}>{t('dev.monitoring.sync_neo4j_btn', 'Synchro Neo4j')}</Button>
        </div>
      </div>
    </AnimatedPage>
  );
};
export default MonitoringConsolePage;
