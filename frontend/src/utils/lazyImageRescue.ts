/**
 * Secours pour le lazy-loading natif dans une SPA animée.
 *
 * Les transitions de route (framer-motion) rendent chaque page à `opacity: 0`
 * avec un `transform` avant de l'animer. Les `<img loading="lazy">` peintes
 * pendant cet état voient leur chargement différé par le navigateur, et comme
 * l'animation opacité/transform ne passe que par le compositeur (aucun
 * scroll/reflow), la heuristique native n'est jamais ré-évaluée : l'image ne
 * s'affiche qu'après un repaint (le fameux « il faut passer la souris dessus »).
 *
 * On installe notre propre IntersectionObserver — purement géométrique, donc
 * insensible à l'opacité de l'ancêtre — qui force le chargement des images
 * réellement en vue. Un MutationObserver couvre celles rendues après coup
 * (résultats de recherche, catalogue chargé en asynchrone…).
 *
 * Retourne une fonction de nettoyage.
 */
export function installLazyImageRescue(): () => void {
  if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
    return () => {};
  }

  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const img = entry.target as HTMLImageElement;
        io.unobserve(img);
        // naturalWidth === 0 → pas encore chargée. Passer en `eager` déclenche
        // le chargement différé sans le redémarrer si elle est déjà en cours.
        if (img.naturalWidth === 0) {
          img.loading = 'eager';
        }
      }
    },
    // Charge un peu avant l'entrée dans le viewport, comme le lazy natif.
    { rootMargin: '300px' },
  );

  const observe = (img: Element) => {
    if (img instanceof HTMLImageElement && img.naturalWidth === 0) {
      io.observe(img);
    }
  };

  document
    .querySelectorAll('img[loading="lazy"]')
    .forEach(observe);

  const mo = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType !== 1) return;
        const el = node as Element;
        if (el.matches?.('img[loading="lazy"]')) observe(el);
        el.querySelectorAll?.('img[loading="lazy"]').forEach(observe);
      });
    }
  });
  mo.observe(document.body, { childList: true, subtree: true });

  return () => {
    io.disconnect();
    mo.disconnect();
  };
}
