import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { ToTNode } from '../../../features/labs/types/totTypes';

interface ToTNodeInspectionModalProps {
  selectedNode: ToTNode | null;
  onClose: () => void;
}

const TYPE_TONES: Record<string, string> = {
  root: 'text-[#F4F1E8]',
  selected: 'text-[#FDB913]',
  pruned: 'text-[#8F94A5]',
  final: 'text-[#E8442B]',
};

export const ToTNodeInspectionModal: React.FC<ToTNodeInspectionModalProps> = ({
  selectedNode,
  onClose,
}) => {
  useEffect(() => {
    if (!selectedNode) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNode, onClose]);

  return (
    <AnimatePresence>
      {selectedNode && (
        <motion.div
          role="dialog"
          aria-modal="true"
          aria-label="Inspection de nœud"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          className="absolute right-8 top-8 z-30 max-h-[calc(100vh-128px)] w-96 overflow-y-auto"
        >
          <section className="overflow-hidden rounded-2xl border border-[#F4F1E8]/15 bg-[#0F1016]">
            <div className="flex items-start justify-between border-b border-[#F4F1E8]/10 p-6">
              <div>
                <p
                  className={`mb-2 text-[10px] font-black uppercase tracking-widest ${
                    TYPE_TONES[selectedNode.type] ?? 'text-[#8F94A5]'
                  }`}
                >
                  Nœud {selectedNode.type}
                </p>
                <h3 className="font-manga text-xl font-black uppercase italic tracking-tighter text-[#F4F1E8]">
                  Inspection <span className="text-[#E8442B]">du nœud</span>
                </h3>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full border-none bg-transparent p-2 text-[#8F94A5] transition-colors hover:text-[#F4F1E8] cursor-pointer"
                aria-label="Fermer l'inspection"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-6 p-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                    Score de confiance
                  </span>
                  <span className="font-manga text-2xl font-black italic text-[#FDB913]">
                    {(selectedNode.score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#F4F1E8]/10">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${selectedNode.score * 100}%` }}
                    className={`h-full ${
                      selectedNode.type === 'pruned' ? 'bg-[#8F94A5]' : 'bg-[#FDB913]'
                    }`}
                  />
                </div>
              </div>

              <div className="space-y-3">
                <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  Trace de pensée
                </span>
                <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-5 text-sm italic leading-relaxed text-[#F4F1E8]/80">
                  "{selectedNode.full_text}"
                </div>
              </div>

              <div className="flex gap-4 pt-2">
                <div className="flex-1 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 text-center">
                  <p className="mb-1 text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                    ID
                  </p>
                  <p className="truncate font-mono text-[10px] text-[#F4F1E8]/70">
                    {selectedNode.id}
                  </p>
                </div>
                <div className="flex-1 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 text-center">
                  <p className="mb-1 text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                    Statut
                  </p>
                  <p
                    className={`text-[10px] font-black uppercase tracking-widest ${
                      selectedNode.type === 'pruned' ? 'text-[#8F94A5]' : 'text-[#FDB913]'
                    }`}
                  >
                    {selectedNode.type === 'pruned' ? 'Élagué' : 'Actif'}
                  </p>
                </div>
              </div>
            </div>
          </section>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
