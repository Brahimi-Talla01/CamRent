{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Statistiques de marché par type de logement (grain : type × ville).
-- N d'observations toujours présent (invariant 8).

select
    property_type_key                                          as property_type,
    city_key                                                    as city,
    count(*)                                                     as n_observations,
    round(avg(rent_price))::bigint                               as mean_rent_price,
    percentile_cont(0.5) within group (order by rent_price)::bigint as median_rent_price,
    min(rent_price)::bigint                                      as min_rent_price,
    max(rent_price)::bigint                                      as max_rent_price
from {{ ref('fct_rent_observations') }}
group by property_type_key, city_key
