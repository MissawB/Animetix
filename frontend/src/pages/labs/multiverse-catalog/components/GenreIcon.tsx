import React from 'react';
import { getGenreIcon } from '../genre';

// Stable component that resolves the genre icon at render time without
// creating a new component during render.
export const GenreIcon: React.FC<{ genre: string; className?: string }> = ({ genre, className }) =>
  React.createElement(getGenreIcon(genre), { className });
