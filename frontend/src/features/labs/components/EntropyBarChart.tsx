import React from 'react';
import { motion } from 'framer-motion';

interface TokenDiagnostic {
  token: string;
  entropy: number;
}

interface Props {
  data: TokenDiagnostic[];
}

const EntropyBarChart: React.FC<Props> = ({ data }) => {
  const getEntropyColor = (entropy: number) => {
    if (entropy < 1.0) return 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.3)]';
    if (entropy < 2.5) return 'bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.3)]';
    return 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]';
  };

  return (
    <div className="w-full h-full flex items-end gap-1 p-4 overflow-x-auto min-h-[240px] scrollbar-thin scrollbar-thumb-white/10">
      {data.map((item, index) => (
        <div key={index} className="flex flex-col items-center flex-1 min-w-[30px] group relative">
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: `${Math.min(item.entropy * 20, 100)}%` }}
            transition={{ delay: index * 0.05, duration: 0.5, ease: "easeOut" }}
            className={`w-full rounded-t-sm transition-all group-hover:brightness-125 ${getEntropyColor(item.entropy)}`}
          />
          <div className="absolute bottom-full mb-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/90 text-[10px] p-2 rounded border border-white/10 z-20 pointer-events-none shadow-xl">
            <div className="font-black italic text-blue-400 mb-1 uppercase tracking-tighter">Token: {item.token}</div>
            <div className="font-medium text-gray-300">Entropy: {item.entropy.toFixed(4)} bits</div>
          </div>
          <span className="text-[8px] font-bold text-gray-600 mt-2 rotate-45 origin-left whitespace-nowrap">
            {item.token}
          </span>
        </div>
      ))}
    </div>
  );
};

export default EntropyBarChart;
