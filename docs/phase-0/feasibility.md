# Verdict de faisabilité et décision de stack

**Phase :** 0 — Validation du problème

## 1. Verdict de faisabilité ML

### Alimentation du problème

| Critère | Évaluation | Commentaire |
|---|---|---|
| Volume | ⚠️ **Faible** | ≈ 1 226 lignes uniques réelles (après déduplication), très loin des « 3 068 » cités |
| Variables prédictives | ⚠️ **Limitées** | ville, quartier, type, chambres, sdb — **pas de surface**, pas d'équipements structurés |
| Qualité des labels (prix) | ⚠️ **Moyenne** | Koutchoumi : prix en **bornes** (`"> X"`) ; Jumia : 11 % sans prix |
| Fraîcheur | ❓ **Inconnue** | aucune date de publication dans les fichiers |
| Biais | ⚠️ **Oui** | Koutchoumi 98 % Douala ; sur-représentation de certains quartiers (Makepe, Bonapriso) |

### Conclusion

> Le problème ML est **partiellement alimenté**. L'échantillon actuel permet une **preuve de concept /
> baseline**, mais **pas** un modèle robuste. Un MVP crédible exige une **collecte supplémentaire** et
> une source fournissant **surface** et **dates**.

**Conséquence sur le périmètre :** le MVP doit rester volontairement réduit (quelques quartiers de
Douala/Yaoundé), et la surface ne peut pas être une variable du MVP tant qu'elle n'est pas collectée.

## 2. Décision de stack

Conformément au Plan Technique §71-74 et pour éviter le sur-engineering, la stack retenue est le
**Niveau 1 (prototype Data)** :

```
Python
CSV / Parquet
PostgreSQL
Pandas / Polars
scikit-learn
```

**Non introduits à ce stade :** MongoDB, Airflow, dbt, AWS/GCP, Data Warehouse, streaming.

Cela tranche la tension relevée entre le Data Discovery Report amont (§5.3 proposait MongoDB +
Airflow + dbt + AWS) et le Plan Technique (§71-74 : ne rien figer avant l'étude des données). Le
Plan Technique prévaut : l'infrastructure ne sera ajoutée qu'à sa phase et si le besoin est démontré.

## 3. Conditions à remplir avant de passer à la Phase 1

1. Décider de l'**origine de la collecte** (Koutchoumi / Geloka) et lire leurs **CGU**.
2. Construire un **référentiel géographique** (ville → quartiers canoniques) pour Yaoundé et Douala.
3. Définir la **stratégie vis-à-vis des prix censurés** de Koutchoumi (`"> X"`) : les exclure, ou les
   traiter comme des bornes (`rent_price >= X`).
4. Définir la **stratégie « surface »** : la collecter ailleurs, ou concevoir le MVP sans elle.
5. Statuer sur l'**usage du dataset `deegeorgie`** : strictement local (analyse) et non redistribué.
