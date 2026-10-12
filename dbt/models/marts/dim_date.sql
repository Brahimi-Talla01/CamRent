{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Dimension date : une ligne par date observée dans les données (date de
-- collecte ou de publication). Construite depuis les données réellement
-- collectées : pas de calendrier artificiel ni de filtration temporelle.
-- `collected_at` est de loin le plus complet (always present côté Phase 2) ;
-- `posted_at` est quasi absent (EDA Phase 3) et reste exposé brut dans
-- `fct_listings`.

with dates as (

    select distinct
        left(coalesce(posted_at, collected_at), 10)      as date_text
    from {{ ref('int_clean_listings') }}
    where coalesce(posted_at, collected_at) is not null

)

select
    date_text                                           as date_day,
    cast(left(date_text, 4) as integer)                  as year,
    cast(substring(date_text, 6, 2) as integer)          as month,
    cast(substring(date_text, 9, 2) as integer)          as day
from dates
