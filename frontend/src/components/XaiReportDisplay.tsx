import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { 
    Layers, 
    ShieldCheck, 
    AlertCircle, 
    ChevronRight, 
    BookOpen, 
    Target, 
    Atom,
    BarChart,
    Lightbulb
} from 'lucide-react';
// Type généré depuis le schéma OpenAPI backend ; ré-exporté pour les consommateurs
// existants (ex. ExpertNexusPage importe `XaiReport` depuis ce module).
import type { XaiReport } from '../types';

export type { XaiReport };

interface XaiReportDisplayProps {
  xaiReport: XaiReport | null;
}

const XaiReportDisplay: React.FC<XaiReportDisplayProps> = ({ xaiReport }) => {
  const [expanded, setExpanded] = useState(false);

  if (!xaiReport) {
    return null;
  }

  const { 
    query_intent, 
    retrieval_attribution, 
    internal_diagnostics, 
    uncertainty, 
    final_confidence 
  } = xaiReport;

  const confidenceScore = uncertainty?.confidence_score ?? 0;
  const confidenceColor = confidenceScore >= 0.7 ? 'bg-emerald-500' :
                          confidenceScore >= 0.4 ? 'bg-yellow-500' : 'bg-red-500';

  const reliabilityBadge = uncertainty?.is_reliable ? (
    <Badge className="bg-emerald-500/20 text-emerald-500 border-emerald-500/30">
      <ShieldCheck className="w-3 h-3 mr-1" /> Fiable
    </Badge>
  ) : (
    <Badge className="bg-yellow-500/20 text-yellow-500 border-yellow-500/30">
      <AlertCircle className="w-3 h-3 mr-1" /> Vérification Recommandée
    </Badge>
  );

  return (
    <Card padding="lg" className="bg-navy-950/50 border-white/5 shadow-2xl rounded-3xl mt-8">
      <button 
        className="w-full flex justify-between items-center cursor-pointer bg-transparent border-none p-0 outline-none group" 
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <h3 className="text-xl font-bold italic text-white flex items-center gap-3 transition-colors group-hover:text-blue-400">
          <Layers className="w-6 h-6 text-blue-500" />
          <span className="text-glow">Diagnostics XAI Avancés</span>
        </h3>
        <ChevronRight className={`w-6 h-6 text-white/50 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="mt-6 border-t border-white/10 pt-6 space-y-8"
          >
            {/* General Confidence */}
            <div>
              <h4 className="text-md font-bold text-white/70 mb-3 flex items-center gap-2"><Lightbulb className="w-4 h-4" /> Résumé de Confiance</h4>
              <div className="flex items-center gap-4">
                <Badge className={`${confidenceColor} text-white text-md py-2 px-4`}>
                  Confiance Finale: {(final_confidence * 100).toFixed(1)}%
                </Badge>
                {reliabilityBadge}
                {uncertainty?.perplexity != null && (
                    <Badge variant="neutral" className="bg-white/10 text-white/80">
                        Perplexité: {uncertainty.perplexity.toFixed(2)}
                    </Badge>
                )}
              </div>
              {uncertainty && (
                <p className="text-sm text-white/60 mt-2">
                  Action requise: <span className="font-semibold">{uncertainty.action_required.replace('_', ' ')}</span>. Méthode: {uncertainty.method.replace('_', ' ')}.
                </p>
              )}
            </div>

            {/* Query Intent */}
            {query_intent && (
                <div>
                    <h4 className="text-md font-bold text-white/70 mb-3 flex items-center gap-2"><Target className="w-4 h-4" /> Intention de la Requête</h4>
                    <p className="text-white/90">{query_intent}</p>
                </div>
            )}

            {/* Retrieval Attribution */}
            {retrieval_attribution && retrieval_attribution.length > 0 && (
              <div>
                <h4 className="text-md font-bold text-white/70 mb-3 flex items-center gap-2"><BookOpen className="w-4 h-4" /> Attribution des Documents</h4>
                <div className="space-y-3">
                  {retrieval_attribution.map((doc, index) => (
                    <div key={index} className="bg-white/5 p-4 rounded-xl border border-white/10 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-semibold text-white">{doc.title} <span className="opacity-50">({doc.document_id})</span></p>
                        <p className="text-xs text-white/70">Score de pertinence: {(doc.relevance_score ?? 0).toFixed(2)} | Contribution: {(doc.contribution_weight * 100).toFixed(1)}%</p>
                      </div>
                      <Badge variant="primary" className="text-blue-400 border-blue-400/30">Source</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Influential Tokens */}
            {internal_diagnostics?.top_influential_tokens && internal_diagnostics.top_influential_tokens.length > 0 && (
              <div>
                <h4 className="text-md font-bold text-white/70 mb-3 flex items-center gap-2"><Atom className="w-4 h-4" /> Tokens Influents</h4>
                <div className="flex flex-wrap gap-2">
                  {internal_diagnostics.top_influential_tokens.map((token, index) => (
                    <Badge key={index} variant="neutral" className="bg-blue-600/20 text-blue-300 border-blue-600/30">
                      {token}
                    </Badge>
                  ))}
                </div>
                <p className="text-xs text-white/50 mt-2">Ces tokens ont eu la plus faible logprob (plus grande surprise) pour le modèle.</p>
              </div>
            )}

            {/* Logit Lens Trajectory (Simplified) */}
            {internal_diagnostics?.logit_lens_trajectory && internal_diagnostics.logit_lens_trajectory.length > 0 && (
              <div>
                <h4 className="text-md font-bold text-white/70 mb-3 flex items-center gap-2"><BarChart className="w-4 h-4" /> Trajectoire Logit Lens (Simplifié)</h4>
                <div className="space-y-4 max-h-60 overflow-y-auto pr-2">
                  {internal_diagnostics.logit_lens_trajectory.map((entry, index) => (
                    <div key={index} className="bg-white/5 p-3 rounded-lg border border-white/10">
                      <p className="text-sm font-semibold text-white">Couche {entry.layer}:</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {entry.top_tokens.map((token, tokenIndex) => (
                          <Badge key={tokenIndex} variant="neutral" className="text-purple-300 border-purple-300/30">
                            {token} ({((entry.internal_probabilities?.[tokenIndex] ?? 0) * 100).toFixed(1)}%)
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-white/50 mt-2">Visualisation simplifiée de l'évolution des prédictions de tokens à travers les couches du modèle.</p>
              </div>
            )}
            
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
};

export default XaiReportDisplay;