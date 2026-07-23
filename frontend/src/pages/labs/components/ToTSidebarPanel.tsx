import React from 'react';
import { Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { LAB_INPUT, LAB_LABEL, LAB_CTA, LAB_BTN_GHOST } from './shared/LabKit';

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

const LEGEND = [
  { color: '#F4F1E8', label: "Point d'origine" },
  { color: '#FDB913', label: 'Chemin sélectionné' },
  { color: '#8F94A5', label: 'Branche élaguée' },
  { color: '#E8442B', label: 'Conclusion finale' },
] as const;

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
    <div className="custom-scrollbar z-20 flex w-96 flex-shrink-0 flex-col overflow-y-auto border-r border-[#F4F1E8]/10 bg-[#0F1016] p-8">
      <header className="mb-10">
        <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
          Protocole · ToT
        </span>
        <h1 className="font-manga mt-3 text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8]">
          TREE OF <span className="text-[#E8442B]">THOUGHTS</span>
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-[#8F94A5]">
          L'IA explore plusieurs branches de raisonnement en parallèle ; le graphe se dessine sous
          tes yeux.
        </p>
      </header>

      <div className="space-y-6">
        <div className="space-y-2">
          <label htmlFor="cognitive-query" className={LAB_LABEL}>
            Requête cognitive
          </label>
          <textarea
            id="cognitive-query"
            aria-label="Requête cognitive"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Pose un problème complexe…"
            className={`${LAB_INPUT} h-32 resize-none`}
          />
        </div>

        <button
          type="button"
          onClick={onGenerateTree}
          disabled={isPending || isStreaming || !query.trim()}
          className={LAB_CTA}
        >
          {isPending ? <Loader2 className="h-6 w-6 animate-spin" /> : "GÉNÉRER L'ARBRE"}
        </button>

        <button
          type="button"
          onClick={onStartStream}
          disabled={isPending || isStreaming || !query.trim()}
          className={`${LAB_BTN_GHOST} w-full justify-center`}
        >
          {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Suivre en direct'}
        </button>

        {error && (
          <div className="rounded-2xl border border-[#E8442B]/25 bg-[#E8442B]/[0.06] p-4">
            <h4 className="text-[11px] font-black uppercase tracking-widest text-[#E8442B]">
              {errorKind === 'auth'
                ? 'Connexion requise'
                : errorKind === 'payment'
                  ? 'Berrix insuffisants'
                  : 'Erreur'}
            </h4>
            <p className="mb-3 mt-1 text-[11px] leading-relaxed text-[#F4F1E8]/80">{error}</p>
            {errorKind === 'auth' && (
              <Link to="/auth/login/" className="block">
                <span className={`${LAB_CTA} py-3 text-xs`}>Se connecter</span>
              </Link>
            )}
            {errorKind === 'payment' && (
              <Link to="/power-station/" className="block">
                <span className={`${LAB_CTA} py-3 text-xs`}>Recharger des Berrix</span>
              </Link>
            )}
          </div>
        )}
      </div>

      <div className="mt-10 space-y-6">
        <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-5">
          <h4 className="mb-4 text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
            Légende des nœuds
          </h4>
          <div className="space-y-3">
            {LEGEND.map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]"
              >
                <span
                  className="h-2 w-2 flex-none rounded-full"
                  style={{ backgroundColor: item.color }}
                  aria-hidden
                />
                {item.label}
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-5">
          <h4 className="mb-3 text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
            Guide du raisonnement
          </h4>
          <div className="space-y-3">
            <p className="text-xs leading-relaxed text-[#8F94A5]">
              <span className="font-black text-[#F4F1E8]">Multi-pensée :</span> l'IA n'écrit pas
              d'un seul trait, elle explore plusieurs branches de réflexion en parallèle pour
              trouver la meilleure solution.
            </p>
            <p className="text-xs leading-relaxed text-[#8F94A5]">
              <span className="font-black text-[#F4F1E8]">Élagage :</span> quand une branche mène à
              une impasse logique, l'IA l'abandonne pour se concentrer sur les chemins prometteurs.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};
