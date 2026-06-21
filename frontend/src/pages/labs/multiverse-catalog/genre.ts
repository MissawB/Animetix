import React from 'react';
import {
  Sparkles,
  Globe,
  Network,
  Orbit,
  Swords,
  Eye,
  Atom,
} from 'lucide-react';

// ─── Genre Icon Map ──────────────────────────────────────────────────
export const genreIcons: Record<string, React.ElementType> = {
  'sci-fi': Atom,
  'shonen': Swords,
  'seinen': Eye,
  'cyberpunk': Network,
  'fantasy': Sparkles,
  'mecha': Orbit,
  'default': Globe,
};

export const genreColors: Record<string, string> = {
  'sci-fi': 'from-cyan-500/20 to-blue-600/20 border-cyan-500/30',
  'shonen': 'from-orange-500/20 to-red-600/20 border-orange-500/30',
  'seinen': 'from-purple-500/20 to-indigo-600/20 border-purple-500/30',
  'cyberpunk': 'from-green-500/20 to-emerald-600/20 border-green-500/30',
  'fantasy': 'from-amber-500/20 to-yellow-600/20 border-amber-500/30',
  'mecha': 'from-red-500/20 to-pink-600/20 border-red-500/30',
  'default': 'from-gray-500/20 to-gray-600/20 border-gray-500/30',
};

export const genreAccentColors: Record<string, string> = {
  'sci-fi': 'text-cyan-400',
  'shonen': 'text-orange-400',
  'seinen': 'text-purple-400',
  'cyberpunk': 'text-green-400',
  'fantasy': 'text-amber-400',
  'mecha': 'text-red-400',
  'default': 'text-gray-400',
};

export const getGenreIcon = (genre: string) => genreIcons[genre.toLowerCase()] || genreIcons.default;
export const getGenreColor = (genre: string) => genreColors[genre.toLowerCase()] || genreColors.default;
export const getGenreAccent = (genre: string) => genreAccentColors[genre.toLowerCase()] || genreAccentColors.default;
