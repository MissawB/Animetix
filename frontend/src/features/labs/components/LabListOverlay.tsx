import React from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowRight } from 'lucide-react';
import { Card } from '../../../components/ui/Card';

interface LabListOverlayProps {
  category: string | null;
  labs: { id: string, title: string, url: string, desc: string }[];
  onClose: () => void;
}

export const LabListOverlay: React.FC<LabListOverlayProps> = ({ category, labs, onClose }) => {
  return (
    <AnimatePresence>
      {category && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl"
        >
          <div className="max-w-4xl w-full">
            <header className="flex justify-between items-center mb-12">
              <h2 className="text-4xl font-black italic manga-font uppercase tracking-tighter text-white">
                Laboratoires <span className="text-red-600">{category}</span>
              </h2>
              <button onClick={onClose} aria-label="Fermer" className="p-2 hover:bg-white/10 rounded-full transition-colors text-white">
                <X className="w-8 h-8" />
              </button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {labs.map((lab) => (
                <Link key={lab.id} to={lab.url} className="no-underline group">
                  <Card padding="lg" className="bg-white/5 border-white/10 hover:border-red-600/50 transition-all">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="text-xl font-black italic uppercase manga-font mb-2 group-hover:text-red-500 transition-colors">
                          {lab.title}
                        </h3>
                        <p className="text-xs opacity-40 uppercase font-bold tracking-wider">
                          {lab.desc}
                        </p>
                      </div>
                      <ArrowRight className="w-6 h-6 opacity-0 group-hover:opacity-100 transform translate-x-[-10px] group-hover:translate-x-0 transition-all text-red-500" />
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
