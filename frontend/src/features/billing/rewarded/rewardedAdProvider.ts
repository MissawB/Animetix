/**
 * Fournisseur de pub RÉCOMPENSÉE (rewarded) — abstrait et AGNOSTIQUE au réseau.
 *
 * Règle AdSense absolue : une pub AdSense (`AdSlot`) n'est JAMAIS le déclencheur
 * d'une récompense. La récompense Bx doit être financée par un réseau REWARDED
 * dédié (Google Ad Manager rewarded units, ou un SSP tiers), strictement séparé
 * d'AdSense (qui reste du display passif).
 *
 * Cette couche permet de brancher ce réseau plus tard sans toucher au reste :
 *   1. `showRewarded()` charge + montre une pub rewarded,
 *   2. on attend le callback « reward » du réseau (pub réellement visionnée),
 *      qui fournit un JETON SIGNÉ,
 *   3. on transmet ce jeton au backend qui le VÉRIFIE (SSV) avant de créditer.
 *
 * Tant qu'aucun réseau n'est configuré, un stub dev (minuteur d'engagement,
 * AUCUNE vraie pub) est utilisé — clairement marqué. Le backend n'accepte le
 * crédit SANS jeton qu'en mode stub (cf. rewarded_ad_verifier.py).
 */

export interface RewardedAdResult {
  /** true si le réseau a émis l'événement « reward » (ou stub terminé). */
  rewarded: boolean;
  /** Jeton signé fourni par le réseau, à vérifier côté serveur (SSV). null en stub. */
  rewardToken: string | null;
  /** Réseau ayant servi la pub (audit + choix du vérificateur serveur). */
  provider: string;
}

export interface RewardedAdProvider {
  readonly name: string;
  /** Le réseau est-il réellement configuré (IDs présents) ? Sinon → stub. */
  isConfigured(): boolean;
  /**
   * Charge puis montre une pub rewarded. Résout quand l'utilisateur a « mérité »
   * la récompense, ou `{ rewarded: false }` s'il a fermé la pub avant la fin.
   * @param onProgress progression 0..100 (utilisé par l'UI, surtout pour le stub).
   */
  showRewarded(onProgress?: (pct: number) => void): Promise<RewardedAdResult>;
}

/* ------------------------------------------------------------------ */
/* Stub dev : minuteur d'engagement — AUCUNE vraie pub n'est jouée.    */
/* ------------------------------------------------------------------ */
const STUB_DURATION_MS = 15000;
const STUB_TICK_MS = 100;

const stubRewardedAdProvider: RewardedAdProvider = {
  name: 'stub',
  isConfigured: () => false,
  showRewarded: (onProgress) =>
    new Promise<RewardedAdResult>((resolve) => {
      const steps = STUB_DURATION_MS / STUB_TICK_MS;
      let step = 0;
      const timer = setInterval(() => {
        step += 1;
        onProgress?.((step / steps) * 100);
        if (step >= steps) {
          clearInterval(timer);
          // Pas de vraie pub → pas de jeton signé. Le backend ne crédite ça
          // qu'en mode stub (REWARDED_ADS_PROVIDER absent/"stub").
          resolve({ rewarded: true, rewardToken: null, provider: 'stub' });
        }
      }, STUB_TICK_MS);
    }),
};

/* ------------------------------------------------------------------ */
/* Emplacement du VRAI réseau (à implémenter avec un compte + IDs).    */
/* ------------------------------------------------------------------ */
// TODO(option A) : quand un compte rewarded existe, ajouter ici un provider
// (ex. Google Ad Manager via googletag rewarded, ou SSP tiers). Il doit :
//   - `isConfigured()` = présence des IDs (import.meta.env.VITE_REWARDED_*),
//   - `showRewarded()` = charger le SDK, afficher la pub rewarded, attendre
//     l'event « reward » et renvoyer le jeton signé du réseau,
//   - ne JAMAIS réutiliser un `AdSlot` AdSense.
// Puis l'exposer dans getRewardedAdProvider() selon VITE_REWARDED_PROVIDER.

/**
 * Sélectionne le fournisseur selon `VITE_REWARDED_PROVIDER`. Par défaut (absent
 * ou « stub »), renvoie le stub d'engagement. Les vrais réseaux ne sont actifs
 * que lorsqu'ils sont implémentés ET configurés.
 */
export function getRewardedAdProvider(): RewardedAdProvider {
  const configured = (import.meta.env.VITE_REWARDED_PROVIDER as string | undefined)?.toLowerCase();
  switch (configured) {
    // case 'gam':
    //   return gamRewardedAdProvider.isConfigured() ? gamRewardedAdProvider : stubRewardedAdProvider;
    default:
      return stubRewardedAdProvider;
  }
}
