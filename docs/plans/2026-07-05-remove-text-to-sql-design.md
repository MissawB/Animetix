# Suppression de la surface text-to-SQL (SQL généré par LLM)

**Date** : 2026-07-05 · **Statut** : validé · **Origine** : item 🔴 de l'audit dette 2026-07-05

## Contexte et décision

`DjangoRepositoryAdapter.query_data_natural_language()` exécute du SQL produit par un LLM
(`cursor.execute(generated_sql)`), auto-flaggé `HIGH-RISK` dans le code. L'exploration a établi
que la chaîne est **du code mort** : aucun appelant de production (seuls le port, les adapters
et les tests la référencent), feature flag `ALLOYDB_NL_QUERY_ACTIVE=False` par défaut, et la
prod tourne sur Neon — le chemin natif `alloydb_ai_nl.get_sql` y est inexécutable. Si le code
tournait, il s'exécuterait avec les pleins droits de `neondb_owner`, bridé seulement par
`SET TRANSACTION READ ONLY`.

**Décision (validée par l'utilisateur)** : supprimer la feature de bout en bout — y compris
`sql_guard.py` (le validateur AST sqlglot), qui n'aurait plus aucun consommateur — plutôt que
la durcir (rôle DB dédié) ou la neutraliser. YAGNI : tout est récupérable dans git si la
feature revient ; la surface d'attaque et la charge de maintenance tombent à zéro.

## Périmètre

### Code supprimé

| Fichier | Élément |
| --- | --- |
| `backend/core/ports/repository_port.py` (l.110-113) | méthode abstraite `query_data_natural_language` |
| `backend/adapters/persistence/django_repository_adapter.py` | `is_alloydb_nl_query_supported()` (l.14-38) + `query_data_natural_language()` (l.222-337) + import `sql_guard` |
| `backend/adapters/persistence/unified_repository_adapter.py` (l.121-125) | délégation |
| `backend/adapters/persistence/pgvector_repository_adapter.py` (l.317-322) | stub « non supporté » |
| `backend/core/utils/sql_guard.py` | fichier entier |
| `scripts/verify/audit_sql_guard.py` | fichier entier |
| `backend/api/animetix_project/settings.py` (l.638-640) | `ALLOYDB_NL_QUERY_ACTIVE`, `ALLOYDB_NL_CONFIG_NAME` |

**Ne PAS toucher** : `ALLOYDB_EMBEDDING_MODEL` (settings.py:477, consommé par
`backend/pipeline/vector_client.py`) ; la migration `0028_alloydb_scann_and_ml` (index SCaNN,
concern distinct) ; l'entrée historique `docs/HISTORY.md` §[2026-06-10] (l.217) qui documente
la création de la feature (c'est de l'histoire).

### Tests supprimés

- `tests/core/test_alloydb_querydata_nl.py` (fichier entier — couvre le guard + les deux flux)
- `tests/security/test_sql_fuzzing.py` (fichier entier — fuzzing du guard)
- `tests/adapters/test_pgvector_repository_adapter.py` l.354 : l'assertion sur le stub
  (la ligne seule, le reste du fichier vit)

### Dépendances

- Retirer `sqlglot==25.0.0` de `requirements.in` (seul consommateur : `sql_guard`).
- Régénérer `requirements.txt` via `pip-compile` **sans** `--upgrade` (ne bouger que sqlglot
  et ses éventuels orphelins, pas les autres pins).

### Documentation

- `README.md` : retirer l.126 (« AlloyDB AI Tools ») et l.213 (« Two-Layered SQL Guardrail »).
- `docs/ROADMAP.md` l.59 : retirer la ligne « SQL Hardening ».
- `docs/FULL_GUIDE.md` l.100 : retirer la mention « SQL Guardrail ».
- `docs/HISTORY.md` : ajouter une entrée [2026-07-05] documentant le retrait et sa raison.
- `TODO.md` : cocher l'item 🔴 « SQL généré par LLM exécuté en base » avec renvoi HISTORY.

## Vérification

1. **Grep zéro-hit** (hors `docs/HISTORY.md`, spec/plans et historique git) :
   `query_data_natural_language|is_alloydb_nl_query_supported|sql_guard|validate_sql_query|sqlglot|ALLOYDB_NL`.
2. **Tests ciblés** (pas la suite `tests/api` complète, qui mass-fail localement sans backend
   d'inférence) : `tests/adapters/test_pgvector_repository_adapter.py` (seul test d'adapter
   repository existant) + collecte pytest globale (`--collect-only`) pour attraper tout
   import cassé.
3. **Lint/type** : ruff, black `--check`, mypy (depuis `backend/`).
4. **Couverture** : le gate CI à 75 % tranche. On supprime du code couvert *et* ses tests ;
   si le ratio passe sous 75 %, c'est un signal légitime à traiter, pas à contourner.

## Risques

- **Import cassé résiduel** : un consommateur dynamique non détecté par grep — mitigé par la
  vérification n°1 et les tests des adapters restants.
- **pip-compile qui dérive** : régénération sans `--upgrade` obligatoire ; diff de
  `requirements.txt` à relire (seuls sqlglot et orphelins doivent bouger).
