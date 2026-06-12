select event_id
from {{ source('telemetry_source', 'archetype_drift') }}
where intensity < 0.0 or intensity > 1.0 or logic_consistency < 0.0 or logic_consistency > 1.0
