{{
    config(
        materialized='table',
        schema='marts',
    )
}}

-- Fait des observations de loyer.
-- Grain : une ligne par observation Silver (aucune agrégation, aucune
-- suppression). Les clés techniques référencent les dimensions.
-- sizeable indicators : les drapeaux (prix borné, républication, aberrations,
-- quartier non reconnu) restent publics car ils décrivent la fiabilité de
-- chaque observation — exigence produit d'exposition de l'incertitude.

select
    listing_key,
    city                                                 as city_key,
    city || '|' || neighborhood                          as neighborhood_key,
    property_type                                        as property_type_key,
    -- Libellés bruts conservés en plus des clés : les marts agrègent dessus
    -- et l'API expose des noms lisibles (« Makepe »), pas des clés composées.
    city,
    neighborhood,
    property_type,
    left(coalesce(posted_at, collected_at), 10)          as date_day,
    bedrooms,
    bathrooms,
    bedrooms_is_bound,
    bathrooms_is_bound,
    area_m2,
    rent_price,
    currency,
    price_is_bound,
    is_republication,
    outlier_flags,
    neighborhood_recognized,
    source_name,
    source_file,
    source_listing_id,
    url
from {{ ref('int_clean_listings') }}
