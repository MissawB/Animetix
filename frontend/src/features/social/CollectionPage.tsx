import React from 'react';
import { Bookmark, Sparkles, Image as ImageIcon, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CreativeFusion } from '../../types';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';

import { useTranslation } from 'react-i18next';

const CollectionPage: React.FC = () => {
  const { t } = useTranslation();

  const { data: fusions, isLoading } = useQuery<CreativeFusion[]>({
    queryKey: ['collection'],
    queryFn: () => apiClient('/api/v1/social/collection/'),
  });

  if (isLoading) return (
    <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
        </div>
    </div>
  );

  return (
    
      <div className="max-w-7xl mx-auto px-6 py-16">
        <h1 className="text-5xl font-black italic manga-font mb-12 text-center tracking-tighter uppercase">
          MA <span className="text-yellow-400">COLLECTION</span>
        </h1>

        {!fusions || fusions.length === 0 ? (
          <Card padding="lg" className="text-center py-20 bg-white/5 border-4 border-dashed border-white/10">
            <Bookmark className="w-20 h-20 text-white opacity-10 mx-auto mb-6" />
            <p className="text-xl font-bold opacity-30 italic uppercase tracking-widest">Votre galerie est vide. Explorez l'Archetypist !</p>
            <Button as={Link} to="/forge/" variant="primary" size="lg" className="mt-8 italic bg-yellow-400 text-black border-none px-12">
              CRÉER UNE FUSION
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
            {fusions.map((fusion: any) => (
              <Card key={fusion.id} padding="none" className="group overflow-hidden transition-all hover:scale-[1.05] hover:rotate-1">
                <div className="aspect-[3/4] relative overflow-hidden bg-black shadow-inner">
                  {fusion.image_url ? (
                    <img src={fusion.image_url} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" alt={fusion.title_a} />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center opacity-20">
                      <ImageIcon className="w-16 h-16 text-white" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity"></div>
                </div>
                
                <div className="p-6">
                  <h3 className="font-black italic text-lg leading-none mb-4 truncate uppercase manga-font">
                    {fusion.title_a} <span className="text-yellow-400">×</span> {fusion.title_b}
                  </h3>
                  <div className="flex items-center justify-between">
                    <Badge variant="neutral" className="text-[8px]">{fusion.media_type_a}</Badge>
                    <div className="flex gap-2">
                      <Button variant="outline" className="p-2 rounded-xl border-none hover:bg-red-500/10 text-red-500">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                      <Button variant="outline" className="p-2 rounded-xl border-none hover:bg-yellow-400/10 text-yellow-400">
                        <Sparkles className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    
  );
};

export default CollectionPage;
