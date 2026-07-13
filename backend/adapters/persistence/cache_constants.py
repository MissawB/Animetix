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
