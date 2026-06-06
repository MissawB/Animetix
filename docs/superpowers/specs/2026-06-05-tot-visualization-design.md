# Design Spec: Visualisation "Tree of Thoughts" (Expert Lab)

**Date :** 2026-06-05
**Sujet :** Création d'une page de laboratoire (MCTS/ToT) pour explorer et visualiser le processus de raisonnement de l'IA.

## 1. Objectifs
- Modifier le service backend `TreeOfThoughtsSearchService` pour qu'il capture l'arbre de décision complet (nœuds explorés, scores, élagages).
- Créer une nouvelle interface "Lab" (`TreeOfThoughtsPage.tsx`) ouverte à tous les utilisateurs.
- Visualiser l'arbre de raisonnement via un **Interactive Force Graph** interactif (`react-force-graph-2d`).

## 2. Architecture Backend

### 2.1 Modification du `TreeOfThoughtsSearchService`
- **Fichier :** `backend/core/domain/services/tree_of_thoughts_service.py`
- **Changements :**
    - Créer une structure de données `full_tree` : `{"nodes": [], "edges": []}`.
    - Lors de la génération d'une nouvelle "pensée" (next_thought), ajouter un nœud à `full_tree["nodes"]`.
        - Champs : `id` (ex: "step_2_branch_1"), `label` (texte court), `full_text` (texte complet), `score`, `status` ("selected", "pruned", "root", "final").
    - Créer un lien (edge) dans `full_tree["edges"]` entre le nœud parent et ce nouveau nœud.
    - Retourner ce `full_tree` en plus de la `final_answer` dans le dictionnaire de résultat.

### 2.2 Nouvel Endpoint API
- **Fichiers :** `backend/api/animetix/api/labs.py` & `backend/api/animetix/urls/api.py`
- **Logique :**
    - Créer `TreeOfThoughtsLabView(APIView)`.
    - Injecter le `tree_of_thoughts_service`.
    - Méthode POST acceptant une `query`.
    - Appeler `self.tot_service.solve_with_tree_of_thoughts(query)`.
    - Retourner la réponse complète (réponse finale + structure de graphe).
    - **Permissions :** `AllowAny` (comme demandé, ouvert à tous).

## 3. Architecture Frontend (React)

### 3.1 Nouvelle Page : `TreeOfThoughtsPage.tsx`
- **Dossier :** `frontend/src/features/labs/`
- **Composants :**
    - **Input Section :** Un textarea stylisé pour poser le problème/question complexe.
    - **Graph Section :** Utilisation de `ForceGraph2D` (depuis `react-force-graph-2d`).
        - *Styling des nœuds :* 
            - Nœud racine : Blanc, grande taille.
            - Nœuds sélectionnés (score élevé) : Vert/Émeraude fluo, liés à la réponse finale.
            - Nœuds élagués (score faible) : Rouge sombre, petite taille.
            - Nœud final : Jaune/Or (Conclusion).
    - **Side Panel (Inspector) :** Lorsqu'un utilisateur clique sur un nœud dans le graphe, un panneau latéral glisse pour afficher le détail de la pensée, le score exact attribué par le critique logique, et le statut.

### 3.2 Intégration
- Lier la nouvelle page dans `SocialRoutes.tsx`.
- Ajouter une tuile de présentation dans le `LabHubPage.tsx` pour y accéder.

## 4. Flux de Données
1. L'utilisateur pose une question complexe dans le Lab.
2. Le frontend affiche un loader "Construction de l'arbre sémantique...".
3. Le backend exécute les N étapes de raisonnement, score chaque branche, élague les mauvaises, et synthétise.
4. L'API renvoie le résultat JSON contenant `nodes` et `edges`.
5. Le composant `ForceGraph2D` s'anime et déploie le réseau de neurones simulé sous les yeux de l'utilisateur.

## 5. Critères d'Acceptation
- [ ] Le backend renvoie l'arbre complet sans casser la logique de génération existante.
- [ ] Le graphe frontend est interactif (zoom, drag, click).
- [ ] Les couleurs des nœuds reflètent correctement leur statut (sélectionné vs élagué).
- [ ] Le panneau latéral affiche les détails au clic sur un nœud.
