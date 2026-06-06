import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { motion } from 'framer-motion';
import { Search, Filter, TrendingUp, Play, Info, Plus, ChevronRight, ChevronLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const ExplorePage: React.FC = () => {
  const [mediaType, setMediaType] = React.useState('Anime');
  
  const { data, isLoading } = useQuery({
    queryKey: ['explore', mediaType],
    queryFn: async () => {
      const res = await fetch(`/api/explore/?media_type=${mediaType}`);
      return res.json();
    }
  });

  const scrollLeft = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollBy({ left: -400, behavior: 'smooth' });
  };

  const scrollRight = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollBy({ left: 400, behavior: 'smooth' });
  };

  const MediaCard = ({ item }: { item: any }) => (
    <motion.div 
      whileHover={{ scale: 1.05, zIndex: 10 }}
      className="flex-none w-48 md:w-56 aspect-[2/3] rounded-xl overflow-hidden relative group cursor-pointer"
    >
      <img 
        src={item.image || 'https://via.placeholder.com/300x450'} 
        alt={item.title}
        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
        <h4 className="text-sm font-black uppercase italic leading-tight mb-2">{item.title}</h4>
        <div className="flex gap-2">
            <button className="p-2 bg-white text-black rounded-full hover:bg-gray-200 transition-colors">
                <Play size={14} fill="currentColor" />
            </button>
            <button className="p-2 bg-gray-800/80 text-white rounded-full hover:bg-gray-700 transition-colors">
                <Plus size={14} />
            </button>
            <Link to={`/media/${mediaType.toLowerCase()}/${item.id}/`} className="p-2 bg-gray-800/80 text-white rounded-full hover:bg-gray-700 transition-colors">
                <Info size={14} />
            </Link>
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Hero Section */}
      <section className="relative h-[70vh] w-full overflow-hidden">
        {data?.trending?.[0] && (
            <>
                <img 
                    src={data.trending[0].image} 
                    className="absolute inset-0 w-full h-full object-cover opacity-40 blur-sm scale-105"
                    alt="Hero Background"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-transparent to-transparent" />
                
                <div className="absolute bottom-20 left-12 max-w-2xl space-y-6">
                    <motion.div 
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center gap-2 text-yellow-500 font-black uppercase tracking-widest text-xs"
                    >
                        <TrendingUp size={16} /> #1 Tendances {mediaType}
                    </motion.div>
                    <motion.h1 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-6xl md:text-8xl font-black italic uppercase tracking-tighter leading-none"
                    >
                        {data.trending[0].title}
                    </motion.h1>
                    <motion.p 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className="text-gray-400 text-lg line-clamp-3 font-medium leading-relaxed"
                    >
                        {data.trending[0].synopsis_fr || data.trending[0].synopsis_en || data.trending[0].description}
                    </motion.p>
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6 }}
                        className="flex gap-4"
                    >
                        <button className="px-8 py-4 bg-white text-black font-black uppercase italic rounded-xl flex items-center gap-2 hover:bg-gray-200 transition-all hover:scale-105">
                            <Play fill="currentColor" size={20} /> Commencer
                        </button>
                        <Link to={`/media/${mediaType.toLowerCase()}/${data.trending[0].id}/`} className="px-8 py-4 bg-gray-800/80 text-white font-black uppercase italic rounded-xl flex items-center gap-2 hover:bg-gray-700 transition-all">
                            <Info size={20} /> Plus d'infos
                        </Link>
                    </motion.div>
                </div>
            </>
        )}
      </section>

      <div className="px-12 -mt-12 relative z-20 space-y-16 pb-24">
        {/* Media Selector */}
        <div className="flex gap-6 border-b border-white/5 pb-4">
            {['Anime', 'Manga', 'Game', 'Movie'].map(type => (
                <button 
                    key={type}
                    onClick={() => setMediaType(type)}
                    className={`text-sm font-black uppercase tracking-widest transition-all ${
                        mediaType === type ? 'text-blue-500 scale-110' : 'text-gray-500 hover:text-white'
                    }`}
                >
                    {type}s
                </button>
            ))}
        </div>

        {/* Categories Rows */}
        <section className="space-y-12">
            {/* Recommendations Row */}
            {data?.recommendations?.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-2xl font-black italic uppercase tracking-widest flex items-center gap-3">
                        Choisi pour vous
                        <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded font-normal not-italic ml-2">IA : SUGGESTION</span>
                        <span className="h-px bg-blue-500/30 flex-1" />
                    </h2>
                    <div className="relative group">
                        <button 
                            onClick={() => scrollLeft('recs-row')}
                            className="absolute left-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                        >
                            <ChevronLeft size={32} />
                        </button>
                        <div 
                            id="recs-row"
                            className="flex gap-6 overflow-x-auto no-scrollbar pb-4"
                        >
                            {data.recommendations.map((item: any) => (
                                <MediaCard key={item.id} item={item} />
                            ))}
                        </div>
                        <button 
                            onClick={() => scrollRight('recs-row')}
                            className="absolute right-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                        >
                            <ChevronRight size={32} />
                        </button>
                    </div>
                </div>
            )}

            <div className="space-y-4">
                <h2 className="text-2xl font-black italic uppercase tracking-widest flex items-center gap-3">
                    Tendances Actuelles
                    <span className="h-px bg-blue-500/30 flex-1" />
                </h2>
                <div className="relative group">
                    <button 
                        onClick={() => scrollLeft('trending-row')}
                        className="absolute left-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                    >
                        <ChevronLeft size={32} />
                    </button>
                    <div 
                        id="trending-row"
                        className="flex gap-6 overflow-x-auto no-scrollbar pb-4"
                    >
                        {data?.trending?.map((item: any) => (
                            <MediaCard key={item.id} item={item} />
                        ))}
                    </div>
                    <button 
                        onClick={() => scrollRight('trending-row')}
                        className="absolute right-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                    >
                        <ChevronRight size={32} />
                    </button>
                </div>
            </div>

            {data?.categories?.map((cat: any, idx: number) => (
                <div key={idx} className="space-y-4">
                    <h2 className="text-xl font-black italic uppercase tracking-widest flex items-center gap-3">
                        {cat.name}
                        <span className="h-px bg-white/5 flex-1" />
                    </h2>
                    <div className="relative group">
                        <button 
                            onClick={() => scrollLeft(`cat-row-${idx}`)}
                            className="absolute left-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                        >
                            <ChevronLeft size={32} />
                        </button>
                        <div 
                            id={`cat-row-${idx}`}
                            className="flex gap-6 overflow-x-auto no-scrollbar pb-4"
                        >
                            {cat.items.map((item: any) => (
                                <MediaCard key={item.id} item={item} />
                            ))}
                        </div>
                        <button 
                            onClick={() => scrollRight(`cat-row-${idx}`)}
                            className="absolute right-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                        >
                            <ChevronRight size={32} />
                        </button>
                    </div>
                </div>
            ))}
        </section>
      </div>

      <style>{`
        .no-scrollbar::-webkit-scrollbar {
            display: none;
        }
        .no-scrollbar {
            -ms-overflow-style: none;
            scrollbar-width: none;
        }
      `}</style>
    </div>
  );
};

export default ExplorePage;
