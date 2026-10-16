-- Test singulier : grain de `mart_data_quality`.
-- Le grain est (source, motif de rejet) : une combinaison dupliquée
-- fausserait la lecture des rejets (le nombre de rejets ne serait plus
-- attribuable à un motif unique).
-- Le test passe s'il ne remonte aucune ligne.

select
    source_name,
    quarantine_reason,
    count(*) as n_lignes
from {{ ref('mart_data_quality') }}
group by source_name, quarantine_reason
having count(*) > 1
