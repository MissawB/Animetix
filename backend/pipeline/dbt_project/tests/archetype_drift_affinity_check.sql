-- Les affinités d'archétype (shonen / seinen) sont des scores normalisés et
-- doivent rester dans [0, 1], au même titre que `intensity` / `logic_consistency`.
-- Le test échoue (retourne des lignes) si une affinité sort de cet intervalle.
select event_id
from {{ source('telemetry_source', 'archetype_drift') }}
where shonen_affinity < 0.0
   or shonen_affinity > 1.0
   or seinen_affinity < 0.0
   or seinen_affinity > 1.0
