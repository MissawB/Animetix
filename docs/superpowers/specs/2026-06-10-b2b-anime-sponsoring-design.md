# Design Specification - B2B Anime Sponsoring (Direct Partnerships)

**Date:** 2026-06-10
**Status:** Approved

## 1. Goal Description
To replace the fictional ads in `SimulatedAdBanner.tsx` with real B2B Anime partners (Crunchyroll, ADN, and Crunchyroll Store). These ads will render high-fidelity, generated visual banners and redirect users to partner services in new tabs.

## 2. Technical Design

### A. Sponsor Data & Assets
We will generate three premium banner illustrations (400x150 px) and save them to `frontend/public/img/sponsors/`:
1. **Crunchyroll Banner:** `crunchyroll_ad.png` (Orange cyber anime theme).
2. **ADN Banner:** `adn_ad.png` (Blue neon anime streaming theme).
3. **Store Banner:** `manga_store_ad.png` (Purple/cyan merchandise theme).

The sponsor array will map each partner:
* **Crunchyroll:** 
  * Slogan: "Le meilleur de l'anime en HD. Essai gratuit de 14 jours !"
  * CTA: "Regarder sur Crunchyroll"
  * URL: `https://www.crunchyroll.com`
* **ADN:** 
  * Slogan: "Découvrez ADN, la plateforme de streaming 100% anime VF/VOSTFR."
  * CTA: "Explorer le Catalogue"
  * URL: `https://animationdigitalnetwork.fr`
* **Crunchyroll Store:** 
  * Slogan: "Figurines de collection et produits officiels de vos séries favoris !"
  * CTA: "Visiter la Boutique"
  * URL: `https://store.crunchyroll.com`

### B. Component Changes: `SimulatedAdBanner.tsx`
- **Visual Rendering:** Change layout to display the partner image banner above the text slogan.
- **Link Behavior:** Clicking the CTA or the banner image will open the external sponsor link using `window.open(sponsor.url, '_blank', 'noopener,noreferrer')`.
- **Styling:** Retain the cyber-manga border and relative layout, adjusting sizes for visual balance.

## 3. Test Verification
- Ensure that unit tests in `PricingPage.test.tsx` continue to mount and run successfully.
- Verify image assets exist and render without loading errors.
