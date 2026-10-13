-- Test singulier : invariant de publication des médianes (décision Phase 3,
-- invariant 8 d'architecture-context.md). La médiane d'un groupe de quartier
-- n'est publiée que si le groupe atteint le seuil `min_publish_n` ; en dessous,
-- le N reste visible mais la médiane est nulle.
-- Le test échoue si une médiane est publiée sous le seuil, ou absente au-dessus
-- (une régression silencieuse casserait la fiabilité des stats des Phases 5-6).
-- Le test passe s'il ne remonte aucune ligne.

{% set seuil = var('min_publish_n', 30) %}

select
    city,
    neighborhood,
    property_type,
    bedrooms,
    n_observations,
    median_rent_price
from {{ ref('mart_neighborhood_prices') }}
where (n_observations < {{ seuil }} and median_rent_price is not null)
   or (n_observations >= {{ seuil }} and median_rent_price is null)
