import React from 'react';
import {
  History,
  AlertCircle,
  ArrowDownLeft,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { WalletTransaction } from '../../../features/billing/types/walletTypes';

// Libellés lisibles des types de transaction. IMPORTANT : ne JAMAIS afficher le
// type brut (ex. `ad_active`) — le vocabulaire « ad » sur un site AdSense évoque
// une récompense pour visionnage de pub (interdit). L'énergie/minage est un
// mécanisme d'engagement, pas une récompense publicitaire.
const TRANSACTION_TYPE_LABELS: Record<string, string> = {
  ad_passive: 'Passive Mining',
  ad_active: 'Active Recharge',
  purchase: 'Direct Purchase',
  ai_usage: 'AI Consumption',
  daily_grant: 'Daily Grant',
};

const transactionTypeLabel = (type: string): string =>
  TRANSACTION_TYPE_LABELS[type] ?? type.replace(/_/g, ' ');

interface TransactionLedgerTableProps {
  walletHistory: WalletTransaction[];
  isLoadingLedger: boolean;
  filterType: string;
  setFilterType: (val: string) => void;
  filterDirection: string;
  setFilterDirection: (val: string) => void;
  currentPage: number;
  totalPages: number;
  setCurrentPage: React.Dispatch<React.SetStateAction<number>>;
}

export const TransactionLedgerTable: React.FC<TransactionLedgerTableProps> = ({
  walletHistory,
  isLoadingLedger,
  filterType,
  setFilterType,
  filterDirection,
  setFilterDirection,
  currentPage,
  totalPages,
  setCurrentPage,
}) => {
  return (
    <div className="mt-20 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h3 className="text-2xl font-black italic uppercase manga-font flex items-center gap-3">
          <History className="w-6 h-6 text-cyan-400" /> Transaction Ledger
        </h3>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4">
          <select
            value={filterType}
            aria-label="Filtrer par catégorie"
            onChange={(e) => {
              setFilterType(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs font-black uppercase tracking-wider text-gray-400 focus:outline-none focus:border-cyan-400"
          >
            <option value="all">All Categories</option>
            <option value="ad_passive">Passive Mining</option>
            <option value="ad_active">Active Recharge</option>
            <option value="purchase">Direct Purchase</option>
            <option value="ai_usage">AI Consumption</option>
            <option value="daily_grant">Daily Grant</option>
          </select>

          <select
            value={filterDirection}
            aria-label="Filtrer par direction"
            onChange={(e) => {
              setFilterDirection(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs font-black uppercase tracking-wider text-gray-400 focus:outline-none focus:border-cyan-400"
          >
            <option value="all">All Directions</option>
            <option value="credit">Credits Only (+)</option>
            <option value="debit">Debits Only (-)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white/5 border border-white/10 rounded-[2rem] overflow-hidden">
        {isLoadingLedger ? (
          <div className="p-20 text-center text-gray-500 font-black animate-pulse uppercase tracking-[0.2em] text-xs">
            Querying database ledger...
          </div>
        ) : walletHistory.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[600px]">
              <thead>
                <tr className="border-b border-white/5 bg-white/5">
                  <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">
                    Transaction Description
                  </th>
                  <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">
                    Source type
                  </th>
                  <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">
                    Timestamp
                  </th>
                  <th className="p-6 text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 text-right">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody>
                {walletHistory.map((t, i) => (
                  <tr
                    key={i}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="p-6 font-bold text-sm text-white">{t.description}</td>
                    <td className="p-6">
                      <span
                        className={`text-[8px] font-black uppercase px-3 py-1 rounded-full border ${
                          t.amount > 0
                            ? 'border-cyan-500/30 text-cyan-400'
                            : 'border-purple-500/30 text-purple-400'
                        }`}
                      >
                        {transactionTypeLabel(t.type)}
                      </span>
                    </td>
                    <td className="p-6 text-xs text-gray-500 font-bold">
                      {new Date(t.date).toLocaleString()}
                    </td>
                    <td
                      className={`p-6 text-right font-black italic manga-font flex items-center justify-end gap-1.5 ${t.amount > 0 ? 'text-green-400' : 'text-purple-400'}`}
                    >
                      {t.amount > 0 ? (
                        <>
                          <ArrowDownLeft className="w-3.5 h-3.5" /> +{t.amount}
                        </>
                      ) : (
                        <>
                          <ArrowUpRight className="w-3.5 h-3.5" /> {t.amount}
                        </>
                      )}{' '}
                      Bx
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-20 text-center space-y-4">
            <AlertCircle className="w-12 h-12 text-gray-700 mx-auto" />
            <p className="text-gray-500 font-bold uppercase tracking-widest text-sm">
              No transaction ledger entries matched your query.
            </p>
          </div>
        )}

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-6 border-t border-white/5 bg-white/5 flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">
              Page {currentPage} of {totalPages}
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                className="flex items-center gap-1"
              >
                <ChevronLeft className="w-4 h-4" /> Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
                className="flex items-center gap-1"
              >
                Next <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
