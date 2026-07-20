/**
 * Normalise une chaîne pour la comparaison de réponses de jeu : retire les
 * diacritiques (é → e) et passe en minuscules, de sorte que « Sébastien » et
 * « sebastien » matchent. Utilisé par les jeux de devinette (Classic, Covertest,
 * Blindtest, VS Battle) — factorisé depuis 4 copies identiques.
 *
 * NB : ne fait PAS de `.trim()` (le filtre Explorer a son propre normaliseur
 * avec trim, cf. pages/explore/hooks/useExploreFilter.ts).
 */
export const normalizeText = (s: string): string =>
  s
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase();
