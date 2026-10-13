{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Dimension villes : une ligne par ville canonique du MVP.
-- Dérivée des observations (au MVP, seules Douala et Yaoundé sont en Silver) ;
-- le nombre d'observations est embarqué pour la transparence (invariant 8).

select
    initcap(city)                    as city_name,
    count(*)                         as n_observations,
    min(rent_price)                  as min_rent_price,
    max(rent_price)                  as max_rent_price
from {{ ref('int_clean_listings') }}
group by initcap(city)
