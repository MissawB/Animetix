# Design Spec: Suppression de toute trace des donations

Ce document détaille la conception technique pour supprimer définitivement le modèle `Donation` et toutes les références associées au soutien et aux dons dans le projet.

## 1. Contexte et Objectifs
Le projet contenait initialement une classe de modèle Django `Donation` inutilisée et des références associées dans la documentation technique. Afin de nettoyer le codebase et de supprimer toute dette technique relative aux dons, nous allons procéder à un nettoyage complet (code + base de données + documentation).

## 2. Changements Proposés

### 2.1. Backend (Django)
* **Fichier cible** : [models.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/api/animetix/models.py)
* **Action** : Supprimer la classe `Donation` (lignes 197 à 206).
* **Fichier cible** : [health_dashboard_service.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/core/domain/services/health_dashboard_service.py)
* **Action** : Conserver la valeur `"is_sustainable": False` mais nettoyer le commentaire `# Donations removed` pour éviter toute trace résiduelle.

### 2.2. Base de données
* **Action** : Générer une migration Django automatique via la commande :
  ```bash
  python manage.py makemigrations
  ```
  Cette migration contiendra l'opération `DeleteModel(name='Donation')`.
* **Action** : Appliquer la migration sur la base de données SQLite locale :
  ```bash
  python manage.py migrate
  ```

### 2.3. Documentation
* **Fichier cible** : [TODO.md](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/docs/TODO.md)
  * **Action** : Supprimer la ligne 14 : `- [ ] **Soutien & Dons (Donations)** : Créer une page \`/donate\` ou \`/support-us\`...`
* **Fichier cible** : [HISTORY.md](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/docs/HISTORY.md)
  * **Action** : Supprimer la ligne 32 : `- **Wall of Fame :** Déploiement de la page de soutien (\`SupportPage.tsx\`)...`

## 3. Plan de Vérification
* Lancer `python manage.py check` pour s'assurer qu'aucune autre partie du backend ne dépend du modèle supprimé.
* Lancer les tests unitaires existants s'ils sont disponibles.
