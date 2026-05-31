import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Gamepad2, Brain, Zap } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from './components/ui/Button';
import { Card } from './components/ui/Card';
import { AnimatedPage } from './components/ui/AnimatedPage';
import { DynamicAuraWrapper } from './components/shared/DynamicAuraWrapper';
import './App.css';

const App: React.FC = () => {
  const { t } = useTranslation();

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-24 text-center relative overflow-hidden">
        <DynamicAuraWrapper>
          {/* Decorative Glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-accent/10 blur-[150px] rounded-full -z-10 animate-pulse" />

          <div className="space-y-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-accent/10 border border-brand-accent/20 text-brand-accent text-[10px] font-black uppercase tracking-[0.3em] mb-4">
               <Zap className="w-3 h-3 fill-current" /> {t('home.engine_badge')}
            </div>

            <h1 className="text-8xl md:text-9xl font-black italic manga-font tracking-tighter leading-[0.85] mb-8">
              {t('home.welcome')} <br />
              <span className="text-brand-accent drop-shadow-[0_0_30px_rgba(var(--color-accent),0.3)]">ANIMETIX</span>
            </h1>
            
            <p className="max-w-2xl mx-auto text-xl font-bold opacity-40 uppercase tracking-[0.4em] leading-relaxed">
               {t('home.description')} <br />
               <span className="text-xs opacity-60 uppercase">{t('home.sub_description')}</span>
            </p>

            <div className="flex flex-wrap justify-center gap-6 pt-12">
                <Button 
                    as={Link}
                    to="/forge/" 
                    size="lg"
                    className="group relative bg-brand-accent text-black px-10 py-6 rounded-[2rem] font-black italic text-2xl uppercase shadow-2xl hover:scale-105 active:scale-95 transition-all flex items-center gap-4 no-underline border-none"
                >
                    <div className="absolute -inset-1 bg-brand-accent blur-md opacity-30 group-hover:opacity-60 transition-opacity rounded-[2rem]" />
                    <Sparkles className="w-8 h-8 relative z-10" />
                    <span className="relative z-10 text-nowrap">{t('home.enter_forge')}</span>
                </Button>

                <Button 
                    as={Link}
                    to="/game/classic/" 
                    variant="outline"
                    size="lg"
                    className="bg-black text-white dark:bg-white dark:text-black px-10 py-6 rounded-[2rem] font-black italic text-2xl uppercase shadow-xl hover:scale-105 active:scale-95 transition-all flex items-center gap-4 no-underline border-none"
                >
                    <Gamepad2 className="w-8 h-8" />
                    <span className="text-nowrap">{t('home.play_classic')}</span>
                </Button>

                <Button 
                    as={Link}
                    to="/akinetix-expert/" 
                    size="lg"
                    variant="secondary"
                    className="px-10 py-6 rounded-[2rem] font-black italic text-2xl uppercase shadow-xl hover:scale-105 active:scale-95 transition-all flex items-center gap-4 no-underline border-none"
                >
                    <Brain className="w-8 h-8" />
                    <span className="text-nowrap">{t('home.akinetix_expert')}</span>
                </Button>

                <Button 
                    as={Link}
                    to="/game/vsbattle/" 
                    size="lg"
                    className="bg-red-500 text-white px-10 py-6 rounded-[2rem] font-black italic text-2xl uppercase shadow-xl hover:scale-105 active:scale-95 transition-all flex items-center gap-4 no-underline border-none"
                >
                    <Zap className="w-8 h-8" />
                    <span className="text-nowrap">VERSUS BATTLE</span>
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto pt-24">
                <Card className="group hover:-translate-y-2 transition-transform text-left" padding="lg">
                    <Brain className="w-10 h-10 text-brand-primary mb-6" />
                    <h3 className="text-lg font-black italic manga-font mb-2 uppercase">{t('home.features.cognition.title')}</h3>
                    <p className="text-[10px] font-bold opacity-30 uppercase leading-loose">{t('home.features.cognition.desc')}</p>
                </Card>
                <Card className="group hover:-translate-y-2 transition-transform text-left" padding="lg">
                    <Sparkles className="w-10 h-10 text-brand-accent mb-6" />
                    <h3 className="text-lg font-black italic manga-font mb-2 uppercase">{t('home.features.synthesis.title')}</h3>
                    <p className="text-[10px] font-bold opacity-30 uppercase leading-loose">{t('home.features.synthesis.desc')}</p>
                </Card>
                <Link to="/latent-space/" className="no-underline">
                  <Card className="group hover:-translate-y-2 transition-transform text-left h-full" padding="lg">
                      <Zap className="w-10 h-10 text-blue-400 mb-6" />
                      <h3 className="text-lg font-black italic manga-font mb-2 uppercase">{t('home.features.latent.title')}</h3>
                      <p className="text-[10px] font-bold opacity-30 uppercase leading-loose text-surface-text">{t('home.features.latent.desc')}</p>
                  </Card>
                </Link>
            </div>
          </div>
        </DynamicAuraWrapper>
      </div>
    </AnimatedPage>
  );
}

export default App;
