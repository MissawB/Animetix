# Tripwire du namespace unique — ce package ne doit JAMAIS être importé.
# La racine canonique est nue : animetix / animetix_project (via backend/api
# sur sys.path), core / adapters / pipeline / scripts (via backend/ sur
# sys.path). Importer backend.* recrée une seconde identité des mêmes modules
# (modèles/signaux/DI chargés deux fois).
# Voir docs/plans/2026-07-05-unify-import-namespace-design.md.
raise ImportError(
    "Import via 'backend.*' interdit : utilisez la racine nue "
    "(animetix, core, adapters, pipeline, scripts). "
    "Voir docs/plans/2026-07-05-unify-import-namespace-design.md"
)
