# Audit générateurs annexes — 2026-07-17

Critères appliqués à chaque générateur :
1. Slot numérique non-conditionné (nombre absent de la question/du contexte fourni, hors année/volume/épisode réel).
2. Sortie identique en masse (le même texte de sortie mappé à N questions différentes).

## Verdicts

- `relation_generators.py` — **SAIN** : toutes les fonctions (`generate_transmedia_instructions`, `generate_awards_and_magazines_instructions`, `generate_songs_and_seiyuu_instructions`, `generate_french_market_relations_instructions`, `generate_japanese_market_relations_instructions`, `generate_volumes_and_episodes_instructions`) projettent des champs réels (`question`/`answer`/`anime_episodes`/`manga_volumes`/`status`/`details`) issus de bases de données statiques écrites à la main. Aucun `rank`/`favs`/`votes` émis. Les 4 variations par relation reformulent la même réponse factuelle avec un habillage différent (pas une duplication insensée : la Q change, la substance de la réponse est la même car elle décrit le même fait) — conforme à l'attendu du spec.

- `market_profile_generators.py` — **SAIN** : les 15 templates par comédien/éditeur/distributeur projettent `data['definition']`, `data['examples']`, `data['origin']`, `data['impact']` — 4 champs réels combinés différemment par template (aucune paire de templates ne produit la même combinaison/ordre des 4 champs). Aucun `rank`/`favs`/`votes`/nombre non-conditionné. Grep du fichier : 0 occurrence de `rank|favourites|favs|votes`.

- `otaku_generators.py` — **SAIN** : 15 templates par concept/créateur, chacun projette une combinaison distincte de `definition`/`examples`/`impact`/`origin` (ou leur traduction EN via Gemini) → pas de sortie dupliquée. Les 12 comparaisons croisées (Tsundere/Yandere, etc.) sont du contenu écrit à la main. Grep confirme : 0 occurrence de `rank|favourites|favs|votes` dans ce fichier.

- `dialogue_generators.py` — **PATCHÉ** : deux maladies distinctes trouvées et corrigées.
  1. **Popularité fabriquée non-quantifiée** (scénario 4 « clarification », sous-scénario `studio_genre`) : les réponses EN/FR affirmaient que le personnage se classe « ranking high with many votes of admiration » / « se classant dans le top avec de nombreux votes d'admiration » — un trope de popularité inventé, sans aucune donnée en entrée pour l'étayer (même sans nombre explicite, c'est la même maladie que le slot numérique fabriqué : une affirmation quantitative-like non vérifiable). Remplacé par une formulation factuelle non-quantifiée : EN → "is one of the fan-favorite characters.", FR → "est particulièrement apprécié de la communauté des fans." La structure à 3 tours est conservée.
  2. **Ligne morte** : `biography = clean_source_prose(char.get("biography", ""))` dans la branche FR du scénario personnage (scénario 1) était appelée mais sa valeur `biography` n'était jamais consommée par `make_french_character_bio(name, origin, orgs)` (qui ne prend pas ce paramètre) — code mort introduit lors du Task 3 quand la biographie a été retirée du prompt FR. Ligne supprimée ; le retour EN équivalent (ligne 143) reste car `make_english_character_bio` consomme bien `biography`.
  3. **Trouvé en review finale** : le scénario 3 (« comparative debate ») affirmait `{pop1:,} members` / `{pop2:,} members` (EN) et `{pop1} membres` / `{pop2} membres` (FR) — la même maladie que ci-dessus, mais quantifiée cette fois (un compte de popularité non-conditionné, sans donnée en entrée pour l'étayer). Retiré des deux tours EN/FR ; les locals `pop1`/`pop2` (désormais inutilisés) ont été supprimés. `BANNED_NUMERIC` (`tests/mlops/test_dataset_sanitation.py`) a été étendu avec `\d[\d,]*\s+(members|membres)` pour que le garde-fou `test_no_numeric_noise_in_dialogue_turns` détecte désormais cette classe de fuite.

- `synthetic_generators.py` — **SAIN** (avec analyse RAG explicite ci-dessous). Les autres sections (`generate_mcp_tool_instructions`, `generate_negative_refusal_examples`) sont des simulations d'outils MCP/refus à contenu fixe ou dérivé de données fournies dans le `tool_response` JSON — tous les nombres émis (`episodes`, `score`, `popularity` Spotify) proviennent du JSON injecté dans `input`, donc conditionnés.

### Raisonnement RAG (`generate_rag_context_instructions`, Scenario C, ~lignes 566/584/595)

Les documents `[Document A]` simulés contiennent `{favs} favorites` (EN, ligne 584) / `{favs} votes d'admiration` (FR, ligne 595). Le nombre `favs` est extrait de `char.get("popularity", {}).get("favourites", 0)` — c'est-à-dire qu'il est **injecté dans le contexte fourni en `input`**, exactement comme le veut la simulation RAG (le modèle doit apprendre à lire un document fourni, pas à halluciner).

Vérification de l'`output` correspondant (lignes 592-593 EN, 603-604 FR) : la réponse cite uniquement `name`, `origin` et `height` — **elle ne reprend jamais `favs`**. La question posée (`q`, lignes 592/603) ne porte d'ailleurs même pas sur la popularité (elle demande la taille officielle et l'œuvre d'origine), donc le modèle est entraîné à ignorer une donnée non pertinente présente dans le contexte, ce qui est le comportement RAG souhaité (extraction sélective + ignorance du bruit, comme documenté explicitement dans la docstring de la fonction : « inclut du bruit … que le modèle doit ignorer »). Aucune fabrication : le chiffre n'apparaît jamais en sortie sans être présent en entrée.

`synthetic_generators.py:566` — `{"favourites": 150000, "rank": 1}` fait partie du dict de fixture par défaut utilisé quand `characters` est vide (construction de données d'entrée), pas une sortie du modèle → **SAIN**, confirmé.

## Suite de tests

Après patch de `dialogue_generators.py`, toute la suite `tests/mlops/` a été relancée (voir rapport de tâche pour la sortie complète) : **PASS**. Aucun test n'asserte le texte exact du filler « votes of admiration »/« votes d'admiration » supprimé dans `dialogue_generators.py` (la seule occurrence de « votes d'admiration » dans les tests, `test_finetuning_dataset.py:178`, porte sur `make_french_character_bio`, une fonction différente déjà corrigée en Task 3, non affectée par ce patch) ; les tests `test_generate_multiturn_dialogues` et `test_generate_multiturn_dialogues_complex_scenarios` ne vérifient que la structure (≥2 tours, langue), qui reste intacte.
