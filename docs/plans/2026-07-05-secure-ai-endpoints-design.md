# Sécurisation des endpoints IA/GPU + throttling rationnel

**Date** : 2026-07-05 · **Statut** : validé · **Origine** : item 🟠 de l'audit dette 2026-07-05

## Contexte et périmètre réel (corrige l'audit)

L'audit citait 4 vues labs ; l'inventaire précis montre que 3 d'entre elles
(`MangaLabDataView`, `AudioLabDataView`, `SeiyuuDiscoveryView`) sont CPU/DB pures et
restent `AllowAny`. Les **vrais** trous IA anonymes sont :

| # | Endpoint | Coût réel | Décision (validée) |
| --- | --- | --- | --- |
| 1 | `consumers/speech_to_speech_live.py:88` `SpeechToSpeechLiveConsumer` (WS `ws/labs/s2s/live/`) | Session **Gemini Multimodal Live** entière, ni auth ni Bx ni limite — le plus grave | Auth au connect + Bx forfaitaire/session + durée max |
| 2 | `api/graph.py:80` `GraphWorldMapView` | `run_partitioning()` → un résumé LLM **par communauté, par hit anonyme** | Cache partagé (artefact identique pour tous) — reste public |
| 3 | `api/labs.py:640` `VideoRAGSearchView` | RAG/vector vidéo (`video_rag_service().search_video_segment`) | Pattern canonique auth + Bx |
| 4 | `api/core.py:109` `MediaSearchView` (GET) | Fallback `_llm_moderate()` du guardrail = LLM non borné sur input anonyme | Endpoint reste public ; fallback LLM réservé aux authentifiés |

Règle produit (mémoire projet) : « toute feature GPU/IA consomme des Bx + require
login » ; les jeux CPU restent `AllowAny`. Contrainte historique : le cap anonyme
`100/day` a déjà cassé des parties de jeux CPU en cours → emoji (5 vues), undercover,
covertest (5 vues) portent `throttle_classes: list = []`, donc **zéro** protection.

## Design

### 1. S2S Live — auth + Bx au connect

Dans `SpeechToSpeechLiveConsumer.connect()` :

1. Résolution utilisateur : `scope["user"]` si `is_authenticated` (session via
   `AuthMiddlewareStack`, déjà en place — cf. `club_consumer.py:20`) ; sinon token
   Firebase en query param `?token=<id_token>`, validé en réutilisant le vérificateur
   de `animetix.auth` (celui de `GoogleIdentityAuthentication`). Échec → `close(code=4401)`.
2. Facturation : quota (`usage_port.check_quota`) puis déduction **forfaitaire par
   session** — nouvelle entrée `FEATURE_BX_COSTS["s2s_live"] = 12`
   (`core/domain/services/berrix_economy.py:93`) — via le helper async de
   `api/streams.py` (`_charge_bx_or_402` ou équivalent adapté au WS). Échec →
   `close(code=4402)`.
3. Durée max de session : timer asyncio de **10 minutes** → close propre code 4408
   (borne le coût Gemini).

Frontend : `SpeechToSpeechLabPage.tsx` ajoute le token à l'URL WS et un gate login
(pattern des autres features Bx).

### 2. Carte-monde — cache partagé, publique

`GraphWorldMapView` reste `AllowAny`. Le résultat de `run_partitioning()`
(communautés + résumés) passe par le cache Django (Redis en prod) : clé versionnée,
TTL 24 h, verrou anti-stampede (`cache.add` lock) pour qu'un seul hit paie la
génération. Management command de préchauffage/régénération optionnelle
(`warm_world_map`). Zéro LLM par requête servie du cache.

### 3. VideoRAG — pattern canonique

`VideoRAGSearchView` : `IsAuthenticated` + `usage_port.check_quota` +
`deduct_berrix(user, FEATURE_BX_COSTS["video_rag"], …)` (nouvelle entrée, 6 Bx) +
`usage_port.log_usage`, calqué sur `paradox.py:74-120`. + throttle scope `gpu`
(cf. §5). Frontend : gate login sur `VideoLabPage.tsx` et `VisualNexusPage.tsx`.

### 4. MediaSearch GET — modération LLM réservée aux authentifiés

