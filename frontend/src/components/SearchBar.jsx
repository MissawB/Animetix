import { useState, useCallback, useRef } from 'react';
import { searchMedia } from '../api';
import { Search, X } from 'lucide-react';

export function SearchBar({ onSelect, placeholder = 'Rechercher un anime, manga...' }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const debounceRef = useRef(null);

  const handleChange = useCallback((e) => {
    const val = e.target.value;
    setQuery(val);
    
    clearTimeout(debounceRef.current);
    if (val.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }
    
    debounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await searchMedia(val);
        setResults(data.results || []);
        setIsOpen(true);
      } catch {
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  }, []);

  const handleSelect = (item) => {
    setQuery(item.title || item.name || '');
    setIsOpen(false);
    if (onSelect) onSelect(item);
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
  };

  return (
    <div className="relative w-full">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-black/30 dark:text-anime-light-text dark:text-anime-dark-text/30 w-5 h-5" />
        <input
          id="search-input"
          type="text"
          value={query}
          onChange={handleChange}
          placeholder={placeholder}
          className="input-field pl-12 pr-10"
          autoComplete="off"
        />
        {query && (
          <button onClick={clearSearch} className="absolute right-3 top-1/2 -translate-y-1/2 text-black/30 dark:text-anime-light-text dark:text-anime-dark-text/30 hover:text-black/60 dark:text-anime-light-text dark:text-anime-dark-text/60 transition-colors">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {isOpen && (
        <div className="absolute z-50 top-full mt-2 w-full glass-card overflow-hidden animate-fade-in">
          {isLoading ? (
            <div className="p-4 flex items-center gap-3 text-black/50 dark:text-anime-light-text dark:text-anime-dark-text/50">
              <div className="w-4 h-4 border-2 border-anime-purple/50 border-t-anime-purple rounded-full animate-spin" />
              Recherche en cours...
            </div>
          ) : results.length === 0 ? (
            <div className="p-4 text-black/40 dark:text-anime-light-text dark:text-anime-dark-text/40 text-sm">Aucun résultat trouvé</div>
          ) : (
            <ul>
              {results.slice(0, 8).map((item, idx) => (
                <li key={item.id || idx}>
                  <button
                    onClick={() => handleSelect(item)}
                    className="w-full text-left px-4 py-3 hover:bg-black/5 dark:bg-white/5 transition-colors flex items-center gap-3 group"
                  >
                    {item.image_url && (
                      <img src={item.image_url} alt="" className="w-8 h-10 object-cover rounded-lg flex-shrink-0" />
                    )}
                    <div className="min-w-0">
                      <p className="font-medium text-anime-light-text dark:text-anime-dark-text group-hover:text-anime-purple-light transition-colors truncate">
                        {item.title || item.name}
                      </p>
                      {item.type && (
                        <p className="text-xs text-black/40 dark:text-anime-light-text dark:text-anime-dark-text/40">{item.type}</p>
                      )}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
