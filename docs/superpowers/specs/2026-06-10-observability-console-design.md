# Spécification de la Console d'Observabilité & Guardrails (Dynamique)

## Objectif
Développer une console d'observabilité permettant le monitoring des dérives d'archétypes et des violations de guardrails, tout en offrant un contrôle dynamique pour ajuster les seuils de sécurité de l'IA.

## Architecture UI
L'interface sera structurée en trois sections fonctionnelles :

### 1. Tableau de Bord d'Observabilité
- **Visualisation de la dérive (`ArchetypeDriftService`) :** Graphiques temporels montrant la dérive des archétypes utilisateurs.
- **Journal des Guardrails :** Flux en temps réel des violations détectées (hallucinations, leaks, modération).

### 2. Panneau de Contrôle Dynamique (Guardrails)
- **Ajustement des Seuils :** Curseurs ou champs de saisie pour modifier en temps réel les seuils (ex: sensibilité hallucination, sévérité de modération).
- **Toggles :** Activation/désactivation par catégorie (SPOILER, JAILBREAK, etc.).

### 3. Gestion des configurations
- **Enregistrement :** Sauvegarde des configurations de seuils appliquées.
- **Réinitialisation :** Bouton pour revenir aux seuils par défaut (production).

## Fonctionnalités Clés
- **Pilotage manuel :** Ajustement dynamique de la politique de sécurité IA.
- **Supervision avancée :** Visibilité sur les dérives et les tentatives d'attaques.

---
*Document de conception validé.*