Le GET reste `AllowAny` (barre de recherche publique). Dans le chemin guardrail
(`guardrail_service.validate_input`), le fallback `_llm_moderate()` ne s'exécute que
si l'appelant est authentifié — signature enrichie d'un flag (`allow_llm=…`) passé
par la vue ; les anonymes gardent la couche heuristique/regex. Le POST (CLIP) est
déjà correctement gaté (`core.py:170`).

### 5. Throttling à deux vitesses

Dans `settings.py` (`DEFAULT_THROTTLE_RATES`, l.258) et une nouvelle petite unité
`api/throttles.py` :

| Scope | Rate | Mécanisme | S'applique à |
| --- | --- | --- | --- |
| `anon` (existant) | `100/day` | inchangé | défaut global |
| `user` (existant) | `1000/day` | inchangé | défaut global |
| `anon_burst` (nouveau) | `30/min` | `BurstAnonRateThrottle` ajouté aux `DEFAULT_THROTTLE_CLASSES` | défaut global |
| `user_burst` (nouveau) | `120/min` | `BurstUserRateThrottle` idem | défaut global |
| `gpu` (mort → réel) | `30/hour` | `ScopedRateThrottle` ajouté aux `throttle_classes` des vues qui déclarent `throttle_scope="gpu"` | `labs.py:153,506,579` + `VideoRAGSearchView` |
| `cpu_game` (nouveau) | `60/min` | `CpuGameThrottle` (IP pour anon, user sinon) | remplace les `throttle_classes: list = []` d'emoji (×5), undercover (×1), covertest (×5) |

Propriétés : les rafales anonymes sont stoppées à la minute partout ; les jeux CPU ne
peuvent plus être floodés mais un humain ne déclenche jamais 60/min ; le cap
journalier ne s'applique toujours pas aux jeux CPU (cause historique des 429
mid-game) ; le scope `gpu` déclaré depuis des mois devient effectif.

## Ce qui ne change pas

Toutes les vues `AllowAny` de catégorie B (jeux CPU) et C (auth/config/catalogue/
labs data statiques/webhook Stripe/open data) — liste dans l'inventaire de session.
Les vues GPU déjà sécurisées (paradox, akinetix_rl, vs_battle, companion, vision
POST, SSE streams) ne sont pas touchées.

## Tests

- Par endpoint sécurisé : 401 anonyme, 402 solde insuffisant, 200 nominal avec
  déduction vérifiée (pattern des tests existants de paradox/vs_battle).
- S2S : `channels.testing.WebsocketCommunicator` — connect anonyme → close 4401 ;
  authentifié sans solde → 4402 ; authentifié avec solde → accepté + Bx déduits.
- Carte-monde : 1er hit appelle le partitioner (mock), 2e hit sert le cache (mock non
  rappelé) ; expiration/verrou couverts par test unitaire du wrapper de cache.
- MediaSearch : anonyme → `_llm_moderate` jamais appelé (mock) ; authentifié → chemin
  LLM possible.
- Throttles : test de config (chaque `throttle_scope` déclaré a un rate — plus de
  scope mort) + test fonctionnel 429 sur rafale (`cpu_game`, `anon_burst`) via
  override de rates bas en test.
- Frontend : tests de gate (pages redirigent/affichent le prompt login quand
  anonyme), pattern des gates existants.

## Risques et parades

- **Sessions WS** : l'auth session ne couvre que les logins Django ; les utilisateurs
  Firebase passent par le token query param — les deux chemins sont implémentés et
  testés.
- **Casse anonyme résiduelle** : seuls VideoLab/VisualNexus/S2S perdent l'accès
  anonyme (voulu) ; la recherche publique et la carte-monde restent intactes.
- **Faux 429 en jeu** : `cpu_game 60/min` est ~10× au-dessus d'un rythme humain ;
  les caps journaliers restent débranchés pour ces vues.
- **Stampede carte-monde** : verrou `cache.add` + TTL généreux. Comportement tranché :
  le détenteur du verrou génère et remplit le cache ; tout hit concurrent sans cache
  reçoit immédiatement **202 `{"status": "generating"}`** (pas d'attente bloquante) et
  le frontend re-tente ; une fois le cache chaud, tout le monde est servi en 200.
