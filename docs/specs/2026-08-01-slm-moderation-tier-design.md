# Étage SLM pour la modération — design

*2026-08-01 — statut : validé, prêt pour le plan d'implémentation.*

## Le problème

Un tour de chat compagnon coûte **trois appels au modèle 7B**, dont deux ne servent
qu'à modérer. [`companion.py`](../../backend/api/animetix/api/companion.py) est
strictement sériel — `validate_input`, génération, `validate_output` — et sans
streaming : l'utilisateur attend les trois.

Pire, le premier étage ne modère rien. `GuardrailService` reçoit comme
`safety_engine` un `LocalGuardrailAdapter` câblé sur l'`UnifiedInferenceAdapter`
([`containers/inference.py:97-102`](../../backend/api/animetix/containers/inference.py)),
or le conteneur web n'a **ni `LLM_API_BASE` ni `LLM_MODEL_NAME`** (vérifié sur le
service Cloud Run) : cet adaptateur tape `http://localhost:11434`, où rien
n'écoute côté web. Chaque modération d'entrée paie donc un appel voué à l'échec,
retombe en « stub », puis fait quand même l'appel au gros modèle.

Le chemin visé existe déjà et n'est pas branché : le brain expose `/moderate`
([`brain_service.py:504`](../../backend/adapters/inference/brain_service.py)) et
`BrainAPIAdapter.moderate_content` l'appelle
([`brain_api_adapter.py:644`](../../backend/adapters/inference/brain_api_adapter.py)).
Il manque le câble et un modèle à la bonne taille.

## Objectif et cadrage

**Objectif retenu : la latence du chat.** Le coût des tokens et le cold start du
brain sont des bénéfices secondaires, pas des critères d'arbitrage.

**L'hébergement est contraint, pas choisi.** Le conteneur web a 4 GiB et
[`inference_config.py:56-72`](../../backend/core/utils/inference_config.py)
interdit explicitement les poids chargés en process — une instance qui charge un
modèle se fait OOM-killer, ce que Cloud Run rend en 503. Un modèle CPU dans le web
est donc exclu d'office. Le brain est déjà sur le chemin critique du chat (en
production la chaîne vaut `[brain_api, google_genai]`, `LOCAL_INFERENCE_ENABLED`
étant faux hors dev), donc y placer la modération **n'ajoute aucun cold start**.

