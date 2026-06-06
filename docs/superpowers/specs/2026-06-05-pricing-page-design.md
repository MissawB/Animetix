# Design Spec: Page "Plans & Tarifs" et Nexus Gateway

**Date :** 2026-06-05
**Sujet :** Création de la page `/pricing/` et d'un flux de souscription immersif.

## 1. Objectifs
- Fournir une interface de comparaison claire entre les tiers (Explorateur, Premium, Expert API).
- Implémenter le flux "Nexus Gateway" : une simulation de transaction sécurisée via modale.
- Renforcer l'identité visuelle "Manga/Futuriste" du projet.

## 2. Architecture Frontend (React)

### 2.1 Nouvelle Page : `PricingPage.tsx`
- **Route :** `/pricing/`
- **Composants :**
    - **PricingHeader** : Titre d'impact avec typographie "Manga-font" et effets de lueur.
    - **PricingGrid** : Layout en 3 colonnes pour les cartes de tarifs.
    - **TierCard** : Composant réutilisable pour chaque offre, incluant la liste des fonctionnalités et le bouton d'action.
- **Logique :** Utiliser `useAuthStore` pour identifier le tier actuel de l'utilisateur et adapter l'UI (ex: marquer le plan actuel comme "ACTIF").

### 2.2 Composant : `NexusGatewayModal.tsx`
- **Description :** Une modale plein écran ou centrée avec un fond semi-transparent et des bordures néon.
- **Etapes du flux :**
    1. **Récapitulatif** : Affiche l'offre choisie et le prix (ex: 9.99€/mois).
    2. **Processing** : Animation de chargement typée "Cyber-système" (ex: "Cryptage de la transaction...", "Validation Nexus...").
    3. **Success** : Message de félicitations avec un effet visuel (confettis néon ou aura de puissance).
- **Intégration API :** Appeler `PATCH /api/social/update_settings/` avec le nouveau `tier`.

## 3. Architecture Backend
- Pas de changement structurel requis : l'API `update_settings` dans `SocialViewSet` gère déjà la mise à jour du tier.
- (Optionnel) Ajouter un log dans `AISafetyEvent` ou un nouveau modèle `UserTransaction` pour tracer ces simulations.

## 4. Design & Esthétique
- **Explorateur** : Sobre, bordures grises, opacité réduite.
- **Premium** : Accent bleu vibrant (`#3b82f6`), ombre portée (glow), badge "RECOMMANDÉ".
- **Expert API** : Accent blanc/rouge, minimaliste, boutons typés "Terminal".

## 5. Critères d'Acceptation
- [ ] La route `/pricing/` est accessible et responsive.
- [ ] Les cartes de tarifs affichent les bonnes fonctionnalités par tier.
- [ ] Le clic sur "Sélectionner" ouvre la "Nexus Gateway".
- [ ] La simulation de transaction dure 2-3 secondes avec des animations cohérentes.
- [ ] Une fois terminé, le profil de l'utilisateur est mis à jour et l'interface (Navbar, Profile) reflète le nouveau statut.
