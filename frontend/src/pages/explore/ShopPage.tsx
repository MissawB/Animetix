import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ShoppingBag, 
  Coins, 
  Search, 
  ArrowUpDown, 
  Plus, 
  X, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  FolderOpen,
  ArrowRightLeft,
  XCircle,
  Sparkles
} from 'lucide-react';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useToastStore } from '../../store/toastStore';
import { motion, AnimatePresence } from 'framer-motion';

// --- Types ---
interface CreativeFusion {
  id: number;
  title_a: string;
  title_b: string;
  media_type_a: string;
  media_type_b: string;
  scenario_text: string;
  image_url: string | null;
  chaos_level: number;
  universe_balance: number;
  art_style: string;
}

interface MarketListing {
  id: number;
  fusion: number;
  fusion_detail: CreativeFusion;
  seller: number;
  seller_name: string;
  price: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface WalletBalanceResponse {
  balance: number;
  history: {
    amount: number;
    type: string;
    description: string;
    date: string;
  }[];
}

const ShopPage: React.FC = () => {
  const queryClient = useQueryClient();
  const addToast = useToastStore((state) => state.addToast);
  
  const [activeTab, setActiveTab] = useState<'market' | 'inventory' | 'listings' | 'history'>('market');
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('newest');
  
  // Modals state
  const [sellModalItem, setSellModalItem] = useState<CreativeFusion | null>(null);
  const [sellPrice, setSellPrice] = useState<number>(100);
  const [buyModalItem, setBuyModalItem] = useState<MarketListing | null>(null);

  // --- Queries ---
  
  // 1. Wallet balance and history
  const { data: walletData } = useQuery<WalletBalanceResponse>({
    queryKey: ['wallet-balance'],
    queryFn: () => apiClient('/api/v1/billing/wallet/balance/'),
  });

  // 2. Marketplace listings
  const { data: listings, isLoading: isListingsLoading } = useQuery<MarketListing[]>({
    queryKey: ['market-listings', search, sort, activeTab],
    queryFn: () => {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      params.append('sort', sort);
      if (activeTab === 'listings') {
        params.append('user_filter', 'mine');
      } else {
        params.append('user_filter', 'active');
      }
      return apiClient(`/api/v1/market/listings/?${params.toString()}`);
    },
  });

  // 3. User fusions (inventory)
  const { data: inventory, isLoading: isInventoryLoading } = useQuery<CreativeFusion[]>({
    queryKey: ['user-inventory'],
    queryFn: () => apiClient('/api/v1/social/collection/'),
    enabled: activeTab === 'inventory',
  });

  // --- Mutations ---

  // 1. Create listing
  const createListingMutation = useMutation<void, Error, { fusion: number; price: number }>({
    mutationFn: (body) => apiClient('/api/v1/market/listings/', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
    onSuccess: () => {
      addToast('Actif mis en vente avec succès !', 'success');
      setSellModalItem(null);
      setSellPrice(100);
      queryClient.invalidateQueries({ queryKey: ['market-listings'] });
      queryClient.invalidateQueries({ queryKey: ['user-inventory'] });
    },
    onError: (error: any) => {
      addToast(error?.error || error?.message || 'Erreur lors de la mise en vente.', 'error');
    }
  });

  // 2. Buy listing
  const buyListingMutation = useMutation<void, Error, number>({
    mutationFn: (listingId) => apiClient(`/api/v1/market/listings/${listingId}/buy/`, {
      method: 'POST',
    }),
    onSuccess: () => {
      addToast('Achat effectué avec succès !', 'success');
      setBuyModalItem(null);
      queryClient.invalidateQueries({ queryKey: ['market-listings'] });
      queryClient.invalidateQueries({ queryKey: ['wallet-balance'] });
      queryClient.invalidateQueries({ queryKey: ['user-inventory'] });
    },
    onError: (error: any) => {
      addToast(error?.error || error?.message || "Erreur lors de l'achat.", 'error');
    }
  });

  // 3. Cancel listing
  const cancelListingMutation = useMutation<void, Error, number>({
    mutationFn: (listingId) => apiClient(`/api/v1/market/listings/${listingId}/cancel/`, {
      method: 'POST',
    }),
    onSuccess: () => {
      addToast('Vente annulée avec succès.', 'info');
      queryClient.invalidateQueries({ queryKey: ['market-listings'] });
      queryClient.invalidateQueries({ queryKey: ['user-inventory'] });
    },
    onError: (error: any) => {
      addToast(error?.error || error?.message || "Erreur lors de l'annulation.", 'error');
    }
  });

  const handleCreateListing = () => {
    if (!sellModalItem) return;
    if (sellPrice <= 0) {
      addToast('Le prix doit être strictement supérieur à 0.', 'error');
      return;
    }
    createListingMutation.mutate({ fusion: sellModalItem.id, price: sellPrice });
  };

  const handleBuyListing = () => {
    if (!buyModalItem) return;
    buyListingMutation.mutate(buyModalItem.id);
  };

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white p-6 max-w-7xl mx-auto py-16">
        
        {/* --- Header & Balance Stats --- */}
        <header className="flex flex-col md:flex-row justify-between items-center gap-8 mb-12 border-b border-white/5 pb-10">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-3xl shadow-[0_0_20px_rgba(16,185,129,0.15)] text-emerald-400">
              <ShoppingBag className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-5xl font-black italic tracking-tighter uppercase manga-font leading-none mb-2">
                BOUTIQUE <span className="text-emerald-400 text-glow-emerald">D'ACTIFS</span>
              </h1>
              <p className="text-xs font-black uppercase tracking-[0.2em] opacity-40">
                Achetez, vendez et échangez des fusions créatives communautaires
              </p>
            </div>
          </div>
          
          <Card padding="md" className="bg-gradient-to-br from-emerald-950/20 via-black/40 to-transparent border-emerald-500/30 flex items-center gap-6 min-w-[260px] shadow-2xl">
            <Coins className="w-10 h-10 text-emerald-400 animate-pulse" />
            <div>
              <p className="text-[10px] font-black uppercase opacity-40 tracking-widest mb-1">Votre Solde Berrix</p>
              <p className="text-3xl font-black italic manga-font text-emerald-400">
                {walletData?.balance !== undefined ? walletData.balance.toLocaleString() : '—'} <span className="text-xs not-italic font-bold">Bx</span>
              </p>
            </div>
          </Card>
        </header>

        {/* --- Tabs --- */}
        <div className="flex flex-col md:flex-row gap-6 justify-between items-center mb-8">
          <div className="flex bg-white/5 p-1.5 rounded-2xl border border-white/10 backdrop-blur-xl shrink-0">
            <button 
              onClick={() => setActiveTab('market')}
              className={`px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2 ${activeTab === 'market' ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20' : 'hover:bg-white/5 opacity-40 hover:opacity-100'}`}
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              Marché
            </button>
            <button 
              onClick={() => setActiveTab('inventory')}
              className={`px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2 ${activeTab === 'inventory' ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20' : 'hover:bg-white/5 opacity-40 hover:opacity-100'}`}
            >
              <FolderOpen className="w-3.5 h-3.5" />
              Mon Inventaire
            </button>
            <button 
              onClick={() => setActiveTab('listings')}
              className={`px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2 ${activeTab === 'listings' ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20' : 'hover:bg-white/5 opacity-40 hover:opacity-100'}`}
            >
              <Clock className="w-3.5 h-3.5" />
              Mes Ventes
            </button>
            <button 
              onClick={() => setActiveTab('history')}
              className={`px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2 ${activeTab === 'history' ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20' : 'hover:bg-white/5 opacity-40 hover:opacity-100'}`}
            >
              <ArrowRightLeft className="w-3.5 h-3.5" />
              Transactions
            </button>
          </div>

          {/* Search and Sort (Hide for history) */}
          {activeTab !== 'history' && (
            <div className="flex gap-4 w-full md:w-auto">
              {activeTab === 'market' && (
                <>
                  <div className="relative flex-1 md:w-64">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 opacity-30" />
                    <input 
                      type="text"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      placeholder="Rechercher une fusion..."
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs outline-none focus:border-emerald-500/40 transition-all font-bold"
                    />
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <ArrowUpDown className="w-3.5 h-3.5 opacity-30" />
                    <select
                      value={sort}
                      onChange={(e) => setSort(e.target.value)}
                      className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-[10px] font-black uppercase tracking-widest focus:outline-none focus:border-emerald-500/40 cursor-pointer"
                    >
                      <option value="newest" className="bg-[#0a0a14]">Plus récents</option>
                      <option value="price_asc" className="bg-[#0a0a14]">Prix croissant</option>
                      <option value="price_desc" className="bg-[#0a0a14]">Prix décroissant</option>
                    </select>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* --- Main Content Grid --- */}
        <AnimatePresence mode="wait">
          
          {/* Tab 1: Marketplace (Browse active listings) */}
          {activeTab === 'market' && (
            <motion.div key="market" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
              {isListingsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {Array(6).fill(0).map((_, i) => (
                    <div key={i} className="h-80 bg-white/5 rounded-3xl animate-pulse border border-white/5" />
                  ))}
                </div>
              ) : !listings || listings.length === 0 ? (
                <div className="text-center py-24 border border-dashed border-white/5 rounded-3xl bg-white/[0.01]">
                  <ShoppingBag className="w-16 h-16 opacity-10 mx-auto mb-4" />
                  <p className="text-xs font-black uppercase tracking-widest opacity-30">Aucun actif listé pour le moment</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {listings.map((listing) => (
                    <Card key={listing.id} padding="none" className="group overflow-hidden bg-navy-900/40 border-white/5 hover:border-emerald-500/50 hover:shadow-[0_0_30px_rgba(16,185,129,0.05)] transition-all flex flex-col h-full">
                      {/* Image section */}
                      <div className="relative aspect-[16/10] bg-black overflow-hidden flex items-center justify-center">
                        {listing.fusion_detail.image_url ? (
                          <img 
                            src={listing.fusion_detail.image_url} 
                            alt={listing.fusion_detail.title_a}
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                          />
                        ) : (
                          <div className="opacity-10">
                            <Sparkles className="w-16 h-16" />
                          </div>
                        )}
                        <div className="absolute top-4 left-4">
                          <Badge variant="neutral" className="bg-black/60 backdrop-blur-sm border-white/10 text-[8px] uppercase tracking-widest">
                            Style: {listing.fusion_detail.art_style}
                          </Badge>
                        </div>
                        <div className="absolute bottom-4 right-4 bg-emerald-500/10 border border-emerald-500/20 backdrop-blur-md px-3 py-1.5 rounded-xl flex items-center gap-1.5 shadow-xl">
                          <Coins className="w-4 h-4 text-emerald-400" />
                          <span className="text-sm font-black italic manga-font text-emerald-400">
                            {listing.price.toLocaleString()} <span className="text-[10px] not-italic font-bold">Bx</span>
                          </span>
                        </div>
                      </div>
                      
                      {/* Body */}
                      <div className="p-6 flex-grow flex flex-col justify-between">
                        <div className="mb-6">
                          <h3 className="text-lg font-black italic uppercase tracking-tighter leading-tight manga-font mb-1 truncate">
                            {listing.fusion_detail.title_a} <span className="text-emerald-400">×</span> {listing.fusion_detail.title_b}
                          </h3>
                          <p className="text-[10px] font-black uppercase opacity-35 tracking-wider mb-3">
                            Vendeur: <span className="text-white/70">{listing.seller_name}</span>
                          </p>
                          <p className="text-xs text-white/50 leading-relaxed italic line-clamp-3">
                            "{listing.fusion_detail.scenario_text}"
                          </p>
                        </div>
                        
                        <Button 
                          onClick={() => setBuyModalItem(listing)}
                          className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-black italic uppercase text-xs tracking-wider rounded-xl py-3 shadow-lg shadow-emerald-950/20"
                        >
                          Acheter l'Actif
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Tab 2: Inventory (Browse fusions that can be listed) */}
          {activeTab === 'inventory' && (
            <motion.div key="inventory" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
              {isInventoryLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  {Array(8).fill(0).map((_, i) => (
                    <div key={i} className="h-64 bg-white/5 rounded-3xl animate-pulse" />
                  ))}
                </div>
              ) : !inventory || inventory.length === 0 ? (
                <div className="text-center py-24 border border-dashed border-white/5 rounded-3xl bg-white/[0.01]">
                  <FolderOpen className="w-16 h-16 opacity-10 mx-auto mb-4" />
                  <p className="text-xs font-black uppercase tracking-widest opacity-30">Votre inventaire est vide</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {inventory.map((item) => (
                    <Card key={item.id} padding="none" className="group overflow-hidden bg-navy-900/40 border-white/5 hover:border-emerald-500/30 transition-all flex flex-col h-full">
                      <div className="relative aspect-[3/4] bg-black overflow-hidden flex items-center justify-center">
                        {item.image_url ? (
                          <img 
                            src={item.image_url} 
                            alt={item.title_a}
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                          />
                        ) : (
                          <div className="opacity-10">
                            <Sparkles className="w-16 h-16" />
                          </div>
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-[#05050a] via-transparent to-transparent opacity-60" />
                        <div className="absolute bottom-4 left-4">
                          <Badge variant="neutral" className="bg-black/60 backdrop-blur-sm border-white/10 text-[8px] uppercase tracking-widest">
                            Style: {item.art_style}
                          </Badge>
                        </div>
                      </div>
                      <div className="p-4 flex-grow flex flex-col justify-between">
                        <h4 className="font-black italic uppercase leading-none mb-4 truncate text-sm manga-font">
                          {item.title_a} <span className="text-emerald-400">×</span> {item.title_b}
                        </h4>
                        <Button 
                          onClick={() => setSellModalItem(item)}
                          className="w-full bg-white/5 hover:bg-white/10 text-white font-black uppercase tracking-widest text-[9px] py-2 rounded-lg border border-white/10 hover:border-white/20 transition-all"
                        >
                          <Plus className="w-3 h-3 mr-1.5" /> Mettre en vente
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Tab 3: Active Listings (User's active listings) */}
          {activeTab === 'listings' && (
            <motion.div key="listings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
              {isListingsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {Array(3).fill(0).map((_, i) => (
                    <div key={i} className="h-80 bg-white/5 rounded-3xl animate-pulse" />
                  ))}
                </div>
              ) : !listings || listings.length === 0 ? (
                <div className="text-center py-24 border border-dashed border-white/5 rounded-3xl bg-white/[0.01]">
                  <Clock className="w-16 h-16 opacity-10 mx-auto mb-4" />
                  <p className="text-xs font-black uppercase tracking-widest opacity-30">Vous n'avez pas de vente active</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {listings.map((listing) => (
                    <Card key={listing.id} padding="none" className="overflow-hidden bg-navy-900/40 border-white/5 flex flex-col h-full">
                      <div className="relative aspect-[16/10] bg-black overflow-hidden flex items-center justify-center">
                        {listing.fusion_detail.image_url ? (
                          <img 
                            src={listing.fusion_detail.image_url} 
                            alt={listing.fusion_detail.title_a}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="opacity-10">
                            <Sparkles className="w-16 h-16" />
                          </div>
                        )}
                        <div className="absolute bottom-4 right-4 bg-emerald-500/10 border border-emerald-500/20 backdrop-blur-md px-3 py-1.5 rounded-xl flex items-center gap-1.5">
                          <Coins className="w-4 h-4 text-emerald-400" />
                          <span className="text-sm font-black italic manga-font text-emerald-400">
                            {listing.price.toLocaleString()} <span className="text-[10px] not-italic font-bold">Bx</span>
                          </span>
                        </div>
                      </div>
                      
                      <div className="p-6 flex-grow flex flex-col justify-between">
                        <div className="mb-6">
                          <h3 className="text-lg font-black italic uppercase tracking-tighter leading-tight manga-font mb-3 truncate">
                            {listing.fusion_detail.title_a} <span className="text-emerald-400">×</span> {listing.fusion_detail.title_b}
                          </h3>
                          <div className="flex justify-between text-[9px] font-black uppercase opacity-45">
                            <span>Mis en vente le</span>
                            <span>{new Date(listing.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        
                        <Button 
                          onClick={() => cancelListingMutation.mutate(listing.id)}
                          className="w-full bg-red-500/10 hover:bg-red-500 text-red-400 hover:text-white font-black uppercase tracking-widest text-[10px] rounded-xl py-3 border border-red-500/20 hover:border-red-500 transition-all shadow-lg"
                        >
                          Annuler la mise en vente
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Tab 4: History (Transactions log) */}
          {activeTab === 'history' && (
            <motion.div key="history" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              {!walletData?.history || walletData.history.length === 0 ? (
                <div className="text-center py-24 border border-dashed border-white/5 rounded-3xl bg-white/[0.01]">
                  <ArrowRightLeft className="w-16 h-16 opacity-10 mx-auto mb-4" />
                  <p className="text-xs font-black uppercase tracking-widest opacity-30">Aucun historique disponible</p>
                </div>
              ) : (
                <div className="space-y-3 max-w-4xl mx-auto">
                  {walletData.history.map((tx, idx) => {
                    const isCredit = tx.amount > 0;
                    return (
                      <div key={idx} className="flex items-center justify-between p-5 bg-white/[0.02] border border-white/5 rounded-2xl hover:bg-white/[0.04] transition-all">
                        <div className="flex items-center gap-4">
                          <div className={`p-3 rounded-xl border ${
                            isCredit 
                              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                              : 'bg-red-500/10 border-red-500/20 text-red-400'
                          }`}>
                            {isCredit ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                          </div>
                          <div>
                            <p className="text-xs font-black uppercase text-white/95">{tx.description}</p>
                            <p className="text-[9px] font-black uppercase opacity-30 mt-1">{new Date(tx.date).toLocaleString()}</p>
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <span className={`text-sm font-black italic manga-font ${isCredit ? 'text-emerald-400' : 'text-red-400'}`}>
                            {isCredit ? '+' : ''}{tx.amount.toLocaleString()} <span className="text-[10px] not-italic font-bold">Bx</span>
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}

        </AnimatePresence>

        {/* --- SELL MODAL --- */}
        <AnimatePresence>
          {sellModalItem && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={() => setSellModalItem(null)}>
              <motion.div 
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-[#0b0b14] border border-emerald-500/30 rounded-3xl w-full max-w-md p-8 relative shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                <button onClick={() => setSellModalItem(null)} className="absolute top-6 right-6 p-2 rounded-full bg-white/5 hover:bg-white/10 transition-colors">
                  <X className="w-4 h-4 text-white/60" />
                </button>
                
                <h3 className="text-2xl font-black italic uppercase tracking-tighter leading-none manga-font text-white mb-6">
                  Mettre en <span className="text-emerald-400">Vente</span>
                </h3>
                
                <div className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-xl bg-black overflow-hidden flex items-center justify-center shrink-0">
                    {sellModalItem.image_url ? (
                      <img src={sellModalItem.image_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <Sparkles className="w-6 h-6 opacity-20" />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-black uppercase text-white truncate leading-none mb-1.5">
                      {sellModalItem.title_a} × {sellModalItem.title_b}
                    </p>
                    <Badge variant="neutral" className="text-[8px]">{sellModalItem.art_style}</Badge>
                  </div>
                </div>

                <div className="space-y-2 mb-8">
                  <label htmlFor="price-input" className="text-[9px] font-black uppercase opacity-40 tracking-widest block">Prix de vente (en Berrix)</label>
                  <div className="relative">
                    <Coins className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-emerald-400" />
                    <input 
                      id="price-input"
                      type="number"
                      value={sellPrice}
                      onChange={(e) => setSellPrice(Math.max(1, parseInt(e.target.value) || 0))}
                      className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-16 text-lg font-black italic focus:outline-none focus:border-emerald-500/40 text-emerald-400"
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-black uppercase tracking-widest opacity-40">Berrix</span>
                  </div>
                </div>

                <div className="flex gap-4">
                  <Button 
                    onClick={() => setSellModalItem(null)}
                    className="flex-1 bg-white/5 hover:bg-white/10 text-white font-black uppercase tracking-widest text-[10px] rounded-xl py-4 border border-white/10"
                  >
                    Annuler
                  </Button>
                  <Button 
                    onClick={handleCreateListing}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-black italic uppercase text-xs rounded-xl py-4"
                  >
                    Confirmer
                  </Button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* --- BUY MODAL --- */}
        <AnimatePresence>
          {buyModalItem && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={() => setBuyModalItem(null)}>
              <motion.div 
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-[#0b0b14] border border-emerald-500/30 rounded-3xl w-full max-w-md p-8 relative shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              >
                <button onClick={() => setBuyModalItem(null)} className="absolute top-6 right-6 p-2 rounded-full bg-white/5 hover:bg-white/10 transition-colors">
                  <X className="w-4 h-4 text-white/60" />
                </button>
                
                <h3 className="text-2xl font-black italic uppercase tracking-tighter leading-none manga-font text-white mb-6">
                  Confirmer <span className="text-emerald-400">l'Achat</span>
                </h3>
                
                <div className="p-6 bg-white/5 rounded-2xl border border-white/5 mb-6 space-y-4">
                  <div className="flex items-center gap-4 border-b border-white/5 pb-4">
                    <div className="w-14 h-14 rounded-xl bg-black overflow-hidden flex items-center justify-center shrink-0">
                      {buyModalItem.fusion_detail.image_url ? (
                        <img src={buyModalItem.fusion_detail.image_url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <Sparkles className="w-6 h-6 opacity-20" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-black uppercase text-white truncate leading-none mb-1.5">
                        {buyModalItem.fusion_detail.title_a} × {buyModalItem.fusion_detail.title_b}
                      </p>
                      <Badge variant="neutral" className="text-[8px]">{buyModalItem.fusion_detail.art_style}</Badge>
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold opacity-40 uppercase tracking-wider">Vendeur</span>
                    <span className="font-black text-white/80">{buyModalItem.seller_name}</span>
                  </div>

                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold opacity-40 uppercase tracking-wider">Prix Actif</span>
                    <span className="font-black text-emerald-400 flex items-center gap-1">
                      <Coins className="w-3.5 h-3.5" />
                      {buyModalItem.price.toLocaleString()} Bx
                    </span>
                  </div>
                </div>

                {/* Solde check */}
                {walletData && walletData.balance < buyModalItem.price ? (
                  <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-red-400 mb-8">
                    <AlertCircle className="w-5 h-5 shrink-0" />
                    <div>
                      <p className="text-[10px] font-black uppercase">Solde Insuffisant</p>
                      <p className="text-[9px] font-medium opacity-80 mt-0.5">Il vous manque {(buyModalItem.price - walletData.balance).toLocaleString()} Bx pour finaliser l'achat.</p>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center gap-3 text-emerald-400 mb-8">
                    <CheckCircle2 className="w-5 h-5 shrink-0" />
                    <div>
                      <p className="text-[10px] font-black uppercase">Solde Suffisant</p>
                      <p className="text-[9px] font-medium opacity-80 mt-0.5">Solde restant après transaction : {(walletData ? walletData.balance - buyModalItem.price : 0).toLocaleString()} Bx.</p>
                    </div>
                  </div>
                )}

                <div className="flex gap-4">
                  <Button 
                    onClick={() => setBuyModalItem(null)}
                    className="flex-1 bg-white/5 hover:bg-white/10 text-white font-black uppercase tracking-widest text-[10px] rounded-xl py-4 border border-white/10"
                  >
                    Fermer
                  </Button>
                  <Button 
                    onClick={handleBuyListing}
                    disabled={!walletData || walletData.balance < buyModalItem.price}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-black italic uppercase text-xs rounded-xl py-4 disabled:opacity-20"
                  >
                    Confirmer l'Achat
                  </Button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

      </div>
    </AnimatedPage>
  );
};

export default ShopPage;
