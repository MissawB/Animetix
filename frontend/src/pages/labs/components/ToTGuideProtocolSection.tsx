import React from 'react';
import { LabGuide } from './shared/LabKit';

export const ToTGuideProtocolSection: React.FC = () => {
  return (
    <div className="mx-auto max-w-7xl px-4 pb-16 sm:px-6">
      <LabGuide
        steps={[
          {
            title: 'Pose une question',
            body: "Formule un problème complexe : l'IA ne répond pas d'un seul jet, elle explore plusieurs pistes de réflexion en parallèle avant de conclure.",
          },
          {
            title: "Lis l'arbre",
            body: "Chaque point est une idée notée par l'IA : or pour une piste retenue, graphite pour une branche abandonnée, vermillon pour la conclusion. Clique sur un nœud pour lire sa trace de pensée.",
          },
          {
            title: 'Choisis ton mode',
            body: "« Générer l'arbre » renvoie l'arbre complet d'un coup ; « Suivre en direct » affiche les nœuds au fur et à mesure (connexion requise, consomme des Berrix).",
          },
        ]}
        note="Recherche arborescente type Tree-of-Thoughts : le modèle génère des pensées candidates, les évalue par un score de confiance et élague les branches faibles, comme dans une exploration MCTS. Le mode direct diffuse chaque nœud via un flux SSE, rendu en temps réel dans un graphe force-directed."
      />
    </div>
  );
};
