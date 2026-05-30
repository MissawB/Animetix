import React from 'react';
import { Link } from 'react-router-dom';
import { 
  FlaskConical, 
  Video, 
  Volume2, 
  Layers, 
  Zap, 
  Layout, 
  Database,
  ArrowRight,
  ShieldAlert,
  Cpu
} from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const LabHubPage: React.FC = () => {
  const labs = [
    {
      title: "Video Lab",
      desc: "Transfert de style temporel SOTA FateZero. Transformez vos vidéos en chefs-d'œuvre d'animation.",
      icon: Video,
      path: "/video-lab/",
      color: "text-red-500",
      bg: "bg-red-500/10",
      tier: "Premium"
    },
    {
      title: "Spatial Lab",
      desc: "Reconstruction 3D Gaussian Splatting & Depth Estimation. Créez des dioramas immersifs.",
      icon: Layers,
      path: "/spatial-lab/",
      color: "text-blue-500",
      bg: "bg-blue-500/10",
      tier: "Premium"
    },
    {
      title: "Manga Lab",
      desc: "OCR & In-painting pour planches de manga. Nettoyage et traduction automatique par IA.",
      icon: Layout,
      path: "/manga_lab/",
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
      tier: "Beta"
    },
    {
      title: "Audio Lab",
      desc: "Clonage vocal Zero-Shot & Synthèse de Soundscapes. Donnez une voix à vos personnages.",
      icon: Volume2,
      path: "/audio_lab/",
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
      tier: "Pro"
    },
    {
      title: "Latent Space",
      desc: "Navigation vectorielle 3D dans le Lore. Explorez les connexions sémantiques infinies.",
      icon: Database,
      path: "/latent-space/",
      color: "text-purple-500",
      bg: "bg-purple-500/10",
      tier: "Public"
    },
    {
        title: "Singularity",
        desc: "Modules IA de 5ème génération. Méta-compilation, Plasticité synaptique et Multivers.",
        icon: Cpu,
        path: "/experimental/",
        color: "text-red-600",
        bg: "bg-red-600/10",
        tier: "Experimental"
      }
  ];

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-16 text-center md:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-gray-500 mb-4">
                <FlaskConical className="w-3 h-3" /> Experimental Division
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                AI <span className="text-red-500 text-glow">LABORATORIES</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Accédez aux moteurs d'inférence de pointe et aux protocoles expérimentaux d'Animetix.
            </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {labs.map((lab) => (
            <Link key={lab.title} to={lab.path} className="no-underline group">
              <Card 
                padding="lg" 
                className="h-full border-white/5 bg-navy-900/50 hover:bg-white/5 hover:border-white/10 transition-all duration-500 hover:-translate-y-2 relative overflow-hidden"
              >
                {/* Background Decoration */}
                <lab.icon className={`absolute -right-8 -bottom-8 w-48 h-48 opacity-[0.03] group-hover:opacity-[0.07] transition-opacity ${lab.color}`} />
                
                <div className="relative z-10 space-y-6">
                  <div className="flex justify-between items-start">
                    <div className={`p-4 rounded-2xl ${lab.bg}`}>
                        <lab.icon className={`w-8 h-8 ${lab.color}`} />
                    </div>
                    <Badge variant="neutral" className="bg-white/5 border-white/10 text-[10px] tracking-widest font-black italic">{lab.tier}</Badge>
                  </div>

                  <div>
                    <h3 className="text-2xl font-black italic manga-font uppercase mb-2 group-hover:text-red-500 transition-colors">
                        {lab.title}
                    </h3>
                    <p className="text-xs font-bold leading-relaxed opacity-40 uppercase tracking-wider">
                        {lab.desc}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-red-500 opacity-0 group-hover:opacity-100 translate-x-[-10px] group-hover:translate-x-0 transition-all">
                      Initialiser le protocole <ArrowRight className="w-3 h-3" />
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>

        {/* Info Box */}
        <div className="mt-24 p-12 rounded-[3rem] bg-gradient-to-br from-red-500/20 to-transparent border border-red-500/20 flex flex-col md:flex-row items-center gap-8">
            <div className="p-6 bg-red-500 rounded-3xl shadow-[0_0_30px_rgba(239,68,68,0.5)]">
                <ShieldAlert className="w-12 h-12 text-white" />
            </div>
            <div className="text-center md:text-left">
                <h4 className="text-2xl font-black italic manga-font uppercase mb-2">Avertissement de Sécurité</h4>
                <p className="text-sm font-bold opacity-50 uppercase leading-relaxed tracking-wide max-w-3xl">
                    Les modules de laboratoire utilisent des clusters de calcul H100 à haute intensité. Toute utilisation abusive ou tentative d'injection de prompt sera automatiquement tracée par le <b>Guardrail v4.2</b>.
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default LabHubPage;
