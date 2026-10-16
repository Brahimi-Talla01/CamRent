-- Test singulier : contrôle des bornes de pièces (règle de la Phase 2, spec 02 §12).
-- `pipelines/silver.py::_outlier_flags` signale — sans jamais supprimer — tout
-- `bedrooms` / `bathrooms` au-delà de `ROOMS_MAX_PLAUSIBLE` (10 par défaut).
-- Exemple réel conservé : `bathrooms = 80` (3 observations), signalées
-- `bathrooms_outlier`.
-- Le test échoue si une valeur hors bornes apparaît dans le dépôt **sans** son
-- drapeau : la valeur resterait alors publiée comme plausible, ce qui est
-- exactement le risque identifié par l'audit (P3). Il ne remonte aucune ligne
-- quand la règle est appliquée.
-- Le test passe s'il ne remonte aucune ligne.

{% set borne = var('rooms_max_plausible', 10) %}

with observations as (

    select
        listing_key,
        bedrooms,
        bathrooms,
        outlier_flags
    from {{ ref('fct_rent_observations') }}

)

select
    listing_key,
    case
        when bedrooms > {{ borne }} and bathrooms > {{ borne }} then 'bedrooms et bathrooms'
        when bedrooms > {{ borne }} then 'bedrooms'
        else 'bathrooms'
    end                                             as colonne_hors_bornes,
    bedrooms,
    bathrooms,
    outlier_flags
from observations
where
    (bedrooms > {{ borne }} and coalesce(outlier_flags, '') not like '%bedrooms_outlier%')
    or (bathrooms > {{ borne }} and coalesce(outlier_flags, '') not like '%bathrooms_outlier%')
