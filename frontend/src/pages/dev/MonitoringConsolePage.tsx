import React from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Button } from "../../components/ui/Button";

const MonitoringConsolePage: React.FC = () => {
  const triggerAction = async (action: string) => {
    try {
      const response = await fetch(`/api/monitoring/${action}/`, { 
        method: 'POST',
        headers: {
          'X-CSRFToken': document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || ''
        }
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      alert(`Action ${action} triggered successfully`);
    } catch (error) {
      console.error('Error triggering action:', error);
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
