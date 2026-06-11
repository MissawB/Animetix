# Guide de Localisation des Assets Audio

Ce document vous guide pas à pas pour résoudre les erreurs `403 (Forbidden)` lors du chargement des fichiers audio de `mixkit.co`. Ces erreurs sont généralement dues à des protections contre le "hotlinking" (l'intégration directe de fichiers depuis un autre site web). La solution consiste à héberger ces fichiers directement dans votre projet.

---

## Étapes à suivre :

### Étape 1 : Créer le Répertoire des Effets Sonores

Vous devez créer un nouveau dossier dans votre projet pour y stocker les fichiers audio.

1.  Ouvrez l'explorateur de fichiers (Windows) ou le Finder (macOS) et naviguez jusqu'à la racine de votre projet.
2.  Allez dans le dossier `frontend/public`.
3.  Créez un nouveau dossier nommé `sfx` à l'intérieur de `frontend/public`.

    Le chemin complet du dossier devrait être : `frontend/public/sfx`

### Étape 2 : Télécharger les Fichiers Audio MP3

Cliquez sur chacun des liens ci-dessous pour télécharger les fichiers MP3. Assurez-vous de les enregistrer avec les noms de fichiers spécifiés.

1.  **Pour le son 'click' :**
    *   Lien : `https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3`
    *   Enregistrer sous : `2571-preview.mp3`

2.  **Pour le son 'win' :**
    *   Lien : `https://assets.mixkit.co/active_storage/sfx/1435/1435-preview.mp3`
    *   Enregistrer sous : `1435-preview.mp3`

3.  **Pour les sons 'loss' et 'error' :**
    *   Lien : `https://assets.mixkit.co/active_storage/sfx/2513/2513-preview.mp3`
    *   Enregistrer sous : `2513-preview.mp3`

4.  **Pour le son 'unlock' :**
    *   Lien : `https://assets.mixkit.co/active_storage/sfx/2019/2019-preview.mp3`
    *   Enregistrer sous : `2019-preview.mp3`

5.  **Pour le son 'reveal' :**
    *   Lien : `https://assets.mixkit.co/active_storage/sfx/2568/2568-preview.mp3`
    *   Enregistrer sous : `2568-preview.mp3`
    *(Note : L'implémentation originale contenait une erreur de lien, celui-ci est le fichier correct pour 'reveal'.)*

### Étape 3 : Placer les Fichiers dans le Répertoire du Projet

Une fois tous les fichiers MP3 téléchargés, déplacez-les dans le dossier `sfx` que vous avez créé à l'Étape 1.

*   Assurez-vous que les fichiers sont directement dans `frontend/public/sfx`.

### Étape 4 : Redémarrer le Serveur de Développement Frontend

Pour que votre application prenne en compte ces nouveaux fichiers locaux, vous devez redémarrer votre serveur de développement frontend.

1.  Arrêtez votre serveur frontend (généralement en appuyant sur `Ctrl+C` dans le terminal où il est lancé).
2.  Relancez le serveur (par exemple, avec `npm run dev` ou `yarn dev`, selon votre configuration).

---

## Vérification

Après avoir suivi toutes ces étapes :

*   Naviguez vers votre application dans le navigateur.
*   Ouvrez la console de développement (F12) et vérifiez l'onglet "Console" et "Réseau".
*   Les erreurs `403 (Forbidden)` pour les fichiers audio de `mixkit.co` ne devraient plus apparaître. Les sons devraient se charger et être joués correctement.

Si vous rencontrez toujours des problèmes, n'hésitez pas à me le faire savoir.