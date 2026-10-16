-- Test singulier : cohérence de la table de qualité.
-- La somme des motifs de rejet par source doit égaler le nombre réel
-- d'observations en quarantaine pour cette source — un rejet perdu dans
-- l'agrégation rendrait la qualité silencieusement optimiste (invariant 5).
-- Le test passe s'il ne remonte aucune ligne.

with par_source as (

    select
        source_name,
        sum(n_rejections) as n_rejections_agregees
    from {{ ref('mart_data_quality') }}
    group by source_name

),

quarantaine as (

    select
        source_name,
        count(*) as n_rejections_reelles
    from {{ ref('stg_quarantine') }}
    group by source_name

)

select
    quarantaine.source_name,
    quarantaine.n_rejections_reelles,
    coalesce(par_source.n_rejections_agregees, 0) as n_rejections_agregees
from quarantaine
left join par_source
    on quarantaine.source_name = par_source.source_name
where coalesce(par_source.n_rejections_agregees, 0) <> quarantaine.n_rejections_reelles
