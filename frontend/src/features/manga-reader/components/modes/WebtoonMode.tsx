import React from 'react';
import { useReaderStore } from '../../stores/useReaderStore';

export const WebtoonMode = () => {
  const { pages } = useReaderStore();

  if (pages.length === 0) return <div className="flex items-center justify-center h-64 text-gray-500 italic">Aucune page chargée</div>;

  return (
    <div className="flex flex-col items-center gap-0 w-full max-w-2xl mx-auto pb-20">
      {pages.map((page) => (
        <img 
          key={page.index}
          src={page.url} 
          alt={`Page ${page.index + 1}`} 
          className="w-full h-auto block"
          loading="lazy"
        />
      ))}
    </div>
  );
};
