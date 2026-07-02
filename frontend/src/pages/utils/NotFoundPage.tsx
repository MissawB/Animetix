import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft, Ghost } from 'lucide-react';
import { Button } from "../../components/ui/Button";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const NotFoundPage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="min-h-[70vh] flex items-center justify-center px-6">
        <div className="text-center space-y-8 max-w-xl">
          {/* Glowing icon */}
          <div className="relative inline-block">
            <div className="absolute -inset-8 bg-yellow-400/10 rounded-full blur-3xl animate-pulse" />
            <div className="relative w-32 h-32 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-[2rem] flex items-center justify-center rotate-12 shadow-2xl mx-auto">
              <Ghost className="w-16 h-16 text-black" />
            </div>
          </div>

          {/* Error code */}
          <div>
            <h1 className="text-[10rem] leading-none font-black italic manga-font tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white/20 to-white/5 select-none">
              404
            </h1>
          </div>

          {/* Message */}
          <div className="space-y-3">
            <h2 className="text-3xl font-black italic manga-font uppercase tracking-tight">
              Dimension <span className="text-yellow-700 dark:text-yellow-400 text-glow">Inconnue</span>
            </h2>
            <p className="text-sm font-bold text-gray-600 dark:text-gray-400 uppercase tracking-[0.2em] max-w-md mx-auto">
              Cette page n'existe pas dans le multivers d'Animetix. Peut-être a-t-elle été absorbée par un trou noir narratif...
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Button
              as={Link}
              to="/"
              variant="primary"
              className="bg-yellow-400 !text-black border-none py-4 px-8 rounded-2xl shadow-xl hover:scale-105 transition-all font-black uppercase italic tracking-wider"
            >
              <Home className="w-5 h-5" /> Accueil
            </Button>
            <Button
              as="button"
              variant="outline"
              className="py-4 px-8 rounded-2xl font-black uppercase italic tracking-wider"
              onClick={() => window.history.back()}
            >
              <ArrowLeft className="w-5 h-5" /> Retour
            </Button>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default NotFoundPage;
