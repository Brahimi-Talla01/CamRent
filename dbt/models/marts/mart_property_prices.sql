{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Statistiques de marché par type de logement (grain : type × ville).
-- N d'observations toujours présent (invariant 8). Mêmes conventions que les
-- deux autres marts (fourchette p10/p90, qualité visible) pour que l'API de
-- marché expose la même forme quel que soit le niveau de filtre.

select
    property_type_key                                          as property_type,
    city_key                                                    as city,
    count(*)                                                     as n_observations,
    round(avg(rent_price))::bigint                               as mean_rent_price,
    percentile_cont(0.5) within group (order by rent_price)::bigint as median_rent_price,
    min(rent_price)::bigint                                      as min_rent_price,
    percentile_cont(0.10) within group (order by rent_price)::bigint as p10_rent_price,
    percentile_cont(0.90) within group (order by rent_price)::bigint as p90_rent_price,
    max(rent_price)::bigint                                      as max_rent_price,
    sum(case when price_is_bound then 1 else 0 end)::bigint      as n_price_bound,
    round(
        100.0 * sum(case when price_is_bound then 1 else 0 end) / count(*)
    )::float                                                     as pct_price_bound,
    sum(case when is_republication then 1 else 0 end)::bigint     as n_republication,
    round(
        100.0 * sum(case when is_republication then 1 else 0 end) / count(*)
    )::float                                                     as pct_republication
from {{ ref('fct_rent_observations') }}
group by property_type_key, city_key
