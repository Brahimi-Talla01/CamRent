{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Statistiques de marché par ville — utilisée par l'API `/market/cities`.
-- Grain : une ligne par ville. N d'observations toujours présent (invariant 8).
-- Aucune exclusion : républications et prix bornés restent comptés, avec
-- visibilité via `pct_price_bound`.

select
    city_key                                                    as city,
    count(*)                                                     as n_observations,
    round(avg(rent_price))::bigint                               as mean_rent_price,
    percentile_cont(0.5) within group (order by rent_price)::bigint as median_rent_price,
    percentile_cont(0.10) within group (order by rent_price)::bigint as p10_rent_price,
    percentile_cont(0.90) within group (order by rent_price)::bigint as p90_rent_price,
    min(rent_price)::bigint                                      as min_rent_price,
    max(rent_price)::bigint                                      as max_rent_price,
    sum(case when price_is_bound then 1 else 0 end)::bigint      as n_price_bound,
    round(
        100.0 * sum(case when price_is_bound then 1 else 0 end) / count(*)
    )::float                                                     as pct_price_bound
from {{ ref('fct_rent_observations') }}
group by city_key
