{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Dimension types de logement : une ligne par type canonique
-- (studio, apartment, house, office, shop, warehouse, room, land).
-- `n_observations` embarqué pour la transparence (invariant 8).

select
    property_type                                       as property_type_name,
    count(*)                                            as n_observations,
    min(rent_price)                                     as min_rent_price,
    max(rent_price)                                     as max_rent_price
from {{ ref('int_clean_listings') }}
group by property_type
