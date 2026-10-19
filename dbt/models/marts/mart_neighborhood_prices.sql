{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Statistiques de marché par quartier — la table utilisée par l'exploration
-- « Explorer les prix » et par l'API `/market/neighborhoods`.
-- Grain : une ligne par (ville, quartier, type, chambres).
--
-- Aucune exclusion : républications et prix bornés restent comptés ; leurs
-- volumes et pourcentages (`n_republication`, `pct_price_bound`) rendent ces
-- biais visibles (invariant 8).

select
    city_key                                                    as city,
    neighborhood,
    neighborhood_recognized,
    property_type_key                                          as property_type,
    bedrooms,
    count(*)                                                     as n_observations,
    round(avg(rent_price))::bigint                               as mean_rent_price,
    case
        when count(*) >= {{ var('min_publish_n', 30) }} then percentile_cont(0.5)
            within group (order by rent_price)::bigint
    end                                                          as median_rent_price,
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
group by city_key, neighborhood, neighborhood_recognized, property_type_key, bedrooms
