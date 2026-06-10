import React from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const ApiHubPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0a0a12] text-white p-6">
        <h1 className="text-3xl font-black italic manga-font uppercase mb-8">API Hub</h1>
        <iframe 
            src="/api/schema/swagger-ui/" 
            className="w-full h-[80vh] border-none rounded-xl"
            title="Swagger UI"
        />
      </div>
    </AnimatedPage>
  );
};

export default ApiHubPage;
