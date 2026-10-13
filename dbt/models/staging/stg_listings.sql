{{
    config(
        materialized='view',
        schema='staging',
    )
}}

-- Grain : une ligne par observation Silver (aucun filtrage, aucune
-- déduplication supplémentaire au-delà de la Phase 2 ; issue #22).
-- Source : table d'atterrissage chargée par `python -m pipelines load`
-- (pipelines/db.py) depuis le Silver Parquet de la Phase 2.
-- Les drapeaux numériques/booléens sont typés ici, une seule fois.

with source as (

    select *
    from {{ source('landing', 'silver_listings') }}

)

select
    source                                           as source_name,
    source_file,
    source_listing_id,
    url,
    city,
    neighborhood,
    neighborhood_recognized::boolean                 as neighborhood_recognized,
    property_type,
    bedrooms::integer                                as bedrooms,
    bathrooms::integer                               as bathrooms,
    bedrooms_is_bound::boolean                       as bedrooms_is_bound,
    bathrooms_is_bound::boolean                      as bathrooms_is_bound,
    price_is_bound::boolean                          as price_is_bound,
    is_republication::boolean                        as is_republication,
    furnished,
    parking,
    gated,
    area_m2,
    rent_price::bigint                               as rent_price,
    currency,
    outlier_flags,
    posted_at,
    collected_at,
    md5(coalesce(source_file, '') || '|' || coalesce(source_listing_id, '')) as listing_key
from source
