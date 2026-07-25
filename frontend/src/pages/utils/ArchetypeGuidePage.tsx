import React from 'react';
import {
  Brain,
  Network,
  Cpu,
  Layers,
  Fingerprint,
  Scale,
  Activity,
  Search,
  Database,
  CheckCircle2,
  ArrowLeft,
  Sparkles,
  Gamepad2,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const ArchetypeGuidePage: React.FC = () => {
  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8] overflow-hidden">
        {/* Hero Section */}
        <section className="relative pt-32 pb-24 px-6 text-center border-b border-[#F4F1E8]/10">
          <div
            className="explore-halftone pointer-events-none absolute inset-x-0 top-0 h-72"
            aria-hidden
          />
          <div className="max-w-4xl mx-auto relative z-10">
            <Link
              to="/explore/"
              className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] hover:text-[#F4F1E8] transition-colors mb-12 no-underline group"
            >
              <ArrowLeft className="w-3 h-3 group-hover:-translate-x-1 transition-transform" />{' '}
              Retour au Nexus
            </Link>

            <div className="inline-flex items-center gap-3 px-3 py-1.5 rounded-full border border-[#E8442B]/25 bg-[#E8442B]/10 text-[#E8442B] text-[10px] font-black uppercase tracking-[0.3em] mb-10">
              <Brain className="w-4 h-4" /> Guide Scientifique du Nexus
            </div>

            <div className="mb-8 flex items-center justify-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                型
              </span>
            </div>
            <h1 className="text-6xl md:text-8xl font-black italic font-manga tracking-tighter uppercase mb-8 leading-none">
              L'INTELLIGENCE <br />
              <span className="text-[#E8442B]">NEURO-SYMBOLIQUE</span>
            </h1>

            <p className="text-lg md:text-xl text-[#8F94A5] font-bold uppercase tracking-widest leading-relaxed max-w-3xl mx-auto italic">
              Découvrez la technologie qui permet à Animetix de comprendre vos goûts, de résoudre
              des paradoxes et de fusionner des univers.
            </p>
          </div>
        </section>

        <main className="max-w-6xl mx-auto px-6 py-24 space-y-40">
          {/* The Core Concept */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
            <div className="space-y-8">
              <h2 className="text-4xl font-black italic uppercase font-manga tracking-tight flex items-center gap-4">
                <Layers className="w-10 h-10 text-[#E8442B]" /> Le Cycle Cognitif
              </h2>
              <p className="text-lg text-[#8F94A5] leading-relaxed font-medium italic">
                Contrairement aux IA classiques qui se contentent de prédire le mot suivant,
                Animetix utilise un
                <span className="text-[#F4F1E8]"> cycle cognitif en 6 phases</span>. C'est
                l'alliance entre la force brute du Deep Learning et la rigueur de la logique
                mathématique.
              </p>
              <div className="space-y-4">
                <StepItem
                  index="01"
                  title="Ingestion Multimodale"
                  desc="Scraping temps réel des métadonnées (MAL, IGDB, TV Tropes)."
                />
                <StepItem
                  index="02"
                  title="Stockage Hybride"
                  desc="Combinaison SQL, Graphes Neo4j et Bases Vectorielles."
                />
                <StepItem
                  index="03"
                  title="RAG Augmenté"
                  desc="Recherche sémantique via Jina-v3 et Matryoshka Embeddings."
                />
              </div>
            </div>
            <div className="relative">
              <div className="relative rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 sm:p-12">
                <div className="grid grid-cols-2 gap-8">
                  <div className="p-6 rounded-2xl bg-[#0B0C10] border border-[#F4F1E8]/10 text-center">
                    <Cpu className="w-12 h-12 text-[#FDB913] mx-auto mb-4" />
                    <h4 className="text-xs font-black uppercase tracking-widest">Neural</h4>
                    <p className="text-[10px] text-[#8F94A5] mt-2">Intuition & Créativité</p>
                  </div>
                  <div className="p-6 rounded-2xl bg-[#0B0C10] border border-[#F4F1E8]/10 text-center">
                    <Scale className="w-12 h-12 text-[#5D7FD3] mx-auto mb-4" />
                    <h4 className="text-xs font-black uppercase tracking-widest">Symbolic</h4>
                    <p className="text-[10px] text-[#8F94A5] mt-2">Logique & Preuve</p>
                  </div>
                  <div className="col-span-2 p-8 rounded-2xl border border-[#E8442B]/25 bg-[#E8442B]/[0.06] text-center">
                    <h4 className="text-xl font-black italic uppercase tracking-widest mb-2 font-manga">
                      NEURO-SYMBOLIQUE
                    </h4>
                    <p className="text-xs font-bold text-[#8F94A5] uppercase">
                      La fusion parfaite pour l'Analyse Otaku
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Logical Profiling */}
          <section className="text-center space-y-16">
            <div className="max-w-3xl mx-auto space-y-6">
              <h2 className="text-5xl md:text-6xl font-black italic uppercase font-manga tracking-tighter">
                PROFILAGE <span className="text-[#E8442B]">LOGIQUE</span>
              </h2>
              <p className="text-[#8F94A5] font-bold uppercase tracking-widest leading-relaxed">
                Animetix ne se contente pas de vous recommander des titres similaires. Il
                déconstruit vos interactions pour extraire des "engrammes" cognitifs.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 sm:p-10 hover:border-[#E8442B]/40 transition-colors group">
                <Fingerprint className="w-12 h-12 text-[#E8442B] mb-8 group-hover:scale-110 transition-transform" />
                <h3 className="text-2xl font-black italic uppercase mb-4 tracking-tight font-manga">
                  Archétype Nexus
                </h3>
                <p className="text-sm text-[#8F94A5] leading-relaxed font-medium italic">
                  Analyse de votre comportement de jeu (Akinetix, Paradox) pour définir votre
                  "empreinte" de fan (ex: Analytique Shonen, Explorateur Seinen).
                </p>
              </div>
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 sm:p-10 hover:border-[#FDB913]/40 transition-colors group">
                <Activity className="w-12 h-12 text-[#FDB913] mb-8 group-hover:scale-110 transition-transform" />
                <h3 className="text-2xl font-black italic uppercase mb-4 tracking-tight font-manga">
                  Drift Sémantique
                </h3>
                <p className="text-sm text-[#8F94A5] leading-relaxed font-medium italic">
                  Notre système détecte en temps réel si vos goûts évoluent ou si vous explorez de
                  nouvelles frontières narratives (KS-Test).
                </p>
              </div>
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 sm:p-10 hover:border-[#5D7FD3]/40 transition-colors group">
                <Network className="w-12 h-12 text-[#5D7FD3] mb-8 group-hover:scale-110 transition-transform" />
                <h3 className="text-2xl font-black italic uppercase mb-4 tracking-tight font-manga">
                  Graphe de Soi
                </h3>
                <p className="text-sm text-[#8F94A5] leading-relaxed font-medium italic">
                  Chaque préférence crée un nœud dans votre graphe personnel, relié aux studios,
                  auteurs et thèmes que vous chérissez.
                </p>
              </div>
            </div>
          </section>

          {/* Interactive Engines */}
          <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-10 sm:p-16 relative overflow-hidden">
            <span
              className="font-manga pointer-events-none absolute -bottom-16 -right-6 text-[13rem] font-black italic leading-none text-[#E8442B]/[0.05]"
              aria-hidden
            >
              型
            </span>

            <h2 className="text-4xl font-black italic uppercase font-manga tracking-tight mb-16 flex items-center gap-4 relative z-10">
              <Gamepad2 className="w-10 h-10 text-[#FDB913]" /> Les Moteurs d'Expérience
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 relative z-10">
              <div className="space-y-8">
                <div className="flex gap-6">
                  <div className="w-16 h-16 rounded-2xl bg-[#FDB913]/10 flex items-center justify-center text-[#FDB913] flex-shrink-0">
                    <Search className="w-8 h-8" />
                  </div>
                  <div>
                    <h4 className="text-xl font-black italic uppercase tracking-widest mb-2 font-manga">
                      Akinetix (RL PPO)
                    </h4>
                    <p className="text-sm text-[#8F94A5] leading-relaxed italic">
                      Utilise l'apprentissage par renforcement pour minimiser l'entropie et deviner
                      vos personnages en un minimum de coups.
                    </p>
                  </div>
                </div>
                <div className="flex gap-6">
                  <div className="w-16 h-16 rounded-2xl bg-[#5D7FD3]/10 flex items-center justify-center text-[#5D7FD3] flex-shrink-0">
                    <CheckCircle2 className="w-8 h-8" />
                  </div>
                  <div>
                    <h4 className="text-xl font-black italic uppercase tracking-widest mb-2 font-manga">
                      Paradox Quest (Z3 Solver)
                    </h4>
                    <p className="text-sm text-[#8F94A5] leading-relaxed italic">
                      Prouve mathématiquement l'existence d'un "intrus" thématique en compilant des
                      prédicats logiques résolus par le solveur Z3 de Microsoft Research.
                    </p>
                  </div>
                </div>
                <div className="flex gap-6">
                  <div className="w-16 h-16 rounded-2xl bg-[#E8442B]/10 flex items-center justify-center text-[#E8442B] flex-shrink-0">
                    <Sparkles className="w-8 h-8" />
                  </div>
                  <div>
                    <h4 className="text-xl font-black italic uppercase tracking-widest mb-2 font-manga">
                      La Forge (Stable Diffusion XL)
                    </h4>
                    <p className="text-sm text-[#8F94A5] leading-relaxed italic">
                      Génération d'images et clonage de voix (XTTS-v2) pour matérialiser vos fusions
                      créatives les plus folles.
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl p-8 sm:p-10 border border-[#F4F1E8]/10 bg-[#0B0C10] flex flex-col justify-center text-center space-y-6">
                <h3 className="text-2xl font-black italic uppercase tracking-tighter text-[#E8442B] font-manga">
                  Prêt pour l'immersion ?
                </h3>
                <p className="text-xs font-bold uppercase tracking-widest text-[#8F94A5] mb-8 leading-loose">
                  Votre voyage dans le Nexus ne fait que commencer. Chaque action alimente la boucle
                  de feedback DPO pour rendre l'IA plus experte.
                </p>
                <div className="flex flex-col gap-4">
                  <Link
                    to="/explore/"
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-6 py-4 font-manga text-sm font-black uppercase italic text-[#F4F1E8] no-underline transition-colors hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                  >
                    COMMENCER L'EXPLORATION
                  </Link>
                  <Link
                    to="/social/transparency/"
                    className="inline-flex items-center justify-center rounded-xl border border-[#F4F1E8]/15 px-6 py-3 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]"
                  >
                    CONSULTER L'AUDIT ÉTHIQUE
                  </Link>
                </div>
              </div>
            </div>
          </section>
        </main>

        {/* Technical Footer */}
        <footer className="py-24 border-t border-[#F4F1E8]/10">
          <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-12 text-[#8F94A5]/50">
            <div className="flex items-center gap-4">
              <Database className="w-6 h-6" />
              <span className="text-[10px] font-black uppercase tracking-widest">
                Neural-Symbolic Architecture v2.4
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="rounded-full border border-[#F4F1E8]/10 bg-[#0F1016] px-4 py-2 text-[10px] font-black uppercase tracking-widest">
                CORE: DEEPSEEK-R1 + Z3 SOLVER
              </span>
            </div>
          </div>
        </footer>
      </div>
    </AnimatedPage>
  );
};

const StepItem = ({ index, title, desc }: { index: string; title: string; desc: string }) => (
  <div className="flex items-start gap-6 group">
    <span className="text-4xl font-black italic font-manga text-[#F4F1E8]/10 group-hover:text-[#E8442B]/30 transition-colors">
      {index}
    </span>
    <div>
      <h4 className="text-sm font-black italic uppercase tracking-widest mb-1 group-hover:text-[#F4F1E8] transition-colors">
        {title}
      </h4>
      <p className="text-xs text-[#8F94A5] font-bold uppercase tracking-tight leading-relaxed">
        {desc}
      </p>
    </div>
  </div>
);

export default ArchetypeGuidePage;
