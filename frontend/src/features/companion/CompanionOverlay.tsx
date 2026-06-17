import React from 'react';
import { useCompanionStore } from './companionStore';
import CompanionDialogue from './CompanionDialogue';
import { MessageCircle, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const CompanionOverlay: React.FC = () => {
  const { isOpen, toggleOpen } = useCompanionStore();

  return (
    <div className="fixed bottom-6 right-6 z-[9999] flex flex-col items-end pointer-events-none">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20, transformOrigin: 'bottom right' }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            className="mb-4 w-[350px] h-[500px] pointer-events-auto"
          >
            <CompanionDialogue />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={toggleOpen}
        className={`pointer-events-auto w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-colors duration-300 ${
          isOpen ? 'bg-red-500 hover:bg-red-600' : 'bg-indigo-600 hover:bg-indigo-500'
        } text-white`}
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
        
        {!isOpen && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="absolute right-16 bg-slate-800 text-white px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap shadow-xl border border-slate-700 hidden sm:block"
          >
            Ask Sensei!
          </motion.div>
        )}
      </motion.button>
    </div>
  );
};

export default CompanionOverlay;
