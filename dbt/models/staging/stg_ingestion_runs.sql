{{ config(materialized='view', schema='staging') }}

-- Métadonnées de collecte, une ligne par lot brut (invariant « raw immuable » :
-- le fichier de métadonnées est écrit une seule fois, comme le brut).
-- Source : `landing.ingestion_runs`, chargée par `python -m pipelines load`
-- (pipelines/db.py) depuis data/raw/metadata/<date>/*.json.
--
-- Provenance renforcée (lot B, spec Phase 1 §6) : `connector_version`,
-- `content_sha256` et `lot_validation_status` sont nuls pour les lots collectés
-- avant l'ajout de ces champs — aucune valeur n'est inventée.

with source as (

    select *
    from {{ source('landing', 'ingestion_runs') }}

)

select
    source                                           as source_name,
    raw_file,
    category,
    method,
    format,
    collected_day::date                              as collected_day,
    collected_at::timestamptz                        as collected_at,
    record_count::integer                            as record_count,
    n_urls::integer                                  as n_urls,
    rights_status,
    connector_version,
    content_bytes::bigint                            as content_bytes,
    content_sha256,
    lot_validation_status,
    lot_validation_failures,
    notes,
    -- Un lot est « traçable » si sa provenance renforcée est complète.
    (connector_version is not null and content_sha256 is not null) as has_provenance
from source
