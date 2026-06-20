# Task List (TODO) - Animetix

Ce document liste toutes les tâches techniques, architecturales et fonctionnelles restant à implémenter ou à corriger. Les tâches terminées sont archivées dans [docs/HISTORY.md](docs/HISTORY.md).

---

## 🚀 Expansion & Futur
- [ ] **Rapports de Conformité :** Automatiser les rapports hebdomadaires de conformité sécurité.
- [x] **Intégration de Tachidesk/Suwayomi (Mihon Backend) :** Connecter le projet à une instance Tachidesk/Suwayomi locale pour connecter les extensions de Mihon/Tachiyomi et accéder à plus de 500 sources de mangas.
- [x] **Optimisation du Lecteur Manga (React UX) :** Améliorer le confort de lecture dans le composant frontend (préchargement d'images, infinite scroll pour le mode Webtoon, découpe/affichage double page, et configurations du lecteur).
- [ ] **Gestionnaire d'Extensions Manga (Suwayomi) :** Permettre l'installation, la désinstallation et la mise à jour des extensions de sources de mangas directement via l'interface d'Animetix.
- [ ] **Suivi & Notifications des Chapitres Manga :** Vérifier les mises à jour des mangas favoris en arrière-plan via une tâche périodique Celery/Django et envoyer des notifications WebSocket lors de la sortie de nouveaux chapitres.
- [ ] **Mode Hors-ligne du Lecteur Manga (PWA) :** Permettre le téléchargement local des chapitres pour une lecture hors-ligne via Service Workers et IndexedDB/Cache API.
- [ ] **Synchronisation avec des Trackers (MAL / AniList) :** Lier les profils tiers des utilisateurs pour synchroniser automatiquement leur progression de lecture à la complétion d'un chapitre.
- [ ] **Catégorisation & Tri de la Bibliothèque :** Organiser la collection de mangas dans des dossiers personnalisés ("En cours", "Terminé", "À lire") avec filtres et compteurs de chapitres non lus.
- [x] **Chat en Temps Réel pour les Clubs :** Intégrer un canal de discussion instantanée (via WebSockets / Django Channels) au sein de chaque Club de découverte pour favoriser l'aspect communautaire.
- [x] **Self-Hosted AI Image Worker (MLOps) :** Configurer un travailleur local (Stable Diffusion / ComfyUI) géré par notre file d'attente de tâches (`enqueue_task`) en cas de dépassement de budget ou d'indisponibilité des API payantes, monitoré sur le tableau de bord "État du Cluster".
- [x] **Optimisation de la rapidité du LLM (Speculative Decoding & KV Cache) :** Accélérer le temps de réponse de nos LLM en implémentant du décodage spéculatif (EAGLE, Medusa) et du cache sémantique/RadixAttention. *Note : Rajouter les papiers de recherche associés dans la page dédiée* [RESEARCH_PAPERS.md](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/docs/RESEARCH_PAPERS.md).
---
*Dernière mise à jour : 20 Juin 2026*