"use client";

/**
 * Formulaire d'estimation (`/estimer`, ticket 09a.2, spec 09 §3-4).
 *
 * Seul composant client du parcours à ce stade : il porte la saisie. Cinq
 * champs, **exactement ceux que le modèle exploite** (ville, quartier, type,
 * chambres, salles de bain) — demander `area_m2`, `parking` ou `meublé`
 * laisserait croire que l'estimation en tient compte (décision 6).
 *
 * Le résultat affiche toujours : l'estimation **avec sa fourchette**, la
 * version du modèle, puis le contexte de marché du groupe (N, moyenne,
 * médiane et seuil de publication, p10-p90). Aucun chiffre n'est inventé : un
 * groupe sans observation est annoncé comme tel.
 */

import { useEffect, useState, type FormEvent } from "react";

import { apiGet, apiPost, ApiError } from "@/lib/api";
import {
  estimationFailureMessage,
  fieldErrorsFromDetails,
  type FieldErrors,
} from "@/lib/estimation-errors";
import type {
  NeighborhoodsResponse,
  PredictionRequest,
  PredictionResponse,
  PricesResponse,
} from "@/lib/api-types";
import { formatFcfa, formatRange } from "@/lib/format";
import {
  findMarketGroup,
  marketPricesUrl,
  neighborhoodOptions,
  neighborhoodsUrl,
} from "@/lib/market";

const CITIES = ["Douala", "Yaoundé"] as const;

const PROPERTY_TYPES = [
  { value: "apartment", label: "Appartement" },
  { value: "studio", label: "Studio" },
  { value: "room", label: "Chambre (room)" },
  { value: "house", label: "Maison" },
] as const;

const ROOMS_MIN = 0;
const ROOMS_MAX = 10;

/** Analyse un nombre de pièces saisi ; l'erreur est portée par `errors`. */
function parseRooms(
  value: string,
  label: string,
  errors: FieldErrors,
  field: keyof FieldErrors,
): number | null {
  const parsed = Number(value);
  if (value.trim() === "" || !Number.isInteger(parsed)) {
    errors[field] = `${label} : nombre entier obligatoire.`;
    return null;
  }
  if (parsed < ROOMS_MIN || parsed > ROOMS_MAX) {
    errors[field] = `${label} : entre ${ROOMS_MIN} et ${ROOMS_MAX}.`;
    return null;
  }
  return parsed;
}

