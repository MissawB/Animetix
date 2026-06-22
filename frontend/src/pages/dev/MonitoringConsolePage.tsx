import React from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Button } from "../../components/ui/Button";
import { apiClient } from "../../utils/apiClient";

const MonitoringConsolePage: React.FC = () => {
  const triggerAction = async (action: string) => {
    try {
      // apiClient injects the CSRF token + Firebase auth header.
      await apiClient(`/api/monitoring/${action}/`, { method: 'POST', skipToast: true });
      alert(`Action ${action} triggered successfully`);
    } catch {
      alert('Error triggering action');
    }
  };

  return (
    <AnimatedPage>
      <div className="p-8">
        <h1 className="text-2xl font-black uppercase">Console Pipeline</h1>
        <div className="flex gap-4 mt-6">
          <Button onClick={() => triggerAction('run_scraper')}>Lancer Scrapers</Button>
          <Button onClick={() => triggerAction('sync_neo4j')}>Synchro Neo4j</Button>
        </div>
      </div>
    </AnimatedPage>
  );
};
export default MonitoringConsolePage;
