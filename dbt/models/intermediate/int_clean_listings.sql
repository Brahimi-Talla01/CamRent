{{
    config(
        materialized='view',
        schema='intermediate',
    )
}}

-- Enrichissement léger de `stg_listings` : dérivations réutilisables par les
-- dims et les marts. Aucune ligne n'est filtrée ni imputée : les drapeaux
-- portent l'information de qualité (invariants 5 et 8 d'architecture-context.md).

select
    listing_key,
    source_name,
    source_file,
    source_listing_id,
    url,
    city,
    neighborhood,
    neighborhood_recognized,
    property_type,
    bedrooms,
    bathrooms,
    bedrooms_is_bound,
    bathrooms_is_bound,
    furnished,
    parking,
    gated,
    area_m2,
    rent_price,
    currency,
    price_is_bound,
    is_republication,
    outlier_flags,
    posted_at,
    collected_at
from {{ ref('stg_listings') }}
