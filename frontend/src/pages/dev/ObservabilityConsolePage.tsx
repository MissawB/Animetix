import React, { useState } from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Button } from "../../components/ui/Button";

const ObservabilityConsolePage: React.FC = () => {
  const [threshold, setThreshold] = useState(0.5);

  return (
    <AnimatedPage>
      <div className="p-8">
        <h1 className="text-2xl font-black uppercase">Console Observabilité</h1>
        <div className="mt-6">
          <label>Seuil de sécurité: {threshold}</label>
          <input type="range" min="0" max="1" step="0.1" value={threshold} onChange={(e) => setThreshold(parseFloat(e.target.value))} />
          <Button onClick={() => console.log('Update', threshold)}>Appliquer</Button>
        </div>
      </div>
    </AnimatedPage>
  );
};
export default ObservabilityConsolePage;