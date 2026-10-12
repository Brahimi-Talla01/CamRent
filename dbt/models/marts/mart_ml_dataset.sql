{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Dataset ML : features du MVP + cible `rent_price` (Prix **demandé** dans
-- l'annonce, pas prix payé). Grain : une ligne par observation Silver.
--
-- Garde-fous (code-standards.md §ML) :
-- - `rent_per_m2` est **interdit** comme feature (dépend directement de la
--   cible) : `area_m2` est exposé brut, la dérivation éventuelle sera faite
--   côté entraînement si la surface devient collectée ;
-- - aucune cible transformée ici (log1p décidé en Phase 5-6) ;
-- - les drapeaux qualité restent disponibles pour une pondération/exclusion
--   **explicite** côté entraînement (prix censurés, républications) — aucune
--   exclusion silencieuse dans les données.

select
    listing_key,
    city,
    neighborhood,
    neighborhood_recognized,
    property_type,
    bedrooms,
    bathrooms,
    furnished,
    parking,
    gated,
    area_m2,
    rent_price                                                   as target_rent_price,
    currency,
    price_is_bound,
    bedrooms_is_bound,
    bathrooms_is_bound,
    is_republication,
    outlier_flags,
    source_name,
    collected_at
from {{ ref('int_clean_listings') }}
