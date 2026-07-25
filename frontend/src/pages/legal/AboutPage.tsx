import React from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, Cpu, Users } from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

/**
 * Page "À propos" — page publique requise (AdSense : transparence & confiance).
 * Texte FR par défaut inline; traductions EN dans les fragments i18n (legal.*).
 */
const AboutPage: React.FC = () => {
  const { t } = useTranslation();

  const blocks: { icon: React.ReactNode; title: string; body: string }[] = [
    {
      icon: <Sparkles className="w-5 h-5" />,
      title: t('legal.about.mission.title', 'Notre mission'),
      body: t(
        'legal.about.mission.body',
        "Animetix explore l'univers de l'animation et du manga à travers l'intelligence artificielle : deviner un personnage en 20 questions, résoudre des énigmes narratives, générer des créations visuelles et sonores. L'objectif est de rendre la découverte de la culture anime à la fois ludique et intelligente.",
      ),
    },
    {
      icon: <Cpu className="w-5 h-5" />,
      title: t('legal.about.tech.title', 'La technologie'),
      body: t(
        'legal.about.tech.body',
        "La plateforme combine un moteur de raisonnement par IA, une base de connaissances en graphe (Neo4j), de la recherche vectorielle sémantique et des modèles génératifs (image, voix, texte). Les jeux de logique restent gratuits ; les fonctionnalités GPU/IA utilisent des crédits appelés Berrix, que l'on gagne en jouant — aucun achat n'est nécessaire.",
      ),
    },
    {
      icon: <Users className="w-5 h-5" />,
      title: t('legal.about.author.title', "L'auteur"),
      body: t(
        'legal.about.author.body',
        "Animetix est un projet indépendant conçu et développé par un passionné d'anime et d'ingénierie IA. Il est en évolution continue, avec de nouveaux modes de jeu et de nouveaux Labs ajoutés régulièrement.",
      ),
    },
  ];

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-3xl mx-auto px-6 py-16">
          <header className="mb-10 text-center">
            <div className="mb-5 flex items-center justify-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                誌
              </span>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                À propos
              </span>
            </div>
            <h1 className="text-4xl md:text-6xl font-black italic font-manga tracking-tighter uppercase mb-4 text-[#F4F1E8]">
              {t('legal.about.title', 'À propos d’Animetix')}
            </h1>
            <p className="text-base text-[#8F94A5] font-bold max-w-2xl mx-auto leading-relaxed">
              {t(
                'legal.about.intro',
                "Animetix (Anime Archetype Engine) est une plateforme interactive où l'IA rencontre la culture anime : jeux, laboratoires créatifs et exploration de connaissances.",
              )}
            </p>
          </header>

          <div className="space-y-6">
            {blocks.map((block) => (
              <section
                key={block.title}
                className="flex gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8"
              >
                <div className="shrink-0 w-11 h-11 rounded-xl bg-[#E8442B]/10 text-[#E8442B] flex items-center justify-center">
                  {block.icon}
                </div>
                <div className="space-y-2">
                  <h2 className="text-lg font-black uppercase tracking-wide font-manga italic text-[#F4F1E8]">
                    {block.title}
                  </h2>
                  <p className="text-sm leading-relaxed text-[#8F94A5]">{block.body}</p>
                </div>
              </section>
            ))}
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AboutPage;
