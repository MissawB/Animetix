import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { RelicItem } from './components/RelicItem';
import { Book, Frame, Headphones, FlaskConical as Flask } from 'lucide-react';

const ForgeHubPage: React.FC = () => {
  const { t } = useTranslation();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = [
    { id: 'narrative', icon: Book, color: 'text-amber-500', glow: 'bg-amber-500' },
    { id: 'visual', icon: Frame, color: 'text-blue-500', glow: 'bg-blue-500' },
    { id: 'audio', icon: Headphones, color: 'text-emerald-500', glow: 'bg-emerald-500' },
    { id: 'experimental', icon: Flask, color: 'text-red-600', glow: 'bg-red-600' }
  ];

  return (
    <AnimatedPage>
      <div className="min-h-screen flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden bg-[#020202]">
        {/* Ambient Glows */}
        <div className="fixed inset-0 pointer-events-none z-0 opacity-10">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-red-600/20 blur-[150px] rounded-full" />
          <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-blue-600/20 blur-[150px] rounded-full" />
        </div>

        <header className="text-center mb-24 z-10">
          <p className="text-[10px] font-black uppercase tracking-[0.5em] text-red-500 mb-2">
            {t('forge_hub.subtitle')}
          </p>
          <h1 className="text-7xl font-black italic manga-font uppercase tracking-tighter text-white">
            {t('forge_hub.title').split(' ')[0]} <span className="text-red-600 drop-shadow-[0_0_15px_rgba(220,38,38,0.5)]">
              {t('forge_hub.title').split(' ').slice(1).join(' ')}
            </span>
          </h1>
        </header>

        <div className="flex flex-wrap gap-12 justify-center items-center z-10 max-w-7xl">
          {categories.map((cat) => (
            <RelicItem
              key={cat.id}
              id={cat.id}
              title={t(`forge_hub.categories.${cat.id}.title`)}
              sub={t(`forge_hub.categories.${cat.id}.sub`)}
              desc={t(`forge_hub.categories.${cat.id}.desc`)}
              color={cat.color}
              glowColor={cat.glow}
              onClick={() => setSelectedCategory(cat.id)}
            >
              <cat.icon className="w-full h-full stroke-[0.5]" />
            </RelicItem>
          ))}
        </div>

        <footer className="mt-24 opacity-20 text-center z-10">
          <p className="text-xs uppercase tracking-[0.4em] text-white">
            {t('forge_hub.description')}
          </p>
        </footer>
      </div>
    </AnimatedPage>
  );
};

export default ForgeHubPage;
