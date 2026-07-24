import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, X } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { ToTNode } from '../../../features/labs/types/totTypes';

interface ToTNodeInspectionModalProps {
  selectedNode: ToTNode | null;
  onClose: () => void;
}

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
          className="absolute top-8 right-8 w-96 max-h-[calc(100vh-128px)] overflow-y-auto z-30"
        >
          <Card
            padding="none"
            className="bg-black/80 backdrop-blur-2xl border-white/10 rounded-[2.5rem] shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden"
          >
            <div className="p-8 border-b border-white/5 flex justify-between items-start">
              <div>
                <Badge
                  variant="neutral"
                  className={`bg-white/5 border-none text-[8px] font-black italic uppercase tracking-widest mb-2 ${
                    selectedNode.type === 'selected'
                      ? 'text-emerald-500'
                      : selectedNode.type === 'pruned'
                        ? 'text-red-500'
                        : selectedNode.type === 'final'
                          ? 'text-yellow-500'
                          : ''
                  }`}
                >
                  {selectedNode.type} NODE
                </Badge>
                <h3 className="text-xl font-black italic manga-font uppercase tracking-tighter">
                  Inspection <span className="text-emerald-500">Nœud</span>
                </h3>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/5 rounded-full transition-colors"
                aria-label="Fermer l'inspection"
              >
                <X className="w-5 h-5 text-white/40" />
              </button>
            </div>

            <div className="p-8 space-y-8">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">
                    Score de Confiance
                  </span>
                  <span className="text-2xl font-black italic manga-font text-emerald-400">
                    {(selectedNode.score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${selectedNode.score * 100}%` }}
                    className={`h-full ${selectedNode.type === 'pruned' ? 'bg-red-800' : 'bg-emerald-500'}`}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <span className="text-[10px] font-black opacity-30 uppercase tracking-widest flex items-center gap-2">
                  <ChevronRight className="w-3 h-3 text-emerald-500" /> Trace de Pensée
                </span>
                <div className="p-6 bg-white/5 rounded-3xl border border-white/5 text-sm font-bold leading-relaxed text-gray-300 italic">
                  "{selectedNode.full_text}"
                </div>
              </div>

              <div className="pt-4 flex gap-4">
                <div className="flex-1 p-4 bg-white/5 rounded-2xl text-center">
                  <p className="text-[8px] font-black opacity-20 uppercase mb-1">ID</p>
                  <p className="text-[10px] font-mono opacity-40 truncate">{selectedNode.id}</p>
                </div>
                <div className="flex-1 p-4 bg-white/5 rounded-2xl text-center">
                  <p className="text-[8px] font-black opacity-20 uppercase mb-1">Status</p>
                  <p className="text-[10px] font-black italic uppercase text-emerald-500">
                    {selectedNode.type === 'pruned' ? 'TERMINATED' : 'ACTIVE'}
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
