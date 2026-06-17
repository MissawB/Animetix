import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Gamepad2, 
  Brain, 
  Zap, 
  Eye, 
  Music, 
  MessageCircle, 
  Ghost, 
  Code,
  Sparkles,
  Trophy,
  ArrowRight,
  Flame,
  Calendar,
  ShieldCheck,
  Search,
  Swords
} from 'lucide-react';
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const GamesHubPage: React.FC = () => {
  const games = [
    {
      title: "La Forge",
      desc: "Fusionnez deux univers d'anime et générez un Visual Novel complet avec l'IA.",
      icon: Flame,
      path: "/forge/",
      color: "text-orange-500",
      bg: "bg-orange-500/10",
      difficulty: "Créatif",
      reward: "500 XP"
    },
    {
      title: "Versus Battle",
      desc: "Simulez des combats mythiques arbitrés par une IA de combat SOTA.",
      icon: Zap,
      path: "/game/vsbattle/",
      color: "text-red-500",
      bg: "bg-red-500/10",
      difficulty: "Hardcore",
      reward: "300 XP"
    },
    {
      title: "Duel Arena",
      desc: "Affrontez d'autres joueurs en 1vs1 temps réel dans des duels de culture anime.",
      icon: Swords,
      path: "/game/duel/lobby/",
      color: "text-blue-500",
      bg: "bg-blue-500/10",
      difficulty: "Compétitif",
      reward: "600 XP"
    },
    {
        title: "Akinetix Expert",
        desc: "L'IA tente de deviner votre personnage pendant que vous l'entraînez par RL.",
        icon: Brain,
        path: "/akinetix-expert/",
        color: "text-cyan-500",
        bg: "bg-cyan-500/10",
        difficulty: "Mental",
        reward: "450 XP"
      },
    {
      title: "Daily Challenge",
      desc: "Un défi unique chaque jour. Testez vos connaissances et gardez votre série active !",
      icon: Calendar,
      path: "/daily-challenge/",
      color: "text-amber-500",
      bg: "bg-amber-500/10",
      difficulty: "Variable",
      reward: "🔥 Bonus Streak"
    },
    {
      title: "Vision Quest",
      desc: "Identifiez les animés et personnages à partir de fragments d'images générés.",
      icon: Eye,
      path: "/vision/",
      color: "text-blue-500",
      bg: "bg-blue-500/10",
      difficulty: "Moyen",
      reward: "200 XP"
    },
    {
      title: "Anime Blindtest",
      desc: "Reconnaissez les OST mythiques transformées ou filtrées par l'IA.",
      icon: Music,
      path: "/blindtest/",
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
      difficulty: "Expert",
      reward: "350 XP"
    },
    {
      title: "Emoji Master",
      desc: "Devinez l'œuvre cachée derrière une série d'emojis cryptiques.",
      icon: MessageCircle,
      path: "/emoji/",
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
      difficulty: "Facile",
      reward: "100 XP"
    },
    {
      title: "Le Paradoxe",
      desc: "Résolvez des énigmes temporelles où les chronologies d'anime s'entremêlent.",
      icon: Ghost,
      path: "/paradox/",
      color: "text-purple-500",
      bg: "bg-purple-500/10",
      difficulty: "Casse-tête",
      reward: "400 XP"
    },
    {
      title: "Code Manga",
      desc: "Décodez les messages secrets cachés dans des planches de manga OCRisées.",
      icon: Code,
      path: "/codemanga/room/lobby/",
      color: "text-gray-400",
      bg: "bg-gray-400/10",
      difficulty: "Technique",
      reward: "250 XP"
    },
    {
      title: "Animinator",
      desc: "Le génie omniscient capable de deviner n'importe quelle œuvre en un clin d'œil.",
      icon: Sparkles,
      path: "/animinator/",
      color: "text-blue-400",
      bg: "bg-blue-400/10",
      difficulty: "Mystique",
      reward: "150 XP"
    },
    {
      title: "Undercover",
      desc: "Infiltrez-vous dans un groupe de fans d'anime et débusquez l'intrus.",
      icon: ShieldCheck,
      path: "/undercover/room/lobby/",
      color: "text-red-400",
      bg: "bg-red-400/10",
      difficulty: "Social",
      reward: "300 XP"
    },
    {
      title: "Akinetix Classic",
      desc: "Le jeu de devinette original, optimisé pour une expérience rapide.",
      icon: Search,
      path: "/akinetix/",
      color: "text-orange-400",
      bg: "bg-orange-400/10",
      difficulty: "Standard",
      reward: "100 XP"
    }
  ];

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-16 flex flex-col md:flex-row justify-between items-end gap-8">
            <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] font-black uppercase tracking-widest text-blue-500 mb-4">
                    <Gamepad2 className="w-3 h-3" /> Entertainment Sector
                </div>
                <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4 leading-none">
                    GAMES <span className="text-blue-500 text-glow">NEXUS</span>
                </h1>
                <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                    Défiez les algorithmes et gagnez des points de rang dans le multivers d'Animetix.
                </p>
            </div>
            
            <div className="flex gap-4">
                <div className="text-right">
                    <p className="text-[10px] font-black uppercase opacity-40 mb-1">Ranked Season</p>
                    <Badge variant="primary" className="bg-blue-600/10 text-blue-500 border-blue-500/20">PHASE 2 : EVOLUTION</Badge>
                </div>
            </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {games.map((game) => (
            <Link key={game.title} to={game.path} className="no-underline group">
              <Card 
                padding="lg" 
                className="h-full border-white/5 bg-navy-900/50 hover:bg-white/5 hover:border-blue-500/30 transition-all duration-500 hover:-translate-y-2 relative overflow-hidden"
              >
                {/* Background Decoration */}
                <game.icon className={`absolute -right-8 -bottom-8 w-48 h-48 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity ${game.color}`} />
                
                <div className="relative z-10 space-y-6">
                  <div className="flex justify-between items-start">
                    <div className={`p-4 rounded-2xl ${game.bg}`}>
                        <game.icon className={`w-8 h-8 ${game.color}`} />
                    </div>
                    <div className="flex flex-col items-end gap-1">
                        <Badge variant="neutral" className="bg-white/5 border-white/10 text-[9px] tracking-widest font-black italic">{game.difficulty}</Badge>
                        <span className="text-[9px] font-black text-yellow-500 uppercase tracking-widest">{game.reward}</span>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-3xl font-black italic manga-font uppercase mb-2 group-hover:text-blue-400 transition-colors">
                        {game.title}
                    </h3>
                    <p className="text-xs font-bold leading-relaxed opacity-40 uppercase tracking-wider">
                        {game.desc}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-blue-500 opacity-0 group-hover:opacity-100 translate-x-[-10px] group-hover:translate-x-0 transition-all">
                      Lancer la session <ArrowRight className="w-3 h-3" />
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>

        {/* Global Leaderboard Call to Action */}
        <div className="mt-24 p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-white/5 flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-8">
                <div className="p-6 bg-blue-600 rounded-3xl shadow-[0_0_30px_rgba(59,130,246,0.5)]">
                    <Trophy className="w-12 h-12 text-white" />
                </div>
                <div>
                    <h4 className="text-3xl font-black italic manga-font uppercase mb-2">Classement Mondial</h4>
                    <p className="text-sm font-bold opacity-40 uppercase tracking-wide">
                        Comparez vos scores avec les meilleurs joueurs de la communauté.
                    </p>
                </div>
            </div>
            <Button as={Link} to="/leaderboard/" variant="outline" className="px-10 py-4 border-white/10 hover:bg-white/5 rounded-2xl">
                VOIR LE LEADERBOARD
            </Button>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default GamesHubPage;


