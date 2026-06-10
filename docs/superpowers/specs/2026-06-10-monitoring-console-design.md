# Spécification de la Console de Monitoring Pipeline

## Objectif
Développer une interface de contrôle et de surveillance pour les pipelines de scraping et la synchronisation Neo4j, permettant un pilotage manuel et une supervision avancée des tâches backend.

## Architecture UI
L'interface sera organisée en quatre sections fonctionnelles :

### 1. Vue "Vue d'ensemble du Pipeline"
- **État Global :** Affichage de l'état actuel des services (Scrapers actifs/inactifs).
- **Indicateurs clés :** Dernière date de synchronisation réussie (Neo4j).

### 2. Panneau de Pilotage
- **Actions Rapides :** Boutons de contrôle individuels pour déclencher manuellement :
    - Scrapers spécialisés.
    - Synchronisation Neo4j.
- **Indicateur de statut :** Feedback visuel pendant l'exécution d'une tâche.

### 3. Moniteur Temps Réel
- **Logs Intégrés :** Journalisation en temps réel des activités.
- **Filtrage :** Filtres par niveau (Erreurs, Succès, Avertissements) et par tâche.

### 4. Historique et Stats
- **Tableau de bord :** Taux de succès historique.
- **Performance :** Durée moyenne d'exécution par tâche.

## Fonctionnalités Clés
- **Pilotage manuel :** Déclenchement granulaire des tâches.
- **Supervision avancée :** Visibilité complète sur l'exécution, les erreurs et les performances.

---
*Document de conception validé.*
