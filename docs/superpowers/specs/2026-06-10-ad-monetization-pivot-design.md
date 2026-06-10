# Spécification de Design : Pivot vers la Monétisation par Publicité (Ad Service)

**Date :** 2026-06-10  
**Statut :** En cours de validation  
**Sujet :** Suppression de la notion d'abonnement payant et mise en place d'un service de sponsoring et de publicités immersives.

---

## 1. Objectifs
- Supprimer toute référence à des formules d'abonnement payantes (prix en €, cycles de facturation mensuels/annuels) pour les utilisateurs finaux.
- Transformer la page de tarifs `/pricing/` en un **Centre de Sponsoring & Boost**.
- Permettre aux utilisateurs de débloquer le statut **Boosté (Premium)** pendant 24h ou de **Recharger leur quota IA** immédiatement en regardant une publicité vidéo simulée de quelques secondes.
- Intégrer des bannières publicitaires simulées de style cyberpunk/anime (ex: *Capsule Corp*, *Nerv*) pour les utilisateurs en statut Standard, qui disparaissent en statut Boosté.

---

## 2. Architecture Backend & API

### 2.1 Nouveau Point d'Accès de Recharge de Quota
Dans le contrôleur de profils `ProfileViewSet` (`backend/api/animetix/api/social.py`), nous ajoutons une action `refill_quota` :
- **Route :** `POST /api/social/profile/refill_quota/`
- **Comportement :** Supprime toutes les entrées du modèle `AITokenUsage` associées à l'utilisateur connecté pour la date du jour (`created_at__date = today`). Cela réinitialise le compteur quotidien à 0, rechargeant de fait son quota.

### 2.2 Préservation des Tiers en Base de Données
Pour conserver la compatibilité avec le code existant, les tests unitaires et la structure de données Django, les rôles techniques suivants restent inchangés :
- `'free'` : Utilisateur **Standard** (soumis aux pubs et limites).
- `'premium'` : Utilisateur **Boosté** (sans pub, quota étendu, accès graph sémantique).
- `'pro'` : Utilisateur **Expert API** (accès direct via clé API générée dans les paramètres).

---

## 3. Architecture Frontend & Composants React

### 3.1 Bannières Publicitaires : `SimulatedAdBanner.tsx`
- **Rôle :** Affiche une bannière publicitaire humoristique cyberpunk tirée au sort.
- **Sponsors intégrés :** *Capsule Corp*, *NERV*, *Future Gadget Lab*, *Ichiraku Ramen*, *Death Note Shop*, *Arasaka Corporation*.
- **Style :** Bordure néon avec animation clignotante, badge `"PUBLICITÉ SPONSORISÉE"`.
- **Intégration :** Positionné en bas de la barre de navigation latérale (`Layout.tsx`) pour les utilisateurs ayant `user.tier === 'free'`.

### 3.2 Centre de Sponsoring & Boost : `PricingPage.tsx`
- **Rôle :** Page de gestion des boosts publicitaires (route `/pricing/`).
- **Éléments affichés :**
  - Statut actuel de l'utilisateur (Standard ou Boosté) et indicateur visuel de quota.
  - Deux blocs de comparaison des fonctionnalités (Standard vs Boosté).
  - Deux boutons d'action :
    1. **Activer le Boost 24H** (lance le lecteur de sponsor pendant 7s, puis passe le profil en tier `premium`).
    2. **Recharger mon Quota** (lance le lecteur de sponsor pendant 4s, puis appelle `POST /api/social/profile/refill_quota/`).

### 3.3 Lecteur de Flux Sponsorisé : `SponsorStreamModal.tsx`
- **Rôle :** Remplace l'ancienne modale de transaction `NexusGatewayModal.tsx`.
- **Visuel :** Écran de chargement cyberpunk rétro-futuriste avec indicateur de progression `0% -> 100%`.
- **Cinématique :** Le bouton de validation `"Réclamer le Boost"` ou `"Valider la Recharge"` est désactivé pendant la lecture de l'annonce et ne s'active qu'une fois le compte à rebours terminé.

---

## 4. Esthétique & Design System
- Les publicités utiliseront la palette néon du projet (bleu cyan, vert émeraude, rose magenta) avec des bordures `border-dashed` clignotantes.
- Pas de placeholders : utilisation d'icônes `lucide-react` animées de manière fluide (`framer-motion`).

---

## 5. Critères d'Acceptation
- [ ] La page `/pricing/` n'affiche plus aucun prix en euros (€) ni aucune mention de cycle de facturation ou d'abonnement.
- [ ] Cliquer sur "Activer le Boost" ou "Recharger le quota" ouvre le `SponsorStreamModal` avec le compte à rebours simulé.
- [ ] La validation met bien à jour le profil de l'utilisateur (le statut passe en "Boosté" pour l'activation, ou le quota est réinitialisé pour la recharge).
- [ ] Les bannières publicitaires simulées apparaissent bien pour les utilisateurs Standard dans la sidebar et disparaissent en statut Boosté.
- [ ] Tous les tests du frontend et du backend continuent de compiler et de passer.
