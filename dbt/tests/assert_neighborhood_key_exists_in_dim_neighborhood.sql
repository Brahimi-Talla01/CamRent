-- Test singulier : chaque paire (ville, quartier) des faits doit exister dans
-- `dim_neighborhood`. Le test générique `relationships` ne compare qu'une seule
-- colonne, or la clé de quartier est composite (`city || '|' || neighborhood`) :
-- la cohérence de la paire est donc contrôlée ici.
-- Le test passe s'il ne remonte aucune ligne.

with faits as (

    select distinct
        city,
        neighborhood
    from {{ ref('fct_rent_observations') }}

)

select
    faits.city,
    faits.neighborhood
from faits
left join {{ ref('dim_neighborhood') }} as dim
    on dim.city_name = faits.city
   and dim.neighborhood_name = faits.neighborhood
where dim.neighborhood_name is null
