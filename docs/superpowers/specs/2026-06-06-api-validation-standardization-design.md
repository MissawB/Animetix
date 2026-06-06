# Design Doc: Standardisation de la validation API (Django Forms & Pydantic)

**Date:** 2026-06-06  
**Status:** Approved  
**Topic:** Finaliser la refactorisation des vues dans `backend/api/animetix/views/api.py` pour utiliser systématiquement les Django Forms (et Pydantic pour le JSON complexe).

## 1. Objectifs
- Supprimer les accès directs à `request.GET` et `request.POST` dans `api.py`.
- Centraliser la validation et le nettoyage des données dans des classes dédiées.
- Utiliser des noms de champs plus descriptifs (`query` au lieu de `q`, `target_secret` au lieu de `secret`, etc.).
- Maintenir la conformité avec le mandat `GEMINI.md` du backend.

## 2. Architecture des Formulaires (Django)
Les formulaires seront regroupés dans `backend/api/animetix/forms.py`.

### Nouveaux Formulaires
- `EmojiStreamForm` : Valide `target_secret`.
- `ParadoxStreamForm` : Valide `item_a`, `item_b`, `intruder_item`.
- `AgenticRagForm` : Valide `query`.
- `AniminatorForm` : Mis à jour pour utiliser `query` au lieu de `question`.

## 3. Schéma de Synchronisation (Pydantic)
Pour la synchronisation offline, qui reçoit une liste JSON complexe via `request.body`, nous utilisons Pydantic pour une validation robuste.

Fichier : `backend/api/animetix/schemas.py`
- `OfflineGameResult` : Définit la structure d'un résultat de jeu (mode, média, score, tentatives).
- `OfflineSyncSchema` : Valide la liste de résultats (max 50 items).

## 4. Refactorisation des Vues (`api.py`)
Chaque vue sera modifiée pour :
1. Instancier le formulaire approprié (ou le schéma Pydantic).
2. Vérifier la validité (`is_valid()` ou `model_validate()`).
3. Renvoyer une `JsonResponse` d'erreur (400) si les données sont invalides.
4. Utiliser les données nettoyées (`form.cleaned_data` ou le modèle Pydantic).

### Exemple de transformation : `emoji_decode_stream`
**Avant :**
```python
secret = request.GET.get('secret')
if not secret: return HttpResponse(status=400)
```
**Après :**
```python
form = EmojiStreamForm(request.GET)
if not form.is_valid():
    return JsonResponse({'error': form.errors}, status=400)
secret = form.cleaned_data['target_secret']
```

## 5. Plan de Validation
- Tests unitaires pour chaque nouveau formulaire.
- Test d'intégration pour `sync_offline_data` avec des payloads JSON valides et invalides.
- Vérification manuelle des flux SSE pour s'assurer que le renommage des paramètres n'a pas cassé le frontend (Note: Si le frontend utilise les anciens noms `q`, `secret`, etc., le formulaire devra mapper `q` -> `query` via l'argument `data` ou le frontend devra être mis à jour).

*Note sur la compatibilité frontend : Pour minimiser les ruptures, les formulaires Django utiliseront les noms actuels (`q`, `secret`, `t1`, `t2`, `intruder`) comme noms de champs internes, ou je mapperai manuellement les données.*

**Décision Finale :** Je vais utiliser les noms de champs descriptifs dans les formulaires mais les lier aux paramètres de requête existants pour éviter de casser le frontend immédiatement, ou je mettrai à jour le frontend si c'est trivial.
