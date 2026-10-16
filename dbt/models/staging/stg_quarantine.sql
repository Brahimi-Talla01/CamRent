{{ config(materialized='view', schema='staging') }}

-- Quarantaine de la Phase 2 : une ligne par observation **rejetée**, conservée
-- avec son motif. Aucune ligne n'est supprimée ni corrigée ici (invariant 5
-- d'architecture-context.md) ; la table sert le module « Qualité » du
-- back-office et l'observabilité (Phase 11).
-- Source : `landing.quarantine_listings`, chargée par `python -m pipelines load`
-- (pipelines/db.py) depuis data/processed/quarantine_listings.parquet.

with source as (

    select *
    from {{ source('landing', 'quarantine_listings') }}

)

select
    source                                           as source_name,
    source_file,
    source_listing_id,
    url,
    city,
    neighborhood,
    property_type,
    rent_price::bigint                               as rent_price,
    currency,
    price_is_bound::boolean                          as price_is_bound,
    outlier_flags,
    quarantine_reason,
    collected_at,
    md5(coalesce(source_file, '') || '|' || coalesce(source_listing_id, '')) as listing_key
from source
