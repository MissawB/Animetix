import React from 'react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Timeline } from "../../components/video/Timeline";
import { Inspector } from "../../components/video/Inspector";

const VideoRagPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0a0a12] text-white p-6">
        <h1 className="text-3xl font-black italic manga-font uppercase">Video-RAG Explorer</h1>
        <div className="mt-8 flex flex-col gap-6">
            <Timeline />
            <Inspector />
        </div>
      </div>
    </AnimatedPage>
  );
};

export default VideoRagPage;
