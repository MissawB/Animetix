# TTL du cache "la collection a-t-elle des vecteurs ?", partagé par les deux
# adapters pgvector (`PgVectorStoreAdapter` et `PGVectorRepositoryAdapter`).
# Cette question est posée avant chaque recherche payante (garde-fou
# anti-facturation d'un index vide) -- sans cache, ce serait une requête
# COUNT(*) de plus par recherche. 60s suffit : il ne s'agit que de détecter si
# l'index a été construit, pas de suivre un compteur exact en temps réel (un
# backfill met alors jusqu'à 60s à "débloquer" la recherche -- c'est le
# compromis accepté, et `upsert_items`/`delete_collection` invalident le cache
# explicitement pour raccourcir cette fenêtre au cas normal).
#
# Une seule définition : les deux adapters comptent la même chose (un booléen
# "la collection a au moins un vecteur ?") et doivent donc partager le même
# TTL au lieu de deux littéraux qui pourraient diverger silencieusement.
COLLECTION_COUNT_CACHE_TTL_SECONDS = 60

# Préfixes des deux clés de cache ci-dessus -- une par adapter, PAS une
# partagée : `PGVectorRepositoryAdapter` (le côté ÉCRITURE, `upsert_items` /
# `delete_collection`) et `PgVectorStoreAdapter` (le côté LECTURE, le
# garde-fou 503 « index non construit » de `MediaSearchView`) comptaient la
# même chose sous deux clés différentes, et seule celle de l'écrivain était
# invalidée après un backfill. Le garde-fou de lecture pouvait donc continuer
# à répondre « index non construit » jusqu'à `COLLECTION_COUNT_CACHE_TTL_SECONDS`
# après qu'une construction venait de réussir. Nommer les deux préfixes ICI
# permet à une écriture d'invalider les deux d'un coup.
PGVRA_COLLECTION_COUNT_CACHE_PREFIX = "pgvra_collection_count_"
VSP_COLLECTION_COUNT_CACHE_PREFIX = "vsp_collection_count_"
