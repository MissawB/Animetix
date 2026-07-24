import React from 'react';
import { Link } from 'react-router-dom';
import {
  Brain,
  Zap,
  Eye,
  Music,
  MessageCircle,
  Ghost,
  Code,
  Trophy,
  ArrowRight,
  Flame,
  Calendar,
  ShieldCheck,
  Search,
  Swords,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { useTranslation } from 'react-i18next';

const GamesHubPage: React.FC = () => {
  const { t } = useTranslation();
  const games = [
    {
      title: t('games.hub.list.forge.title', 'La Forge'),
      desc: t(
        'games.hub.list.forge.desc',
        "Fusionnez deux univers d'anime et générez un Visual Novel complet avec l'IA.",
      ),
      icon: Flame,
      path: '/forge/',
      difficulty: t('games.hub.list.forge.difficulty', 'Créatif'),
      reward: '500 XP',
    },
    {
      title: 'Versus Battle',
      desc: t(
        'games.hub.list.versus.desc',
        'Simulez des combats mythiques arbitrés par une IA de combat SOTA.',
      ),
      icon: Zap,
      path: '/game/vsbattle/',
      difficulty: t('games.hub.list.versus.difficulty', 'Hardcore'),
      reward: '300 XP',
    },
    {
      title: 'Duel Arena',
      desc: t(
        'games.hub.list.duel.desc',
        "Affrontez d'autres joueurs en 1vs1 temps réel dans des duels de culture anime.",
      ),
      icon: Swords,
      path: '/game/duel/lobby/',
      difficulty: t('games.hub.list.duel.difficulty', 'Compétitif'),
      reward: '600 XP',
    },
    {
      title: 'Akinetix Expert',
      desc: t(
        'games.hub.list.akinetix_expert.desc',
        "L'IA tente de deviner votre personnage pendant que vous l'entraînez par RL.",
      ),
      icon: Brain,
      path: '/akinetix-expert/',
      difficulty: t('games.hub.list.akinetix_expert.difficulty', 'Mental'),
      reward: '450 XP',
    },
    {
      title: 'Daily Challenge',
      desc: t(
        'games.hub.list.daily.desc',
        'Un défi unique chaque jour. Testez vos connaissances et gardez votre série active !',
      ),
      icon: Calendar,
      path: '/daily-challenge/',
      difficulty: t('games.hub.list.daily.difficulty', 'Variable'),
      reward: '🔥 Bonus Streak',
    },
    {
      title: 'Vision Quest',
      desc: t(
        'games.hub.list.vision.desc',
        "Identifiez les animés et personnages à partir de fragments d'images générés.",
      ),
      icon: Eye,
      path: '/vision/',
      difficulty: t('games.hub.list.vision.difficulty', 'Moyen'),
      reward: '200 XP',
    },
    {
      title: 'Anime Blindtest',
      desc: t(
        'games.hub.list.blindtest.desc',
        "Reconnaissez les OST mythiques transformées ou filtrées par l'IA.",
      ),
      icon: Music,
      path: '/blindtest/',
      difficulty: t('games.hub.list.blindtest.difficulty', 'Expert'),
      reward: '350 XP',
    },
    {
      title: 'Emoji Master',
      desc: t(
        'games.hub.list.emoji.desc',
        "Devinez l'œuvre cachée derrière une série d'emojis cryptiques.",
      ),
      icon: MessageCircle,
      path: '/emoji/',
      difficulty: t('games.hub.list.emoji.difficulty', 'Facile'),
      reward: '100 XP',
    },
    {
      title: t('games.hub.list.paradox.title', 'Le Paradoxe'),
      desc: t(
        'games.hub.list.paradox.desc',
        "Résolvez des énigmes temporelles où les chronologies d'anime s'entremêlent.",
      ),
      icon: Ghost,
      path: '/paradox/',
      difficulty: t('games.hub.list.paradox.difficulty', 'Casse-tête'),
      reward: '400 XP',
    },
    {
      title: 'Code Manga',
      desc: t(
        'games.hub.list.codemanga.desc',
        'Deux équipes, deux espions : décryptez les cartes anime/manga de votre équipe.',
      ),
      icon: Code,
      path: '/codemanga/',
      difficulty: t('games.hub.list.codemanga.difficulty', 'Social'),
      reward: '300 XP',
    },
    {
      title: 'Undercover',
      desc: t(
        'games.hub.list.undercover.desc',
        "Infiltrez-vous dans un groupe de fans d'anime et débusquez l'intrus.",
      ),
      icon: ShieldCheck,
      path: '/undercover/',
      difficulty: t('games.hub.list.undercover.difficulty', 'Social'),
      reward: '300 XP',
    },
    {
      title: 'Akinetix',
      desc: t(
        'games.hub.list.akinetix.desc',
        "Devine-l'œuvre : laisse l'IA te cuisiner, ou interroge le génie. Anime, manga ou personnage.",
      ),
      icon: Search,
      path: '/akinetix/',
      difficulty: t('games.hub.list.akinetix.difficulty', 'Standard'),
      reward: '100 XP',
    },
  ];

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <header className="relative mb-16 flex flex-col md:flex-row justify-between items-end gap-8">
            <div
              className="explore-halftone pointer-events-none absolute -inset-x-6 -top-12 h-48"
              aria-hidden
            />
            <div className="relative">
              <div className="flex items-center gap-3 mb-4">
                <span className="explore-stamp -rotate-2" aria-hidden>
                  遊
                </span>
                <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                  Entertainment Sector
                </span>
              </div>
              <h1 className="font-manga text-6xl md:text-7xl font-black italic tracking-tighter uppercase mb-4 leading-none text-[#F4F1E8]">
                GAMES <span className="text-[#E8442B]">NEXUS</span>
              </h1>
              <p className="text-base leading-relaxed text-[#8F94A5] max-w-2xl">
                {t(
                  'games.hub.tagline',
                  "Défiez les algorithmes et gagnez des points de rang dans le multivers d'Animetix.",
                )}
              </p>
            </div>

            <div className="relative flex gap-4">
              <div className="text-right">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] mb-2">
                  Ranked Season
                </p>
                <span className="inline-block rounded-[2px] border-2 border-[#E8442B] px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[#E8442B]">
                  PHASE 2 : EVOLUTION
                </span>
              </div>
            </div>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {games.map((game) => (
              <Link key={game.title} to={game.path} className="no-underline group">
                <section className="relative h-full overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 transition-all duration-500 hover:-translate-y-2 hover:border-[#E8442B]/40">
                  {/* Décor de fond */}
                  <game.icon className="absolute -right-8 -bottom-8 w-48 h-48 text-[#F4F1E8] opacity-[0.03] transition-opacity group-hover:opacity-[0.06]" />

                  <div className="relative z-10 space-y-6">
                    <div className="flex justify-between items-start">
                      <div className="p-4 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]">
                        <game.icon className="w-8 h-8 text-[#F4F1E8] transition-colors group-hover:text-[#E8442B]" />
                      </div>
                      <div className="flex flex-col items-end gap-1.5">
                        <span className="rounded-full border border-[#F4F1E8]/15 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                          {game.difficulty}
                        </span>
                        <span className="text-[9px] font-black text-[#FDB913] uppercase tracking-widest">
                          {game.reward}
                        </span>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-manga text-3xl font-black italic uppercase mb-2 text-[#F4F1E8] transition-colors group-hover:text-[#E8442B]">
                        {game.title}
                      </h3>
                      <p className="text-sm leading-relaxed text-[#8F94A5]">{game.desc}</p>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#E8442B] opacity-0 group-hover:opacity-100 translate-x-[-10px] group-hover:translate-x-0 transition-all">
                      {t('games.hub.launch_session', 'Lancer la session')}{' '}
                      <ArrowRight className="w-3 h-3" />
                    </div>
                  </div>
                </section>
              </Link>
            ))}
          </div>

          {/* Classement mondial */}
          <div className="mt-24 p-10 md:p-12 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-8">
              <div className="p-6 rounded-xl border border-[#E8442B]/30 bg-[#E8442B]/10">
                <Trophy className="w-12 h-12 text-[#E8442B]" />
              </div>
              <div>
                <h4 className="font-manga text-3xl font-black italic uppercase mb-2 text-[#F4F1E8]">
                  {t('games.hub.leaderboard_title', 'Classement Mondial')}
                </h4>
                <p className="text-sm leading-relaxed text-[#8F94A5]">
                  {t(
                    'games.hub.leaderboard_desc',
                    'Comparez vos scores avec les meilleurs joueurs de la communauté.',
                  )}
                </p>
              </div>
            </div>
            <Button
              as={Link}
              to="/leaderboard/"
              variant="outline"
              className="px-10 py-4 rounded-xl border-[#F4F1E8]/15 text-[#F4F1E8] hover:border-[#FDB913] hover:bg-transparent"
            >
              {t('games.hub.view_leaderboard', 'VOIR LE LEADERBOARD')}
            </Button>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default GamesHubPage;
