# Spécification Technique : Diagnostics & Incertitude Avancés

- **Date :** 2026-06-01
- **Sujet :** Migration vers l'exploitation des logprobs réels pour la quantification de l'incertitude.
- **Statut :** Approuvé (Phase Conception)

## 1. Objectif
Améliorer la précision du système d'auto-évaluation (XAI) en remplaçant l'estimation par proxy (modèle GPT-2 local) par l'utilisation des probabilités logarithmiques (`logprobs`) réelles fournies par les moteurs d'inférence (Ollama, BrainAPI, etc.).

## 2. Modifications Architecturales

### 2.1 Schémas de données (`backend/core/domain/entities/ai_schemas.py`)
Introduction de structures pour transporter les métadonnées d'inférence.

```python
class TokenLogProb(BaseModel):
    token: str
    logprob: float
    top_logprobs: Optional[List[Dict[str, float]]] = None

class InferenceMetadata(BaseModel):
    logprobs: Optional[List[TokenLogProb]] = None
    usage: Optional[Dict[str, int]] = None
    thinking: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None

class InferenceResponse(BaseModel):
    text: str
    metadata: InferenceMetadata
```

### 2.2 Interface `InferencePort` (`backend/core/ports/inference_port.py`)
Mise à jour de la signature de `generate` pour retourner un objet `InferenceResponse`.

```python
def generate(
    self, 
    prompt: str, 
    system_prompt: str = "...",
    thinking_budget: int = 0,
    thinking_mode: bool = False,
    include_logprobs: bool = True  # Nouveau paramètre
) -> InferenceResponse:
    ...
```

### 2.3 Services de Domaine (`backend/core/domain/services/xai_service.py`)
- **UncertaintyService :** La méthode `measure_confidence` doit maintenant accepter une `InferenceResponse` optionnelle.
- **Logique de calcul :** 
    1. Si `InferenceResponse.metadata.logprobs` est présent, calculer l'entropie directement.
    2. Sinon, basculer sur le calcul via le modèle local GPT-2 (fallback).

## 3. Impact sur les Adaptateurs
- **UnifiedInferenceAdapter :** Doit extraire les logprobs si disponibles via l'API OpenAI/Ollama compatible.
- **BrainAPIAdapter :** Mise à jour pour parser les logprobs retournés par le "Cerveau" distant.
- **FallbackInferenceAdapter :** Doit propager l'objet `InferenceResponse` complet.

## 4. Bénéfices attendus
- **Fidélité :** Mesure de confiance alignée sur l'état interne réel du modèle utilisé.
- **Performance :** Suppression d'un passage redondant dans GPT-2 pour les modèles supportant les logprobs.
- **Robustesse :** Meilleure détection des hallucinations dans le workflow RAG.

## 5. Plan de Test
- **Unit Tests :** Vérifier que `UncertaintyService` calcule correctement l'entropie à partir d'une liste de logprobs fournie.
- **Integration Tests :** Simuler une réponse d'adaptateur avec logprobs et vérifier que le fallback n'est pas déclenché.
- **Regression :** Vérifier que les anciens adaptateurs (sans logprobs) fonctionnent toujours via le fallback GPT-2.
