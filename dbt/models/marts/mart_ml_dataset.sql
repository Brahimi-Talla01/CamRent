{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Dataset ML : features du MVP + cible `rent_price` (Prix **demandé** dans
-- l'annonce, pas prix payé) + la sémantique explicite de cette cible
-- (`rent_semantics`, décision du 2026-10-15). Grain : une ligne par observation
-- Silver.
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
    -- Sémantique de la cible, explicite dans les données (décision 9) :
    -- `asking_rent` = loyer demandé dans une annonce ; `unknown` = sémantique
    -- non établie. Le Silver ne conserve que des lignes dont le prix est celui
    -- de l'annonce (les prix manquants partent en quarantaine) : toutes les
    -- lignes actuelles sont donc `asking_rent`. La colonne existe pour que la
    -- sémantique soit **lue dans les données**, jamais supposée — et pour
    -- permettre à une future source de rester `unknown` plutôt que d'être
    -- silencieusement présentée comme un loyer demandé.
    case
        when rent_price is not null then 'asking_rent'
        else 'unknown'
    end                                                          as rent_semantics,
    currency,
    price_is_bound,
    bedrooms_is_bound,
    bathrooms_is_bound,
    is_republication,
    outlier_flags,
    source_name,
    collected_at
from {{ ref('int_clean_listings') }}
