{{ config(materialized='table', schema='marts') }}

-- Lots de collecte et leur provenance (lot B du plan de réalignement §7.7).
-- Grain : une ligne par lot brut (fichier de `data/raw/metadata`).
--
-- Répond à « qu'a-t-on collecté, quand, avec quelle version du code, et ce lot
-- a-t-il été validé ? » sans relire `data/raw/` à la main — matière première du
-- module « Sources » du back-office.
-- `has_provenance` est faux pour les lots antérieurs à l'ajout de la version du
-- connecteur et de l'empreinte de contenu : l'absence est signalée, jamais
-- comblée par une valeur inventée.

select
    source_name,
    raw_file,
    category,
    method,
    format,
    collected_day,
    collected_at,
    record_count,
    n_urls,
    rights_status,
    connector_version,
    content_bytes,
    content_sha256,
    lot_validation_status,
    lot_validation_failures,
    has_provenance,
    notes
from {{ ref('stg_ingestion_runs') }}
