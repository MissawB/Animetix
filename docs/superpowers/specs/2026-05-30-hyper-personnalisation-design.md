# Design Spec: Hyper-Personnalisation Graphique (Visual Meta)

**Date :** 2026-05-30
**Statut :** En attente de revue
**Approche :** Visual Meta (Backend-driven)

## 1. Objectif
Implémenter une personnalisation dynamique et immersive de l'interface utilisateur d'Animetix, basée sur l'évolution psychologique et les affinités de l'utilisateur ("Archetype Drift"). L'interface doit refléter l'ambiance des contenus consommés via des éléments graphiques dynamiques (auras, accents, animations).

## 2. Architecture Technique

### 2.1 Backend (Core Domain)
Un nouveau service `ArchetypeDriftService` sera responsable du calcul de l'état visuel.

- **Entrées (Signaux) :**
    - `AIFeedback` : Feedbacks explicites (pouces levés/baissés).
    - `GameplaySession` : Historique des thèmes et médias consultés.
    - `LongTermMemoryService` : Contextes sémantiques résumés.
- **Logique de calcul (Inertie Modérée) :**
    - Utilisation d'une Moyenne Mobile Exponentielle (EMA) pour lisser les changements.
    - `DriftScore = (CurrentSignal * alpha) + (PreviousScore * (1 - alpha))` où `alpha ≈ 0.3`.
- **Mapping Archétypes -> Visuel :**
    - Dictionnaire statique mappant les concepts (ex: `Tsundere`, `Shonen`, `Cyberpunk`) vers des variables CSS et des types d'effets.

### 2.2 API & Middleware
- Un Middleware Django intercepte les réponses sortantes.
- Si l'utilisateur est authentifié, il appelle le service de personnalisation.
- Injecte un objet `meta.visual_config` dans la réponse JSON.

### 2.3 Frontend (React)
- **Store Zustand (`personalizationStore`) :**
    - Persiste l'état visuel actuel.
    - Met à jour les variables CSS root (`:root`) dynamiquement.
- **Système d'Aura (`DynamicAuraWrapper`) :**
    - Composant React utilisant `Framer Motion`.
    - Affiche des effets visuels (lueurs, particules, distorsions) autour des éléments clés (avatars, cartes, boutons).

## 3. Schéma de Données (VisualConfig)

```typescript
interface VisualConfig {
  archetype_id: string;      // ex: "nekketsu_hero"
  primary_accent: string;    // ex: "#FF4500"
  aura_type: "none" | "fire" | "electric" | "shadow" | "sparkles";
  aura_intensity: number;    // 0.0 to 1.0
  font_vibe: "default" | "manga" | "brush";
}
```

## 4. Plan de Tests
- **Backend :** Test unitaire sur `ArchetypeDriftService` pour vérifier la stabilité du score face à des signaux contradictoires.
- **Frontend :** Vérifier que les variables CSS sont correctement injectées dans le DOM.
- **E2E :** Simuler une série d'actions "Shonen" et vérifier l'apparition de l'accent orange et de l'aura associée.

## 5. Contraintes & Sécurité
- **Performance :** Le calcul de drift doit être ultra-rapide (< 10ms) ou mis en cache.
- **Accessibilité :** Les couleurs générées dynamiquement doivent conserver un contraste suffisant (WCAG). Un mode "Safe/Static" doit être disponible.
