import React from 'react';
import { BrainCircuit, CheckCircle2, ChevronRight, BookOpen, Fingerprint } from 'lucide-react';
import type { components } from '../../types/api';

type XaiReport = components['schemas']['XaiReport'];

export interface XaiReportViewerProps {
  report: XaiReport;
  className?: string;
}

interface AgentTraceStep {
  agent?: string;
  thought?: string;
  [key: string]: unknown;
}

export const XaiReportViewer: React.FC<XaiReportViewerProps> = ({ report, className = '' }) => {
  const formatConfidence = (conf: number) => `${Math.round(conf * 100)}%`;

  return (
    <div className={`font-sans bg-slate-900 text-slate-50 w-full max-w-2xl rounded-xl shadow-lg border border-slate-700 overflow-hidden ${className}`}>
      
      {/* Header */}
      <div className="bg-slate-800 p-4 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BrainCircuit className="text-blue-400" size={24} />
          <div>
            <h3 className="text-sm text-slate-400 font-medium uppercase tracking-wider">Query Intent</h3>
            <p className="text-lg font-semibold">{report.query_intent}</p>
          </div>
        </div>
        <div className="text-right">
          <h3 className="text-sm text-slate-400 font-medium uppercase tracking-wider">Confidence</h3>
          <div className="flex items-center gap-2 justify-end">
            <span className="text-xl font-bold text-emerald-400">{formatConfidence(report.final_confidence)}</span>
            <CheckCircle2 className="text-emerald-400" size={20} />
          </div>
        </div>
      </div>

      <div className="p-5 space-y-6">
        
        {/* Agent Trace Timeline */}
        {report.agent_trace && report.agent_trace.length > 0 && (
          <section>
            <h4 className="text-slate-300 font-medium mb-4 flex items-center gap-2">
              <ChevronRight size={18} className="text-slate-500" />
              Agent Trace
            </h4>
            <div className="pl-2 border-l-2 border-slate-700 ml-2 space-y-4">
              {report.agent_trace.map((trace: AgentTraceStep, idx) => (
                <div key={idx} className="relative pl-6">
                  <div className="absolute -left-[29px] top-1 w-3 h-3 rounded-full bg-blue-500 border-4 border-slate-900" />
                  <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
                    <span className="text-xs font-bold text-blue-400 uppercase tracking-wider block mb-1">
                      {trace.agent || `Step ${idx + 1}`}
                    </span>
                    <p className="text-sm text-slate-300">{trace.thought || JSON.stringify(trace)}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Data Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          {/* Attribution */}
          {report.retrieval_attribution && report.retrieval_attribution.length > 0 && (
            <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700/30">
              <h4 className="text-slate-300 font-medium mb-3 flex items-center gap-2 text-sm">
                <BookOpen size={16} className="text-amber-400" />
                Source Attribution
              </h4>
              <div className="space-y-3">
                {report.retrieval_attribution.map((attr, idx) => {
                  const val = attr.contribution_weight ?? attr.relevance_score;
                  return (
                  <div key={idx}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-300 truncate max-w-[70%]">{attr.title}</span>
                      <span className="text-amber-400">{formatConfidence(val)}</span>
                    </div>
                    <div className="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
                      <div 
                        className="bg-amber-400 h-full rounded-full" 
                        style={{ width: `${Math.max(0, Math.min(100, val * 100))}%` }} 
                      />
                    </div>
                  </div>
                )})}
              </div>
            </div>
          )}

          {/* Tokens */}
          {report.internal_diagnostics?.top_influential_tokens && (
            <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700/30">
              <h4 className="text-slate-300 font-medium mb-3 flex items-center gap-2 text-sm">
                <Fingerprint size={16} className="text-purple-400" />
                Influential Tokens
              </h4>
              <div className="flex flex-wrap gap-2">
                {report.internal_diagnostics.top_influential_tokens.map((token, idx) => (
                  <span 
                    key={idx} 
                    className="px-2.5 py-1 bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded text-xs font-mono"
                  >
                    {token}
                  </span>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
