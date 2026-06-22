// eslint-disable-next-line no-undef
module.exports = {
  'src/**/*.{ts,tsx}': [
    // Format first, then let ESLint fix what's left (eslint-config-prettier keeps
    // the two from fighting over style).
    'prettier --write',
    'eslint --fix',
    // On lance un check de type complet pour garantir l'intégrité globale
    () => 'npm run check-types',
  ],
  'src/**/*.{css,json}': ['prettier --write'],
};
