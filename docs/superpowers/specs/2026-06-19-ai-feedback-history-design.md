# Conception - Historique des Feedbacks IA (ai-feedback-history)

Date : 2026-06-19
Auteur : Antigravity AI

## 1. Contexte & Problématique

Les utilisateurs d'Animetix soumettent des retours (feedbacks positifs/négatifs) sur les réponses de l'IA (comme les scénarios de fusion ou les prédictions). 
Il existe déjà une page pour visualiser cet historique (`AIFeedbackHistoryPage.tsx`) et une route `/social/ai-feedback-history/`, mais :
- Elle n'est accessible via aucun lien de l'application (Sidebar ou paramètres).
- Le bouton de retour de la page pointe vers `/settings` qui n'existe pas (le bon chemin étant `/auth/settings/`).

## 2. Objectifs

1. Rendre la page d'historique découvrable en ajoutant des liens dans la Sidebar et la page de gestion du compte.
2. Corriger le lien de retour sur la page d'historique des feedbacks.

## 3. Changements Proposés

### Navigation & Expositions (Frontend)

1. **Sidebar (`Layout.tsx`)** :
   - Importer `MessageSquare` de `lucide-react`.
   - Ajouter une entrée pour l'historique sous la section "Communauté" pour les utilisateurs authentifiés.

2. **Paramètres (`AccountSettingsPage.tsx`)** :
   - Ajouter un bouton pour naviguer vers `/social/ai-feedback-history/` sous la section "Historique IA" (Quotas & Consommation).

3. **Page Historique (`AIFeedbackHistoryPage.tsx`)** :
   - Modifier le lien de retour (`ChevronLeft`) pour pointer vers `/auth/settings/`.

## 4. Plan de Validation

### Vérification Manuelle
- Vérifier que la compilation TypeScript se passe bien.
- S'assurer que les liens s'affichent correctement et redirigent vers le bon chemin.
