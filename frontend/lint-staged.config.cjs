module.exports = {
  'src/**/*.{ts,tsx}': [
    'eslint --fix',
    // On lance un check de type complet pour garantir l'intégrité globale
    () => 'npm run check-types',
  ],
};
