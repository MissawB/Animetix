import React from 'react';
import { Compass, Radar } from 'lucide-react';

/** Deux repères en clair sous la carte : comment la lire, et d'où elle vient. */
export const MapGuide: React.FC = () => (
  <div className="mt-20 grid grid-cols-1 gap-6 md:grid-cols-2">
    <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8">
      <h3 className="font-manga mb-5 flex items-center gap-3 text-lg font-black uppercase italic text-[#F4F1E8]">
        <Compass className="h-5 w-5 text-[#FDB913]" aria-hidden="true" /> Comment lire la carte
      </h3>
      <div className="space-y-4 text-sm leading-relaxed text-[#8F94A5]">
        <p>
          <span className="font-bold text-[#F4F1E8]">Les territoires.</span> Chaque masse regroupe
          des œuvres qui se ressemblent. Plus un territoire contient d&apos;œuvres, plus il est
          grand.
        </p>
        <p>
          <span className="font-bold text-[#F4F1E8]">Les points.</span> Ce sont les œuvres du
          territoire. On ne trace aucun trait entre elles : la carte montre les regroupements, elle
          n&apos;invente pas de liens.
        </p>
        <p>
          <span className="font-bold text-[#F4F1E8]">La lecture.</span> Cliquez un territoire (ou
          tabulez jusqu&apos;à lui) pour ouvrir son dossier : un résumé et ses œuvres clés.
        </p>
      </div>
    </section>

    <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8">
      <h3 className="font-manga mb-5 flex items-center gap-3 text-lg font-black uppercase italic text-[#F4F1E8]">
        <Radar className="h-5 w-5 text-[#FDB913]" aria-hidden="true" /> D&apos;où vient cette carte
      </h3>
      <div className="space-y-4 text-sm leading-relaxed text-[#8F94A5]">
        <p>
          <span className="font-bold text-[#F4F1E8]">Le regroupement.</span> Les œuvres sont
          rassemblées non par titre, mais par ce qu&apos;elles ont en commun : thèmes, auteurs,
          studios, inspirations (méthode dite « Leiden »).
        </p>
        <p>
          <span className="font-bold text-[#F4F1E8]">La fabrication.</span> La carte est préparée à
          l&apos;avance, la nuit. Elle n&apos;est jamais calculée pendant votre visite — résumer
          chaque territoire coûte un appel à l&apos;IA.
        </p>
        <p>
          <span className="font-bold text-[#F4F1E8]">À quoi ça sert.</span> Ces regroupements aident
          l&apos;IA à saisir le contexte d&apos;une saga entière avant d&apos;affiner une recherche.
        </p>
      </div>
    </section>
  </div>
);