export function EstimationForm() {
  const [city, setCity] = useState<string>("Douala");
  const [neighborhood, setNeighborhood] = useState("");
  const [propertyType, setPropertyType] = useState<string>("apartment");
  const [bedrooms, setBedrooms] = useState("2");
  const [bathrooms, setBathrooms] = useState("1");

  const [neighborhoods, setNeighborhoods] = useState<NeighborhoodsResponse | null>(null);
  const [neighborhoodsUnavailable, setNeighborhoodsUnavailable] = useState(false);

  const [pending, setPending] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [banner, setBanner] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [market, setMarket] = useState<PricesResponse | null>(null);

  // Les quartiers viennent des marts (`/market/neighborhoods?city=…`). Une
  // réponse périmée (changement de ville pendant l'aller-retour) est jetée :
  // elle porte sa ville, on ne fait pas confiance à l'ordre d'arrivée. L'effet
  // appelle `setState` uniquement dans un callback : le reset de la liste
  // précédente se fait dans le handler du changement de ville.
  useEffect(() => {
    let cancelled = false;

    apiGet<NeighborhoodsResponse>(neighborhoodsUrl(city))
      .then((data) => {
        if (cancelled) {
          return;
        }
        if (data.city === city) {
          setNeighborhoods(data);
        } else {
          setNeighborhoodsUnavailable(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setNeighborhoodsUnavailable(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [city]);

  const options = neighborhoods ? neighborhoodOptions(neighborhoods) : [];
  const minPublishN = neighborhoods?.min_publish_n ?? 30;
  const listedCount = neighborhoods?.n_neighborhoods ?? 0;
  const groupBedrooms = Number(bedrooms);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBanner(null);
    setPrediction(null);
    setMarket(null);

    const errors: FieldErrors = {};
    const bedroomsValue = parseRooms(bedrooms, "Chambres", errors, "bedrooms");
    const bathroomsValue = parseRooms(bathrooms, "Salles de bain", errors, "bathrooms");
    if (neighborhood.trim() === "") {
      errors.neighborhood = "Le quartier du logement est obligatoire.";
    }
    setFieldErrors(errors);
    if (bedroomsValue === null || bathroomsValue === null || neighborhood.trim() === "") {
      return;
    }

    const payload: PredictionRequest = {
      city,
      neighborhood: neighborhood.trim(),
      property_type: propertyType,
      bedrooms: bedroomsValue,
      bathrooms: bathroomsValue,
    };

    setPending(true);
    try {
      // Les deux lectures partent en parallèle : l'estimation (modèle) et le
      // contexte de marché (marts). Un échec de contexte n'empêche pas le
      // résultat : seul le bloc marché s'en trouve réduit.
      const [predictionResult, marketResult] = await Promise.allSettled([
        apiPost<PredictionResponse>("/api/v1/predictions", payload),
        apiGet<PricesResponse>(marketPricesUrl(payload)),
      ]);

      if (predictionResult.status === "rejected") {
        const failure = predictionResult.reason;
        setPrediction(null);
        if (failure instanceof ApiError && failure.status === 422 && failure.details.length > 0) {
          setFieldErrors(fieldErrorsFromDetails(failure.details));
        } else {
          setBanner(estimationFailureMessage(failure));
        }
        return;
      }

      setPrediction(predictionResult.value);
      setFieldErrors({});
      setMarket(marketResult.status === "fulfilled" ? marketResult.value : null);
    } finally {
      setPending(false);
    }
  }

  const marketGroup = market
    ? findMarketGroup(market, { property_type: propertyType, bedrooms: groupBedrooms })
    : null;

  return (
    <div className="estimation">
      <form className="form-grid" onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label className="field__label" htmlFor="estimer-ville">
            Ville
          </label>
          <select
            id="estimer-ville"
            className="field__input"
            value={city}
            onChange={(event) => {
              setCity(event.target.value);
              setNeighborhood("");
              // Reset immédiat de la liste périmée (et non plus dans l'effet,
              // dont seul le retour asynchrone doit écrire l'état).
              setNeighborhoods(null);
              setNeighborhoodsUnavailable(false);
            }}
          >
            {CITIES.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          <p className="field__hint">Marché couvert par les données actuelles : Yaoundé et Douala.</p>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="estimer-quartier">
            Quartier
          </label>
          <input
            id="estimer-quartier"
            className="field__input"
            type="text"
            list="estimer-options"
            maxLength={120}
            value={neighborhood}
            onChange={(event) => setNeighborhood(event.target.value)}
            aria-invalid={fieldErrors.neighborhood !== undefined}
            aria-describedby={
              fieldErrors.neighborhood !== undefined ? "estimer-quartier-erreur" : undefined
            }
          />
          <datalist id="estimer-options">
            {options.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
          {fieldErrors.neighborhood !== undefined ? (
            <p className="field__error" id="estimer-quartier-erreur">
              {fieldErrors.neighborhood}
            </p>
          ) : neighborhoodsUnavailable ? (
            <p className="field__hint">
              Liste des quartiers momentanément indisponible : saisissez le quartier tel
              qu&apos;annoncé.
            </p>
          ) : (
            <p className="field__hint">
              {listedCount > 0
                ? `${listedCount} quartiers observés dans les données pour ${city} — choisissez-en un ou saisissez le vôtre.`
                : "Saisissez le quartier tel qu'annoncé dans l'offre."}
            </p>
          )}
        </div>

        <div className="field">
          <label className="field__label" htmlFor="estimer-type">
            Type de bien
          </label>
          <select
            id="estimer-type"
            className="field__input"
            value={propertyType}
            onChange={(event) => setPropertyType(event.target.value)}
          >
            {PROPERTY_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          <p className="field__hint">Types vraiment représentés dans les données collectées.</p>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="estimer-chambres">
            Chambres
          </label>
          <input
            id="estimer-chambres"
            className="field__input"
            type="number"
            inputMode="numeric"
            min={ROOMS_MIN}
            max={ROOMS_MAX}
            step={1}
            required
            value={bedrooms}
            onChange={(event) => setBedrooms(event.target.value)}
            aria-invalid={fieldErrors.bedrooms !== undefined}
            aria-describedby={
              fieldErrors.bedrooms !== undefined ? "estimer-chambres-erreur" : undefined
            }
          />
          {fieldErrors.bedrooms !== undefined && (
            <p className="field__error" id="estimer-chambres-erreur">
              {fieldErrors.bedrooms}
            </p>
          )}
        </div>

        <div className="field">
          <label className="field__label" htmlFor="estimer-sdb">
            Salles de bain
          </label>
          <input
            id="estimer-sdb"
            className="field__input"
            type="number"
            inputMode="numeric"
            min={ROOMS_MIN}
            max={ROOMS_MAX}
            step={1}
            required
            value={bathrooms}
            onChange={(event) => setBathrooms(event.target.value)}
            aria-invalid={fieldErrors.bathrooms !== undefined}
            aria-describedby={
              fieldErrors.bathrooms !== undefined ? "estimer-sdb-erreur" : undefined
            }
          />
          {fieldErrors.bathrooms !== undefined && (
            <p className="field__error" id="estimer-sdb-erreur">
              {fieldErrors.bathrooms}
            </p>
          )}
        </div>

        <div className="field field__submit">
          <button className="button button--primary" type="submit" disabled={pending}>
            {pending ? "Estimation en cours…" : "Estimer mon loyer"}
          </button>
          <p className="field__hint">
            Aucune donnée personnelle n&apos;est demandée ni envoyée : cinq caractéristiques, rien
            de plus.
          </p>
        </div>
      </form>

      {fieldErrors.form !== undefined && (
        <p className="field__error" role="alert">
          {fieldErrors.form}
        </p>
      )}

      <div aria-live="polite" className="estimation__outcomes">
        {banner !== null && (
          <div className="notice notice--warning" role="alert">
            <h2>Estimation refusée</h2>
            <p>{banner}</p>
          </div>
        )}

        {prediction !== null && (
          <article className="card result" aria-labelledby="resultat-titre">
            <span className="badge">Résultat</span>
            <h2 id="resultat-titre">Loyer mensuel estimé</h2>
            <p className="result__amount">{formatFcfa(prediction.estimated_rent)}</p>
            <dl className="result__grid">
              <div>
                <dt>Fourchette estimée</dt>
                <dd>{formatRange(prediction.lower_bound, prediction.upper_bound)}</dd>
              </div>
              <div>
                <dt>Unité</dt>
                <dd>{prediction.currency === "XAF" ? "FCFA / mois" : prediction.currency}</dd>
              </div>
              <div>
                <dt>Modèle</dt>
                <dd>{prediction.model_version}</dd>
              </div>
            </dl>
            <p className="result__market-notice">
              Loyer <strong>demandé</strong> dans les annonces, estimé par le modèle épinglé : ce
              n&apos;est pas la valeur officielle du bien, la fourchette est là pour en juger.
            </p>
          </article>
        )}

        {prediction !== null && market === null && (
          <p className="small muted">
            Contexte de marché momentanément indisponible. L&apos;estimation reste affichée sans la
            référence du quartier.
          </p>
        )}

        {prediction !== null && market !== null && marketGroup === null && (
          <div className="notice">
            <h2>Pas de référence de marché pour ce groupe</h2>
            <p>
              Aucune observation collectée pour ce quartier avec ce type et ce nombre de chambres :
              le contexte de marché n&apos;est pas affiché plutôt que simulé.
            </p>
          </div>
        )}

        {prediction !== null && marketGroup !== null && (
          <article className="card card--market" aria-labelledby="marche-titre">
            <span className="badge">Contexte de marché</span>
            <h2 id="marche-titre">Référence locale : {neighborhood.trim()}</h2>
            <dl className="result__grid">
              <div>
                <dt>Observations (N)</dt>
                <dd className="tabular">{marketGroup.stats.n_observations}</dd>
              </div>
              <div>
                <dt>Prix moyen demandé</dt>
                <dd>{formatFcfa(marketGroup.stats.mean_rent_price)}</dd>
              </div>
              <div>
                <dt>Prix médian demandé</dt>
                <dd>
                  {marketGroup.stats.median_published
                    ? formatFcfa(marketGroup.stats.median_rent_price)
                    : `Non publiée (moins de ${minPublishN} observations)`}
                </dd>
              </div>
              <div>
                <dt>Étendue p10 – p90</dt>
                <dd>
                  {marketGroup.stats.p10_rent_price !== null &&
                  marketGroup.stats.p90_rent_price !== null
                    ? formatRange(marketGroup.stats.p10_rent_price, marketGroup.stats.p90_rent_price)
                    : "Non disponible"}
                </dd>
              </div>
            </dl>
            <p className="small muted">
              Statistiques issues des marts de la plateforme de données, prix demandés dans les
              annonces. Médiane publiée à partir de {minPublishN} observations seulement.
            </p>
          </article>
        )}
      </div>
    </div>
  );
}
