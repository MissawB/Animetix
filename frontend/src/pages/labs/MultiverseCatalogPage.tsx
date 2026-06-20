import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  SlidersHorizontal,
  LayoutGrid,
  LayoutList,
  Sparkles,
  Globe,
  Users,
  ChevronLeft,
  ChevronRight,
  X,
  Loader2,
  Network,
  Orbit,
  Swords,
  BookOpen,
  ArrowUpDown,
  Filter,
  Eye,
  Star,
  Atom,
  Download,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

// ─── Types ───────────────────────────────────────────────────────────
interface UniverseCharacter {
  name: string;
  role: string;
  power_level: number;
}

interface Universe {
  id: string;
  name: string;
  description: string;
  cosmology: string;
  genre: string;
  is_synthetic: boolean;
  character_count: number;
  characters: UniverseCharacter[];
  created_at: string | null;
}

interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

interface GenreOption {
  name: string;
  count: number;
}

interface CatalogResponse {
  results: Universe[];
  pagination: Pagination;
  filters: {
    search: string;
    genre: string;
    sort: string;
  };
  available_genres: GenreOption[];
}

// ─── Genre Icon Map ──────────────────────────────────────────────────
const genreIcons: Record<string, React.ElementType> = {
  'sci-fi': Atom,
  'shonen': Swords,
  'seinen': Eye,
  'cyberpunk': Network,
  'fantasy': Sparkles,
  'mecha': Orbit,
  'default': Globe,
};

const genreColors: Record<string, string> = {
  'sci-fi': 'from-cyan-500/20 to-blue-600/20 border-cyan-500/30',
  'shonen': 'from-orange-500/20 to-red-600/20 border-orange-500/30',
  'seinen': 'from-purple-500/20 to-indigo-600/20 border-purple-500/30',
  'cyberpunk': 'from-green-500/20 to-emerald-600/20 border-green-500/30',
  'fantasy': 'from-amber-500/20 to-yellow-600/20 border-amber-500/30',
  'mecha': 'from-red-500/20 to-pink-600/20 border-red-500/30',
  'default': 'from-gray-500/20 to-gray-600/20 border-gray-500/30',
};

const genreAccentColors: Record<string, string> = {
  'sci-fi': 'text-cyan-400',
  'shonen': 'text-orange-400',
  'seinen': 'text-purple-400',
  'cyberpunk': 'text-green-400',
  'fantasy': 'text-amber-400',
  'mecha': 'text-red-400',
  'default': 'text-gray-400',
};

const getGenreIcon = (genre: string) => genreIcons[genre.toLowerCase()] || genreIcons.default;
const getGenreColor = (genre: string) => genreColors[genre.toLowerCase()] || genreColors.default;
const getGenreAccent = (genre: string) => genreAccentColors[genre.toLowerCase()] || genreAccentColors.default;

