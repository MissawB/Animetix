# 🎯 Spécification Technique : Standardisation des Logs & Élimination du Silent Error Handling

- **Date :** 2026-05-26
- **Auteur :** Antigravity
- **Statut :** Approuvé (par défaut après timeout)
- **Composants ciblés :** `GuardrailService`, `TreeOfThoughtsSearchService`, `DSPyPromptOptimizer`, `CounterfactualConversationSimulator`, `Labs API View`, `Neo4jGraphAdapter`

---

## 📌 1. Contexte & Problématique
Une analyse approfondie du codebase a révélé 14 occurrences de captures génériques d'exceptions (`except Exception:`) dont plusieurs étouffent silencieusement les erreurs de calculs ou d'infrastructures críticas. Ce manque de transparence conduit à :
1. **Des failles de sécurité/sécurité fonctionnelle :** Le `GuardrailService` renvoie silencieusement `is_safe=True` si l'API de modération ou le LLM plante, contournant ainsi le filtrage de contenu de manière invisible.
2. **De la dette de débogage :** Des échecs d'évaluation dans Tree-of-Thoughts ou DSPy sont remplacés par des scores arbitraires (0.7, 0.75, 0.5) sans laisser la moindre trace dans la console ou dans `ObservabilityService`.

---

## 🏗️ 2. Architecture de Résolution (Approche Hybride)

Nous mettons en place une stratégie hybride claire :

### 2.1 Pour les flux critiques (Sécurité/Modération)
Le `GuardrailService` ne doit jamais masquer un échec. Si le moteur d'inférence ou la validation plante, le service doit propager une exception typée `ContentModerationError` pour avertir l'orchestrateur amont qui pourra alors appliquer une politique de repli sécurisée (ex: bloquer par défaut).

```python
# Dans backend/core/domain/services/guardrail_service.py
except Exception as e:
    logger.exception("❌ Guardrail check failed due to unexpected error.")
    raise ContentModerationError("Guardrail verification failed.") from e
```

### 2.2 Pour les flux non critiques (Statistiques, Simulateurs, Optimiseurs)
Pour les simulateurs ou pages de reporting où un plantage complet de la requête n'est pas souhaitable, nous conservons la valeur de repli (ex: score de 0.7 ou statut indisponible), mais nous enregistrons systématiquement l'erreur de manière explicite via `logger.warning` avec la trace d'appel (`exc_info=True`).

```python
# Exemple dans tree_of_thoughts_service.py
except Exception as e:
    logger.warning("⚠️ Tree-of-Thoughts Critic evaluation failed. Falling back to default score 0.7.", exc_info=True)
    return 0.7
```

---

## 🛠️ 3. Fichiers impactés & Modifications spécifiques

### 3.1 `guardrail_service.py` ([guardrail_service.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/domain/services/guardrail_service.py))
- **Avant :**
  ```python
  except Exception:
      return { "is_safe": True, ... }
  ```
- **Après :**
  ```python
  except Exception as e:
      logger.exception("❌ Guardrail verification failed.")
      from core.domain.entities.exceptions import ContentModerationError
      raise ContentModerationError("Guardrail verification failed due to internal error.") from e
  ```

### 3.2 `tree_of_thoughts_service.py` ([tree_of_thoughts_service.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/domain/services/tree_of_thoughts_service.py))
- **Avant :**
  ```python
  except Exception:
      return 0.7
  ```
- **Après :**
  ```python
  except Exception as e:
      logger.warning("⚠️ Logic Critic evaluation failed. Falling back to 0.7.", exc_info=True)
      return 0.7
  ```

### 3.3 `dspy_prompt_optimizer.py` ([dspy_prompt_optimizer.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/domain/services/dspy_prompt_optimizer.py))
- **Avant :**
  ```python
  except Exception:
      scores.append(0.5)
  ...
  except Exception:
      return 0.7
  ```
- **Après :**
  ```python
  except Exception as e:
      logger.warning("⚠️ DSPy variant evaluation step failed. Appending fallback score 0.5.", exc_info=True)
      scores.append(0.5)
  ...
  except Exception as e:
      logger.warning("⚠️ DSPy Judge evaluation failed. Falling back to 0.7.", exc_info=True)
      return 0.7
  ```

### 3.4 `counterfactual_simulator.py` ([counterfactual_simulator.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/domain/services/counterfactual_simulator.py))
- **Avant :**
  ```python
  except Exception:
      alternative_utility = 0.75
  ```
- **Après :**
  ```python
  except Exception as e:
      logger.warning("⚠️ Counterfactual Utility evaluation failed. Falling back to 0.75.", exc_info=True)
      alternative_utility = 0.75
  ```

### 3.5 `labs.py` (Django View - [labs.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/api/labs.py))
- **Avant :**
  ```python
  except Exception:
      stats['knowledge_graph'] = {"status": "unavailable"}
  ```
- **Après :**
  ```python
  except Exception as e:
      logger.warning("⚠️ Failed to audit Knowledge Graph health. Mark as unavailable.", exc_info=True)
      stats['knowledge_graph'] = {"status": "unavailable"}
  ```

### 3.6 `neo4j_graph_adapter.py` ([neo4j_graph_adapter.py](file:///C:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/persistence/neo4j_graph_adapter.py))
- **Avant :**
  ```python
  except Exception:
      return False
  ```
- **Après :**
  ```python
  except Exception as e:
      logger.debug("Neo4j connectivity check failed.", exc_info=True)
      return False
  ```

---

## 🧪 4. Plan de Vérification
Des tests unitaires ciblés seront écrits dans `tests/core/test_guardrail_service.py` pour valider que `ContentModerationError` est bien levée en cas de défaillance. Nous validerons également les autres modules via pytest.
