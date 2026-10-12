{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Fait des annonces : une ligne par observation Silver (grain identique à
-- `fct_rent_observations`, avec les attributs source bruts conservés pour la
-- traçabilité : url, source_file, source_listing_id — Plan Technique §29).
-- Séparer les deux faits reflète leurs usages distincts :
--   - fct_rent_observations → analyse de marché, dashes …
--   - fct_listings → traçabilité vers la source, rejeu/débogage.

select
    listing_key,
    city                                                 as city_key,
    city || '|' || neighborhood                          as neighborhood_key,
    property_type                                        as property_type_key,
    left(coalesce(posted_at, collected_at), 10)          as date_day,
    bedrooms,
    bathrooms,
    area_m2,
    rent_price,
    currency,
    price_is_bound,
    is_republication,
    outlier_flags,
    neighborhood_recognized,
    source_name,
    source_file,
    source_listing_id,
    url
from {{ ref('int_clean_listings') }}