// ─── Universe Card (Grid) ────────────────────────────────────────────
const UniverseGridCard: React.FC<{ universe: Universe; index: number; onSelect: (u: Universe) => void }> = ({ universe, index, onSelect }) => {
  const Icon = getGenreIcon(universe.genre);
  const colorClasses = getGenreColor(universe.genre);
  const accent = getGenreAccent(universe.genre);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.4 }}
      layout
    >
      <Card
        padding="none"
        className={`group cursor-pointer bg-gradient-to-br ${colorClasses} border hover:scale-[1.02] hover:shadow-2xl hover:shadow-black/40 transition-all duration-500 overflow-hidden h-full flex flex-col`}
        onClick={() => onSelect(universe)}
      >
        {/* Visual header area */}
        <div className="relative h-44 bg-black/40 flex items-center justify-center overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.03),transparent_70%)]" />

          {/* Floating particles */}
          <div className="absolute top-4 right-6 w-2 h-2 rounded-full bg-white/10 animate-pulse" />
          <div className="absolute bottom-8 left-10 w-1.5 h-1.5 rounded-full bg-white/5 animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-12 left-8 w-1 h-1 rounded-full bg-white/10 animate-pulse" style={{ animationDelay: '0.5s' }} />

          <Icon className={`w-16 h-16 ${accent} opacity-20 group-hover:opacity-40 group-hover:scale-110 transition-all duration-700`} />

          {/* Genre badge */}
          <div className="absolute top-4 left-4">
            <Badge variant="neutral" className={`text-[8px] uppercase font-black tracking-widest ${accent} bg-black/50 backdrop-blur-sm border-white/10`}>
              {universe.genre}
            </Badge>
          </div>

          {/* Synthetic badge */}
          <div className="absolute top-4 right-4">
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <Sparkles className="w-2.5 h-2.5 text-emerald-400" />
              <span className="text-[8px] font-black text-emerald-400 uppercase">IA</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-5 flex-1 flex flex-col">
          <h3 className="text-base font-black italic manga-font uppercase mb-2 group-hover:text-white transition-colors leading-tight truncate">
            {universe.name}
          </h3>
          <p className="text-[10px] font-bold opacity-40 uppercase leading-relaxed tracking-wider line-clamp-3 mb-4 flex-1">
            {universe.description || universe.cosmology || 'Univers synthétique généré par IA'}
          </p>

          {/* Characters preview */}
          <div className="flex items-center justify-between pt-3 border-t border-white/5">
            <div className="flex items-center gap-2">
              <Users className="w-3.5 h-3.5 opacity-30" />
              <span className="text-[9px] font-black uppercase opacity-40">{universe.character_count} entités</span>
            </div>
            {universe.characters.length > 0 && (
              <div className="flex -space-x-1.5">
                {universe.characters.slice(0, 3).map((c, i) => (
                  <div
                    key={i}
                    className={`w-6 h-6 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-[8px] font-black ${accent}`}
                    title={c.name}
                  >
                    {c.name.charAt(0)}
                  </div>
                ))}
                {universe.character_count > 3 && (
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-[8px] font-bold opacity-30">
                    +{universe.character_count - 3}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

// ─── Universe Row (List) ─────────────────────────────────────────────
const UniverseListRow: React.FC<{ universe: Universe; index: number; onSelect: (u: Universe) => void }> = ({ universe, index, onSelect }) => {
  const Icon = getGenreIcon(universe.genre);
  const accent = getGenreAccent(universe.genre);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03, duration: 0.3 }}
      onClick={() => onSelect(universe)}
      className="flex items-center gap-6 p-5 bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 hover:border-white/10 rounded-2xl cursor-pointer transition-all duration-300 group"
    >
      {/* Icon */}
      <div className={`shrink-0 p-4 rounded-xl bg-white/5 group-hover:bg-white/10 transition-colors`}>
        <Icon className={`w-7 h-7 ${accent}`} />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <h3 className="text-sm font-black italic manga-font uppercase truncate group-hover:text-white transition-colors">
            {universe.name}
          </h3>
          <Badge variant="neutral" className={`text-[8px] uppercase font-black ${accent} shrink-0`}>
            {universe.genre}
          </Badge>
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 shrink-0">
            <Sparkles className="w-2 h-2 text-emerald-400" />
            <span className="text-[7px] font-black text-emerald-400 uppercase">Synthétique</span>
          </div>
        </div>
        <p className="text-[10px] font-bold opacity-30 uppercase tracking-wider truncate">
          {universe.description || universe.cosmology || 'Univers généré par intelligence artificielle'}
        </p>
      </div>

      {/* Stats */}
      <div className="shrink-0 flex items-center gap-6">
        <div className="text-right">
          <p className="text-[8px] font-black uppercase opacity-20 mb-0.5">Entités</p>
          <p className={`text-lg font-black italic manga-font ${accent}`}>{universe.character_count}</p>
        </div>
        <div className="shrink-0 flex -space-x-1.5">
          {universe.characters.slice(0, 4).map((c, i) => (
            <div
              key={i}
              className="w-7 h-7 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-[9px] font-black opacity-60"
              title={c.name}
            >
              {c.name.charAt(0)}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

// ─── Detail Panel ────────────────────────────────────────────────────
const UniverseDetailPanel: React.FC<{ universe: Universe; onClose: () => void }> = ({ universe, onClose }) => {
  const Icon = getGenreIcon(universe.genre);
  const accent = getGenreAccent(universe.genre);
  const colorClasses = getGenreColor(universe.genre);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 10 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className={`relative w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-[#0a0a14] border ${colorClasses.split(' ').pop()} rounded-3xl shadow-2xl custom-scrollbar`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`p-10 bg-gradient-to-br ${colorClasses} relative overflow-hidden`}>
          <div className="absolute -top-10 -right-10 opacity-10">
            <Icon className="w-40 h-40" />
          </div>
          <button onClick={onClose} className="absolute top-6 right-6 p-2 rounded-full bg-black/30 hover:bg-black/50 transition-colors">
            <X className="w-5 h-5 text-white/60" />
          </button>

          <div className="flex items-center gap-2 mb-4">
            <Badge variant="primary" className={`${accent} bg-black/30 border-white/10 text-[9px]`}>
              {universe.genre}
            </Badge>
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <Sparkles className="w-2.5 h-2.5 text-emerald-400" />
              <span className="text-[8px] font-black text-emerald-400 uppercase">Généré par IA</span>
            </div>
          </div>

          <h2 className="text-4xl font-black italic manga-font uppercase tracking-tight text-white leading-none relative z-10">
            {universe.name}
          </h2>
        </div>

        {/* Body */}
        <div className="p-10 space-y-8">
          {/* Description */}
          {universe.description && (
            <section>
              <h3 className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 mb-3 flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5" /> Synopsis
              </h3>
              <p className="text-sm font-bold leading-relaxed text-gray-300 italic">
                {universe.description}
              </p>
            </section>
          )}

          {/* Cosmology */}
          {universe.cosmology && (
            <section>
              <h3 className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 mb-3 flex items-center gap-2">
                <Orbit className="w-3.5 h-3.5" /> Cosmologie
              </h3>
              <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/5">
                <p className="text-sm font-bold leading-relaxed text-gray-400">
                  {universe.cosmology}
                </p>
              </div>
            </section>
          )}

          {/* Characters */}
          {universe.characters.length > 0 && (
            <section>
              <h3 className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 mb-4 flex items-center gap-2">
                <Users className="w-3.5 h-3.5" /> Entités du Nexus ({universe.character_count})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {universe.characters.map((c, i) => (
                  <div key={i} className="flex items-center gap-4 p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] transition-colors">
                    <div className={`w-10 h-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-sm font-black ${accent}`}>
                      {c.name.charAt(0)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-black uppercase text-white/80 truncate">{c.name}</p>
                      <p className="text-[9px] font-bold opacity-30 truncate">{c.role}</p>
                    </div>
                    {c.power_level > 0 && (
                      <div className="shrink-0 text-right">
                        <p className="text-[8px] font-black uppercase opacity-20">PWR</p>
                        <p className={`text-sm font-black italic ${accent}`}>{c.power_level.toLocaleString()}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* CTA */}
          <div className="pt-6 border-t border-white/5 flex gap-4">
            <Link to="/lab/multiverse/" className="flex-1">
              <Button className="w-full bg-cyan-600 hover:bg-cyan-500 text-white py-4 rounded-xl font-black italic uppercase shadow-lg shadow-cyan-900/20">
                <Network className="w-4 h-4 mr-2" /> Explorer dans le Nexus
              </Button>
            </Link>
            <Button
              onClick={() => {
                window.open(`/api/v1/multiverse/${encodeURIComponent(universe.name)}/export-pdf/`, '_blank');
              }}
              className="bg-white/5 hover:bg-white/10 text-white border border-white/10 py-4 px-6 rounded-xl font-black italic uppercase shrink-0 flex items-center justify-center"
            >
              <Download className="w-4 h-4 mr-2" /> Exporter PDF
            </Button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

// ─── Main Catalog Page ───────────────────────────────────────────────
const MultiverseCatalogPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [genre, setGenre] = useState('');
  const [sort, setSort] = useState('newest');
  const [page, setPage] = useState(1);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedUniverse, setSelectedUniverse] = useState<Universe | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset to first page on search
    }, 350);
    return () => clearTimeout(timer);
  }, [search]);

  // Reset page on filter change
  useEffect(() => {
    setPage(1);
  }, [genre, sort]);

  const queryParams = useMemo(() => {
    const params = new URLSearchParams();
    if (debouncedSearch) params.set('search', debouncedSearch);
    if (genre) params.set('genre', genre);
    params.set('sort', sort);
    params.set('page', String(page));
    params.set('page_size', '12');
    return params.toString();
  }, [debouncedSearch, genre, sort, page]);

  const { data, isLoading, isFetching } = useQuery<CatalogResponse>({
    queryKey: ['multiverse-catalog', queryParams],
    queryFn: () => apiClient(`/api/v1/multiverse/catalog/?${queryParams}`),
    placeholderData: (prev) => prev,
  });

  const sortOptions = [
    { value: 'newest', label: 'Plus récents' },
    { value: 'name', label: 'Alphabétique' },
    { value: 'characters', label: 'Plus peuplés' },
  ];

  const handleClearFilters = useCallback(() => {
    setSearch('');
    setDebouncedSearch('');
    setGenre('');
    setSort('newest');
    setPage(1);
  }, []);

  const hasActiveFilters = debouncedSearch || genre || sort !== 'newest';

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white">
        {/* ── Hero Header ─────────────────────────────────────── */}
        <header className="relative overflow-hidden border-b border-white/5">
          {/* Background decor */}
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-950/20 via-transparent to-purple-950/10" />
          <div className="absolute top-10 right-20 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-20 w-48 h-48 bg-purple-500/5 rounded-full blur-3xl" />

          <div className="max-w-7xl mx-auto px-6 py-16 relative z-10">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-black uppercase tracking-widest text-cyan-500 mb-4">
                  <Sparkles className="w-3 h-3" /> Catalogue Communautaire
                </div>
                <h1 className="text-6xl md:text-7xl font-black italic manga-font tracking-tighter uppercase mb-2">
                  MULTIVERSE <span className="text-cyan-500 text-glow">GALLERY</span>
                </h1>
                <p className="text-lg font-bold opacity-30 uppercase tracking-[0.2em] leading-relaxed">
                  Explorez les univers synthétiques générés par l'intelligence artificielle
                </p>
              </div>

              <div className="flex flex-col items-end gap-2">
                <div className="text-right">
                  <p className="text-[10px] font-black uppercase opacity-25 mb-1">Univers Total</p>
                  <p className="text-4xl font-black italic manga-font text-cyan-400">
                    {data?.pagination.total ?? '—'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* ── Controls Bar ────────────────────────────────────── */}
        <div className="sticky top-0 z-30 bg-[#05050a]/90 backdrop-blur-xl border-b border-white/5">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center">
              {/* Search */}
              <div className="relative flex-1 max-w-lg">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 opacity-30" />
                <input
                  id="catalog-search"
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Rechercher un univers, une cosmologie..."
                  className="w-full pl-11 pr-10 py-3 bg-white/5 border border-white/10 rounded-xl text-sm font-bold placeholder:opacity-30 focus:outline-none focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/10 transition-all"
                />
                {search && (
                  <button
                    onClick={() => { setSearch(''); setDebouncedSearch(''); }}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-white/10 transition-colors"
                  >
                    <X className="w-3.5 h-3.5 opacity-40" />
                  </button>
                )}
              </div>

              {/* Sort */}
              <div className="flex items-center gap-2">
                <ArrowUpDown className="w-3.5 h-3.5 opacity-30 shrink-0" />
                <select
                  id="catalog-sort"
                  value={sort}
                  onChange={(e) => setSort(e.target.value)}
                  className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-[10px] font-black uppercase tracking-widest focus:outline-none focus:border-cyan-500/40 transition-all appearance-none cursor-pointer"
                >
                  {sortOptions.map(opt => (
                    <option key={opt.value} value={opt.value} className="bg-[#0a0a14]">{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Filter toggle (mobile) */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`md:hidden flex items-center gap-2 px-4 py-3 rounded-xl border transition-all text-[10px] font-black uppercase tracking-widest ${
                  showFilters ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-white/5 border-white/10'
                }`}
              >
                <Filter className="w-3.5 h-3.5" /> Filtres
              </button>

              {/* View toggle */}
              <div className="flex bg-white/5 border border-white/10 rounded-xl overflow-hidden shrink-0">
                <button
                  id="view-grid"
                  onClick={() => setViewMode('grid')}
                  className={`p-3 transition-colors ${viewMode === 'grid' ? 'bg-cyan-500/20 text-cyan-400' : 'hover:bg-white/5 opacity-40'}`}
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button
                  id="view-list"
                  onClick={() => setViewMode('list')}
                  className={`p-3 transition-colors ${viewMode === 'list' ? 'bg-cyan-500/20 text-cyan-400' : 'hover:bg-white/5 opacity-40'}`}
                >
                  <LayoutList className="w-4 h-4" />
                </button>
              </div>

              {/* Clear filters */}
              {hasActiveFilters && (
                <button
                  onClick={handleClearFilters}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  <X className="w-3 h-3" /> Réinitialiser
                </button>
              )}
            </div>
          </div>
        </div>

        {/* ── Main Content ────────────────────────────────────── */}
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="flex gap-8">
            {/* Sidebar: Genre filters */}
            <aside className={`shrink-0 w-56 space-y-4 ${showFilters ? 'block' : 'hidden md:block'}`}>
              <h3 className="text-[10px] font-black uppercase tracking-widest opacity-30 flex items-center gap-2 mb-4">
                <SlidersHorizontal className="w-3.5 h-3.5" /> Genres
              </h3>

              <button
                onClick={() => setGenre('')}
                className={`w-full text-left px-4 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                  !genre ? 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-400' : 'bg-white/[0.02] border border-transparent hover:bg-white/5 opacity-60 hover:opacity-100'
                }`}
              >
                Tous les genres
                <span className="float-right opacity-40">{data?.pagination.total ?? 0}</span>
              </button>

              {data?.available_genres.map(g => {
                const accent = getGenreAccent(g.name);
                const isActive = genre.toLowerCase() === g.name.toLowerCase();
                return (
                  <button
                    key={g.name}
                    onClick={() => setGenre(g.name)}
                    className={`w-full text-left px-4 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                      isActive
                        ? `bg-white/5 border border-white/10 ${accent}`
                        : 'bg-white/[0.02] border border-transparent hover:bg-white/5 opacity-60 hover:opacity-100'
                    }`}
                  >
                    {g.name}
                    <span className="float-right opacity-40">{g.count}</span>
                  </button>
                );
              })}

              {/* Nexus link */}
              <div className="pt-6 border-t border-white/5">
                <Link to="/lab/multiverse/" className="block">
                  <Card padding="sm" className="bg-cyan-500/5 border-cyan-500/20 hover:bg-cyan-500/10 transition-colors group">
                    <div className="flex items-center gap-3">
                      <Network className="w-5 h-5 text-cyan-500 group-hover:scale-110 transition-transform" />
                      <div>
                        <p className="text-[10px] font-black uppercase text-cyan-400">Nexus Map</p>
                        <p className="text-[8px] font-bold opacity-30 uppercase">Vue graphe 3D</p>
                      </div>
                    </div>
                  </Card>
                </Link>
              </div>
            </aside>

            {/* Results */}
            <main className="flex-1 min-w-0">
              {/* Results header */}
              <div className="flex items-center justify-between mb-6">
                <p className="text-[10px] font-black uppercase opacity-30 tracking-widest">
                  {data ? `${data.pagination.total} univers trouvé${data.pagination.total > 1 ? 's' : ''}` : ''}
                  {debouncedSearch && ` pour "${debouncedSearch}"`}
                  {genre && ` • ${genre}`}
                </p>
                {isFetching && !isLoading && (
                  <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                )}
              </div>

              {/* Loading state */}
              {isLoading && (
                <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-3'}>
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className={`bg-white/[0.02] rounded-2xl animate-pulse ${viewMode === 'grid' ? 'h-72' : 'h-20'}`} />
                  ))}
                </div>
              )}

              {/* Empty state */}
              {!isLoading && data && data.results.length === 0 && (
                <div className="flex flex-col items-center justify-center py-24 text-center">
                  <Globe className="w-16 h-16 text-white/10 mb-6" />
                  <h3 className="text-xl font-black italic manga-font uppercase text-white/40 mb-2">Aucun univers trouvé</h3>
                  <p className="text-[10px] font-bold uppercase opacity-20 tracking-wider mb-6">
                    {debouncedSearch ? 'Essayez un autre terme de recherche' : 'Aucun univers synthétique ne correspond aux filtres sélectionnés'}
                  </p>
                  {hasActiveFilters && (
                    <button onClick={handleClearFilters} className="px-6 py-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-black uppercase tracking-widest text-cyan-400 hover:bg-cyan-500/20 transition-colors">
                      Réinitialiser les filtres
                    </button>
                  )}
                </div>
              )}

              {/* Grid view */}
              {!isLoading && data && data.results.length > 0 && viewMode === 'grid' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {data.results.map((u, i) => (
                    <UniverseGridCard key={u.id} universe={u} index={i} onSelect={setSelectedUniverse} />
                  ))}
                </div>
              )}

              {/* List view */}
              {!isLoading && data && data.results.length > 0 && viewMode === 'list' && (
                <div className="space-y-3">
                  {data.results.map((u, i) => (
                    <UniverseListRow key={u.id} universe={u} index={i} onSelect={setSelectedUniverse} />
                  ))}
                </div>
              )}

              {/* Pagination */}
              {data && data.pagination.total_pages > 1 && (
                <div className="flex items-center justify-center gap-4 mt-12">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={!data.pagination.has_previous}
                    className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest disabled:opacity-20 hover:bg-white/10 transition-all"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" /> Précédent
                  </button>

                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.min(data.pagination.total_pages, 7) }, (_, i) => {
                      let pageNum: number;
                      const totalPages = data.pagination.total_pages;
                      const currentPage = data.pagination.page;

                      if (totalPages <= 7) {
                        pageNum = i + 1;
                      } else if (currentPage <= 4) {
                        pageNum = i + 1;
                      } else if (currentPage >= totalPages - 3) {
                        pageNum = totalPages - 6 + i;
                      } else {
                        pageNum = currentPage - 3 + i;
                      }

                      return (
                        <button
                          key={pageNum}
                          onClick={() => setPage(pageNum)}
                          className={`w-10 h-10 rounded-xl text-[10px] font-black transition-all ${
                            pageNum === currentPage
                              ? 'bg-cyan-500/20 border border-cyan-500/30 text-cyan-400'
                              : 'bg-white/[0.02] hover:bg-white/5 opacity-40 hover:opacity-100'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                  </div>

                  <button
                    onClick={() => setPage(p => Math.min(data.pagination.total_pages, p + 1))}
                    disabled={!data.pagination.has_next}
                    className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest disabled:opacity-20 hover:bg-white/10 transition-all"
                  >
                    Suivant <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </main>
          </div>
        </div>

        {/* ── Detail Modal ────────────────────────────────────── */}
        <AnimatePresence>
          {selectedUniverse && (
            <UniverseDetailPanel
              universe={selectedUniverse}
              onClose={() => setSelectedUniverse(null)}
            />
          )}
        </AnimatePresence>
      </div>
    </AnimatedPage>
  );
};

export default MultiverseCatalogPage;
