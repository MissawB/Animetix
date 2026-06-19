# Spécification Technique : Suppression de la Marketplace (Boutique d'Actifs)

Ce document décrit le plan pour supprimer définitivement la fonctionnalité de marketplace (achat/vente de Fusions Créatives via les Berrix) du projet Animetix, tant au niveau du frontend que du backend.

## 1. Contexte & Objectif

La marketplace permet actuellement aux utilisateurs de mettre en vente leurs Fusions Créatives contre des Berrix (monnaie virtuelle du site) et aux autres utilisateurs de les acheter. L'objectif est de supprimer entièrement cette fonctionnalité pour simplifier l'application.

## 2. Modifications Proposées

### Frontend

1.  **Suppression de la page de la boutique :**
    *   Fichier à supprimer : [ShopPage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/explore/ShopPage.tsx)
2.  **Mise à jour des routes :**
    *   Fichier à modifier : [ExploreRoutes.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/features/explore/routes/ExploreRoutes.tsx)
    *   Retirer l'import de `ShopPage` et la route `/explore/shop/`.
3.  **Nettoyage de l'interface et de la navigation :**
    *   Fichier à modifier : [ExplorePage.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/pages/explore/ExplorePage.tsx)
        *   Retirer le bouton/lien vers `/explore/shop/` ("Boutique d'Actifs").
    *   Fichier à modifier : [Layout.tsx](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/frontend/src/components/Layout.tsx)
        *   Retirer le lien "Boutique d'Actifs" de la Sidebar (lignes 175-177).

### Backend (Django)

1.  **Modèles de données (`models.py`) :**
    *   Fichier à modifier : [models.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/api/animetix/models.py)
        *   Supprimer la classe `MarketListing`.
        *   Retirer le champ relationnel ManyToMany `collected_fusions` dans `Profile`.
        *   Retirer les choix de transactions `"market_sale"` et `"market_purchase"` de `WalletTransaction.TRANSACTION_TYPES`.
2.  **Sérialiseurs (`serializers.py`) :**
    *   Fichier à modifier : [serializers.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/api/animetix/serializers.py)
        *   Supprimer la classe `MarketListingSerializer`.
        *   Retirer l'import de `MarketListing`.
3.  **Vues & Logique API (`api/explore.py`) :**
    *   Fichier à modifier : [explore.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/api/animetix/api/explore.py)
        *   Supprimer le ViewSet `MarketListingViewSet`.
        *   Retirer les imports de `MarketListing` et `MarketListingSerializer`.
4.  **Routage des URLs API (`urls/api.py`) :**
    *   Fichier à modifier : [api.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/backend/api/animetix/urls/api.py)
        *   Retirer tous les endpoints associés au marché (`market/listings/`).

### Cycle de Base de Données

*   Générer une migration Django via `manage.py makemigrations` pour appliquer la suppression des tables correspondantes au niveau SQL.

### Tests

*   Fichier à supprimer : [test_market_api.py](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/tests/api/test_market_api.py)

## 3. Plan de Vérification

### Tests Automatisés
*   Exécuter les tests restants de l'API `explore` pour s'assurer de l'absence de régressions :
    ```bash
    .venv\Scripts\pytest tests/api/test_explore.py
    ```

### Vérification Manuelle
*   Vérifier que les liens "Boutique d'Actifs" ne s'affichent plus dans la Sidebar ni sur la page d'exploration.
*   S'assurer que l'accès direct aux URLs de la boutique côté frontend redirige correctement ou n'affiche pas d'erreurs fatales.
