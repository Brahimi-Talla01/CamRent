{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Dimension quartiers : une ligne par (ville, quartier) canonique.
-- Le référentiel provient du seed curé pipelines/geo.py (issue #20) : aucun
-- mapping inventé. `n_observations` est embarqué pour repérer les volumes
-- faibles (seuils MIN_NEIGHBORHOOD_N / LOW_VOLUME_N côté EDA, Phase 3).

select distinct
    city                                                  as city_name,
    neighborhood                                          as neighborhood_name,
    neighborhood_recognized                               as is_canonical
from {{ ref('int_clean_listings') }}
