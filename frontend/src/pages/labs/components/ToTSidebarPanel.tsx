import React from 'react';
import { GitBranch, Search, Loader2, Info, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';

interface ToTSidebarPanelProps {
  query: string;
  setQuery: (val: string) => void;
  isPending: boolean;
  isStreaming: boolean;
  onGenerateTree: () => void;
  onStartStream: () => void;
  error: string | null;
  errorKind: 'auth' | 'payment' | 'generic' | null;
}

export const ToTSidebarPanel: React.FC<ToTSidebarPanelProps> = ({
  query,
  setQuery,
  isPending,
  isStreaming,
  onGenerateTree,
  onStartStream,
  error,
  errorKind,
}) => {
  return (
    <div className="w-96 flex-shrink-0 border-r border-white/5 bg-black/40 backdrop-blur-xl p-8 flex flex-col z-20 overflow-y-auto custom-scrollbar">
      <header className="mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-4">
          <GitBranch className="w-3 h-3" /> Recursive Reasoning Lab
        </div>
        <h1 className="text-4xl font-black italic manga-font tracking-tighter uppercase mb-4">
          TREE OF <span className="text-emerald-500 text-glow">THOUGHTS</span>
        </h1>
        <p className="text-[10px] font-bold opacity-30 uppercase tracking-widest leading-relaxed">
          Visualisez le raisonnement multi-branches (MCTS) de l'IA en temps réel.
        </p>
      </header>

      <div className="space-y-6">
        <div className="space-y-3">
          <label
            htmlFor="cognitive-query"
            className="text-[10px] font-black opacity-30 uppercase tracking-widest px-2 flex items-center gap-2"
          >
            <Search className="w-3 h-3" /> Requête Cognitive
          </label>
          <textarea
            id="cognitive-query"
            aria-label="Requête cognitive"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Entrez un problème complexe..."
            className="w-full h-32 bg-white/5 border-2 border-white/5 rounded-2xl p-4 text-sm font-bold text-white outline-none focus:border-emerald-500/50 transition-all resize-none placeholder:opacity-20"
          />
        </div>

        <Button
          onClick={onGenerateTree}
          disabled={isPending || isStreaming || !query.trim()}
          className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:scale-[1.02] active:scale-[0.98] transition-all border-none"
        >
          {isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "GÉNÉRER L'ARBRE"}
        </Button>

        <Button
          onClick={onStartStream}
          disabled={isPending || isStreaming || !query.trim()}
          className="w-full bg-white/5 hover:bg-white/10 text-emerald-300 py-4 rounded-2xl font-black italic uppercase border border-emerald-500/30 transition-all"
        >
          {isStreaming ? <Loader2 className="w-5 h-5 animate-spin" /> : 'STREAM EN DIRECT'}
        </Button>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400">
            <h4 className="text-[11px] font-black italic uppercase mb-1">
              {errorKind === 'auth'
                ? 'Connexion requise'
                : errorKind === 'payment'
                  ? 'Berrix insuffisants'
                  : 'Erreur'}
            </h4>
            <p className="text-[10px] font-bold opacity-80 leading-relaxed mb-3">{error}</p>
            {errorKind === 'auth' && (
              <Link to="/auth/login/">
                <Button className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded-xl font-black italic uppercase text-xs border-none">
                  Se connecter
                </Button>
              </Link>
            )}
            {errorKind === 'payment' && (
              <Link to="/power-station/">
                <Button className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded-xl font-black italic uppercase text-xs border-none">
                  Recharger des Berrix
                </Button>
              </Link>
            )}
          </div>
        )}
      </div>

      <div className="mt-12 space-y-8">
        <Card padding="md" className="bg-white/5 border-white/5 opacity-60">
          <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 text-emerald-400 flex items-center gap-2">
            <Info className="w-3 h-3" /> Légende des Nœuds
          </h4>
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-[8px] font-black uppercase">
              <div className="w-2 h-2 rounded-full bg-white" /> Point d'Origine
            </div>
            <div className="flex items-center gap-3 text-[8px] font-black uppercase">
              <div className="w-2 h-2 rounded-full bg-emerald-500" /> Chemin Sélectionné
            </div>
            <div className="flex items-center gap-3 text-[8px] font-black uppercase">
              <div className="w-2 h-2 rounded-full bg-red-800" /> Branche Élaguée
            </div>
            <div className="flex items-center gap-3 text-[8px] font-black uppercase">
              <div className="w-2 h-2 rounded-full bg-yellow-400" /> Conclusion Finale
            </div>
          </div>
        </Card>

        <Card
          padding="md"
          className="bg-black/40 border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.1)] relative overflow-hidden group"
        >
          <div className="absolute -right-6 -bottom-6 opacity-5 group-hover:opacity-10 transition-opacity">
            <GitBranch className="w-32 h-32 text-emerald-500" />
          </div>
          <h4 className="text-[11px] font-black italic manga-font uppercase mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-400" /> Guide de l'Arbre
          </h4>
          <div className="space-y-3 relative z-10">
            <p className="text-[9px] font-bold uppercase tracking-wider text-white/50 leading-relaxed">
              <span className="text-emerald-400">Multi-Pensée :</span> L'IA n'écrit pas d'un seul
              trait. Elle explore plusieurs "branches" de réflexion en parallèle pour trouver la
              meilleure solution.
            </p>
            <p className="text-[9px] font-bold uppercase tracking-wider text-white/50 leading-relaxed">
              <span className="text-emerald-400">L'Élagage :</span> Si une branche mène à une
              impasse logique, l'IA l'abandonne (en rouge) pour se concentrer sur les chemins
              prometteurs (en vert).
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
