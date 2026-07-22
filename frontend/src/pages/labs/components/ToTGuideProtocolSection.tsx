import React from 'react';
import { GitBranch, Sparkles } from 'lucide-react';
import { Card } from '../../../components/ui/Card';

export const ToTGuideProtocolSection: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-6 pb-16">
      <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card
          padding="lg"
          className="bg-black/40 border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.1)] relative overflow-hidden group"
        >
          <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
            <GitBranch className="w-64 h-64 text-emerald-500" />
          </div>
          <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-emerald-400" /> Guide du Raisonnement
          </h4>
          <div className="space-y-4 relative z-10">
            <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
              <span className="text-emerald-400">La Question :</span> Posez un problème complexe.
              L'IA ne répond pas d'un seul jet : elle explore plusieurs pistes de réflexion en
              parallèle avant de conclure.
            </p>
            <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
              <span className="text-emerald-400">La Lecture :</span> Chaque point est une idée notée
              par l'IA. Vert = piste retenue, rouge = branche abandonnée, jaune = conclusion.
              Cliquez sur un nœud pour lire sa trace de pensée.
            </p>
            <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
              <span className="text-emerald-400">Les Deux Modes :</span> "Générer l'arbre" renvoie
              l'arbre complet d'un coup ; "Stream en direct" affiche les nœuds au fur et à mesure
              (connexion requise, consomme des Berrix).
            </p>
          </div>
        </Card>

        <div className="p-12 rounded-[4rem] bg-gradient-to-br from-emerald-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
          <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-emerald-200/60">
            Recherche arborescente type Tree-of-Thoughts : le modèle génère des pensées candidates,
            les évalue par un score de confiance et élague les branches faibles, comme dans une
            exploration MCTS. <br />
            Le mode direct diffuse chaque nœud via un flux SSE, rendu en temps réel dans un graphe
            force-directed.
          </p>
        </div>
      </div>
    </div>
  );
};
