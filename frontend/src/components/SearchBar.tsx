import React, { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchMedia } from '../api';
import { Search, X, Camera, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Input } from './ui/Input';
import { Card } from './ui/Card';

interface SearchItem {
  id?: number | string;
  title?: string;
  name?: string;
  image_url?: string;
  type?: string;
}

interface SearchBarProps {
  onSelect?: (item: SearchItem) => void;
  placeholder?: string;
  id?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSelect, placeholder, id }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<SearchItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [imagePreview, setPreviewUrl] = useState<string | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    
    if (debounceRef.current) clearTimeout(debounceRef.current);
    
    if (val.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }
    
    debounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await searchMedia(val);
        // data is already MediaItem[] which is compatible with SearchItem
        setResults(data);
        setIsOpen(true);
      } catch {
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && query.trim().length >= 2) {
        setIsOpen(false);
        navigate(`/search/?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const handleImageSearch = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setPreviewUrl(URL.createObjectURL(file));
    setIsLoading(true);
    setIsOpen(true);
    
    try {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('media_type', 'Anime');

        const res = await fetch('/api/v1/search/', {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) throw new Error('Image search failed');
        const data = await res.json();
        setResults(data);
    } catch (err) {
        console.error("Image search failed:", err);
        setResults([]);
    } finally {
        setIsLoading(false);
    }
  };

  const handleSelect = (item: SearchItem) => {
    setQuery(item.title || item.name || '');
    setIsOpen(false);
    setPreviewUrl(null);
    
    if (onSelect) {
        onSelect(item);
    } else {
        // Default behavior: go to detail page
        navigate(`/media/${item.type}/${item.id}/`);
    }
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
    setPreviewUrl(null);
  };

  return (
    <div className="relative w-full">
      <div className="relative flex items-center group">
        <div className="absolute left-4 z-10">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin text-blue-500" /> : <Search className="text-black/30 dark:text-white/30 w-5 h-5 group-focus-within:text-blue-500 transition-colors" />}
        </div>
        
        <Input
          id={id}
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || t('search.placeholder')}
          className="pl-12 pr-24"
          autoComplete="off"
        />

        <div className="absolute right-4 flex items-center gap-2">
            {imagePreview && (
                <div className="relative w-8 h-8 rounded-lg overflow-hidden border-2 border-yellow-400 group/preview">
                    <img src={imagePreview} className="w-full h-full object-cover" alt="" />
                    <button onClick={() => setPreviewUrl(null)} className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover/preview:opacity-100 transition-opacity">
                        <X className="w-3 h-3 text-white" />
                    </button>
                </div>
            )}
            
            <button 
                onClick={() => fileInputRef.current?.click()}
                className="p-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-xl transition-colors text-blue-500"
                title={t('search.image_search_hint')}
            >
                <Camera className="w-5 h-5" />
            </button>
            <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleImageSearch} />

            {query && (
                <button onClick={clearSearch} className="p-2 text-black/30 dark:text-white/30 hover:text-black/60 dark:hover:text-white/60 transition-colors">
                    <X className="w-5 h-5" />
                </button>
            )}
        </div>
      </div>

      {isOpen && (
        <Card className="absolute z-50 top-full mt-2 w-full overflow-hidden animate-fade-in shadow-2xl" padding="none">
          {isLoading ? (
            <div className="p-4 flex items-center gap-3 text-black/50 dark:text-white/50">
              <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
              {t('search.searching')}
            </div>
          ) : results.length === 0 ? (
            <div className="p-4 text-black/40 dark:text-white/40 text-sm italic">{t('search.no_results')}</div>
          ) : (
            <ul>
              {results.slice(0, 8).map((item, idx) => (
                <li key={item.id || idx}>
                  <button
                    onClick={() => handleSelect(item)}
                    className="w-full text-left px-5 py-4 hover:bg-gray-50 dark:hover:bg-white/5 transition-all flex items-center gap-4 group"
                  >
                    {item.image_url && (
                      <div className="relative">
                        <img src={item.image_url} alt="" className="w-10 h-14 object-cover rounded-xl flex-shrink-0 shadow-lg group-hover:scale-105 transition-transform" />
                        <div className="absolute inset-0 rounded-xl ring-1 ring-inset ring-black/10"></div>
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="font-black text-sm text-black dark:text-white group-hover:text-blue-500 transition-colors truncate uppercase tracking-tighter">
                        {item.title || item.name}
                      </p>
                      {item.type && (
                        <p className="text-[10px] font-black text-black/30 dark:text-white/30 uppercase tracking-[0.2em] mt-1">{item.type}</p>
                      )}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}
    </div>
  );
};