Hors périmètre : les autres rôles mécaniques (reformulation de requête, extraction
structurée, classification d'intention). Ils tiennent sur la même mécanique une
fois celle-ci en place, mais ils n'améliorent pas la latence du chat et
tripleraient la surface de la première livraison.

## Le design

### Côté brain

`GenerateRequest` **et** `ModerateRequest` gagnent un champ `model: Optional[str]`,
et `/generate` comme `/moderate` servent le tag demandé plutôt que le seul tag
configuré. Les deux endpoints comptent : `_llm_moderate` passe par `/generate`
(prompt taillé) tandis que le `safety_engine` passe par `/moderate` — n'en équiper
qu'un laisserait la moitié de la modération sur le 7B. Le service garde un **cache
d'engines par modèle** ; il n'en construit pas un par requête.

Un client ne choisit pas un modèle arbitraire : le brain n'accepte que les tags
**réellement registrés auprès d'Ollama**, vérifiés contre `/api/tags`. C'est la
vérification d'appartenance introduite pour le health check dans
`_downgrade_if_model_unserved`, réutilisée ici. Un tag inconnu est rejeté en 400 —
jamais servi, jamais silencieux.

L'image bake un troisième tag via un `ARG`, comme les deux autres :
`qwen2.5:1.5b-instruct` (~1 Go). Le `CMD` le **préchauffe** au démarrage au même
titre que le modèle principal ; sans ça, la première modération après un réveil
paie le chargement et le problème est déplacé, pas résolu. Sur les 22 Go utilisables
de la L4, 4,7 Go + 1 Go cohabitent sans tension, et `OLLAMA_KEEP_ALIVE=24h` les
garde résidents.

Le choix du 1,5B plutôt que du 0,5B est délibéré : la détection de spoiler demande
de comprendre ce qui est révélé, pas de repérer un mot.

La forme de la sortie JSON n'est PAS garantie d'office : le décodage contraint ne
s'active que si l'appel demande `json_mode`, et ce drapeau devait traverser trois
maillons qui le perdaient (payload de `BrainAPIAdapter`, schéma `GenerateRequest`
— Pydantic jette un champ non déclaré en silence —, puis l'endpoint). Il les
traverse maintenant, et la modération le demande. Comme un décodage contraint
reste un « très probablement » et pas un « toujours », une réponse illisible
déclenche le MÊME repli sur le moteur principal qu'un appel en échec : dans les
deux cas il n'y a pas de verdict, et un contrôle sauté ne doit pas prendre
l'apparence d'un contrôle passé. Le risque résiduel porte donc sur la qualité de
la décision, pas sur sa lisibilité. Le rôle étant surchargeable par variable
d'environnement, descendre au 0,5B après mesure ne coûtera qu'une variable.

### Côté web

`BrainAPIAdapter` accepte un `model` optionnel qu'il transmet. Le conteneur fournit
un `brain_guardrail_adapter` : le même adaptateur, épinglé sur le petit tag via un
nouveau rôle `GUARDRAIL_OLLAMA_MODEL` dans `core/utils/local_models.py`,
surchargeable par `GUARDRAIL_MODEL_NAME` comme les autres rôles.

Deux branchements :

1. `local_guardrail_adapter` reçoit `brain_guardrail_adapter` au lieu de
   l'`unified` mort. Le premier étage se met à modérer et l'appel `localhost`
   condamné disparaît.
2. `GuardrailService` gagne un paramètre `moderation_engine` **optionnel**, par
   défaut `inference_engine` — donc rien ne change là où il n'est pas fourni — et
   `_llm_moderate` l'utilise. C'est ce qui fait basculer `validate_output` sur le
   petit modèle **sans toucher aux prompts** : `input_moderator` et
   `output_moderator` restent où ils sont, seul le moteur qui les exécute change.

### Le chemin critique

| Étape | Aujourd'hui | Après |
| --- | --- | --- |
| Entrée | appel `localhost` en échec → stub → 7B | 1,5B |
| Génération | 7B | 7B |
| Sortie | 7B | 1,5B |

Un seul appel au gros modèle au lieu de trois, et l'appel mort supprimé.

### Postures d'échec

Si le petit modèle est indisponible, `/moderate` et `/generate` retombent sur le
moteur principal : plus lent, jamais fail-open silencieux. La posture
`GUARDRAIL_FAIL_CLOSED` existante n'est pas modifiée, et les couches
déterministes (regex de jailbreak, empreintes de fuite système) restent en amont
du moteur, donc actives quoi qu'il arrive.

## Tests

- `tests/deploy/test_brain_model_tag_is_baked.py` est **étendu au nouveau rôle** :
  un `GUARDRAIL_MODEL_NAME` pointant sur un tag non baké fait échouer la CI. La
  classe de bug du 2026-08-01 (un tag servi que l'image ne registre pas) ne peut
  pas revenir par cette porte.
- Câblage du conteneur : le `safety_engine` du guardrail est bien l'adaptateur
  brain, et il est épinglé sur le rôle guardrail.
- Le brain rejette en 400 un `model` non registré auprès d'Ollama.
- Repli sur le moteur principal quand le petit modèle manque.
- `GuardrailService` sans `moderation_engine` se comporte exactement comme avant.

## Mesure

Une mesure avant/après sur le même prompt, **sur instance chaude vérifiée** (une
requête de chauffe d'abord, la mesure ensuite). La seule mesure existante à ce jour
— 6,79 s pour 3 tokens — a été prise sur une instance qui venait de démarrer et
inclut probablement le chargement des 4,7 Go : elle ne vaut pas de référence. Aucun
gain ne sera annoncé sur une estimation.

## Déploiement

Toucher à ce qui est baké impose un rebuild de l'image brain (~90 min) **et un
déploiement manuel** : la CI ne reconstruit jamais le brain, seulement le web. Une
modification livrée sans ce déploiement laisse la feature morte avec un pipeline
vert. Le déploiement fait donc partie de la livraison, pas de l'après.
