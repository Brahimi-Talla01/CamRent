{{ config(materialized='table', schema='marts') }}

-- Qualité des données : **motifs de rejet agrégés** par source (lot B du plan
-- de réalignement, support du module « Qualité » du back-office et de la
-- Phase 11).
-- Grain : une ligne par (source, motif de rejet).
--
-- Invariant 8 : chaque ligne porte son nombre de rejets, et le total des rejets
-- de la source est exposé à côté de la part — jamais un pourcentage seul.
-- Aucun rejet n'est masqué : les lignes de `stg_quarantine` sont toutes comptées
-- (le test singulier `assert_data_quality_motifs_sum_to_quarantine_total`
-- garantit que la somme des motifs égale la quarantaine réelle).

with quarantine as (

    select
        source_name,
        quarantine_reason
    from {{ ref('stg_quarantine') }}

),

by_source as (

    select
        source_name,
        count(*)::bigint as n_rejections_source
    from quarantine
    group by source_name

),

by_motif as (

    select
        source_name,
        quarantine_reason,
        count(*)::bigint as n_rejections
    from quarantine
    group by source_name, quarantine_reason

)

select
    motifs.source_name,
    motifs.quarantine_reason,
    motifs.n_rejections,
    totaux.n_rejections_source,
    round(100.0 * motifs.n_rejections / totaux.n_rejections_source)::float
                                                                     as pct_of_source_rejections
from by_motif as motifs
join by_source as totaux
    on motifs.source_name = totaux.source_name
