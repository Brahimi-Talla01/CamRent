-- Test singulier : cohérence de `rent_semantics` avec la cible.
-- Règle (décision 9) : une observation dont le prix est celui de l'annonce est
-- étiquetée `asking_rent` ; une observation sans prix interprétable reste
-- `unknown`. Toute autre combinaison signalerait une sémantique supposée sans
-- preuve — ce qui rendrait la lecture du dataset trompeuse.
-- Le test passe s'il ne remonte aucune ligne.

select
    listing_key,
    target_rent_price,
    rent_semantics
from {{ ref('mart_ml_dataset') }}
where (target_rent_price is not null and rent_semantics <> 'asking_rent')
   or (target_rent_price is null and rent_semantics <> 'unknown')
