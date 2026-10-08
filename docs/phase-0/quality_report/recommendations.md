# Rapport de qualité — Recommandations

## 1. Collecte (Phase 1)

1. **Prioriser Koutchoumi + Geloka**, mais **lire leurs CGU** avant collecte (voir
   `../legal-assessment.md`).
2. Conserver, à chaque collecte, `source`, `source_listing_id`, `collected_at` — indispensables pour
   traiter doublons et republications.
3. **Cibler la surface et la date** : ce sont les deux champs manquants les plus critiques.
4. Ajouter des **features géo externes** (OpenStreetMap, INS) côté enrichissement.
5. Exclure dès la collecte les **données personnelles** (téléphone, e-mail, nom).
6. Limiter le débit de requêtes et respecter les CGU.

## 2. Nettoyage (Phase 2)

1. **Déduplication exacte** en premier (retire ≈ 1 839 lignes de Koutchoumi).
2. **Convertir** prix, chambres et salles de bain en entiers.
3. **Traiter les prix censurés** Koutchoumi (`"> X"`) explicitement : les exclure, ou les modéliser
   comme bornes (`rent_price >= X`). Ne pas les convertir en valeur exacte.
4. **Isoler / quarantine** : `Price = 0` ou `1`, `> 2 M`, `Bedrooms = 20`, `Bathrooms = 80`.
   Ne pas supprimer automatiquement.
5. Construire un **référentiel géographique** (ville → quartiers canoniques) pour fusionner
   `Akwa` / `Akwa I`, `Makepe` / `Makepe II`, etc.
6. Uniformiser les **libellés de type** FR/EN.

## 3. Produit

1. Communiquer clairement que l'estimation repose sur les **prix demandés** dans les annonces.
2. Ne pas exposer de statistique **sans son nombre d'observations**.
3. Ne pas proposer d'estimation **au m²** tant que la surface n'est pas collectée.

## 4. Gouvernance

1. Documenter chaque source (grain, fréquence, droits, limites).
2. Ne pas redistribuer le dataset tiers `deegeorgie` (sans licence).
3. Conserver la traçabilité : source → transformation → dataset analytique.
