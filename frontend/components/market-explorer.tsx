"use client";

/**
 * Écran d'exploration du marché (`/explorer`, ticket 09a.3, spec 09 §5).
 *
 * Les filtres vivent **dans l'URL** (`?city=…&neighborhood=…&property_type=…&bedrooms=…`) :
 * un état de l'écran est donc partageable, et chaque combinaison (quartier
 * publié, groupe sous le seuil, filtre sans résultat) est vérifiable dans un
 * navigateur réel. Le composant ne calcule aucune statistique : il lit les
 * marts via `/market/neighborhoods` (synthèse par quartier) et
 * `/market/prices` (détail quartier × type × chambres), et applique les règles
 * d'affichage :
 *
 * - **N toujours visible**, aucune statistique sans nombre d'observations ;
 * - **médiane jamais affichée sous le seuil**, même si une réponse
 *   incohérente la proposait (`medianDisplay` revérifie) ;
 * - **aucun chiffre inventé** : un filtre vide l'annonce, un échec de l'API
 *   vide la table au lieu de garder des chiffres périmés ;
 * - les biais connus (prix bornés, republications, quartiers non reconnus)
 *   sont signalés au niveau agrégé, avec leur volume.
 */

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { apiGet } from "@/lib/api";
import type {
  CitiesResponse,
  NeighborhoodMarket,
  NeighborhoodsResponse,
  PriceGroup,
  PricesResponse,
} from "@/lib/api-types";
import {
  emptyStateMessage,
  explorerHref,
  hasActiveFilters,
  medianDisplay,
  neighborhoodsPath,
  parseExplorerFilters,
  pricesPath,
  qualityNotes,
  type ExplorerFilters,
} from "@/lib/explorer";
import {
  formatCount,
  formatDate,
  formatFcfa,
  formatRange,
  formatShare,
} from "@/lib/format";
import {
  CITIES,
  PROPERTY_TYPES,
  bedroomsLabel,
  propertyTypeLabel,
  roomChoices,
} from "@/lib/vocabulary";

const CITIES_PATH = "/api/v1/market/cities";

const MARKET_UNAVAILABLE =
  "Les statistiques de marché sont momentanément indisponibles. Aucun chiffre n'est " +
  "affiché plutôt qu'un chiffre approximatif : réessayez dans un instant.";

type ExplorerTable =
  | { key: string; kind: "neighborhoods"; data: NeighborhoodsResponse }
  | { key: string; kind: "groups"; data: PricesResponse };

function EmptyState({
  filters,
  onReset,
}: {
  filters: ExplorerFilters;
  onReset: () => void;
}) {
  return (
    <div className="empty-state">
      <p>
        <strong>{emptyStateMessage(filters)}</strong> Aucune statistique n&apos;est
        approchée depuis un autre quartier, un autre type ou une autre ville.
      </p>
      <button className="button button--secondary" type="button" onClick={onReset}>
        Retirer les filtres
      </button>
    </div>
  );
}

function NeighborhoodRow({
  item,
  onSelect,
}: {
  item: NeighborhoodMarket;
  onSelect: (name: string) => void;
}) {
  return (
    <tr>
      <td>
        {item.neighborhood}
        {!item.neighborhood_recognized && (
          <span className="table-note">Libellé non reconnu</span>
        )}
      </td>
      <td className="tabular numeric">{formatCount(item.stats.n_observations)}</td>
      <td className="tabular numeric">{formatFcfa(item.stats.mean_rent_price)}</td>
      <td className="tabular numeric">
        {formatRange(item.stats.min_rent_price, item.stats.max_rent_price)}
      </td>
      <td className="tabular numeric">{formatCount(item.n_groups)}</td>
      <td>
        <button
          className="link-button"
          type="button"
          onClick={() => onSelect(item.neighborhood)}
        >
          Détail
        </button>
      </td>
    </tr>
  );
}

function GroupRow({ group, minPublishN }: { group: PriceGroup; minPublishN: number }) {
  const median = medianDisplay(group.stats, minPublishN);
  const range =
    group.stats.p10_rent_price !== null && group.stats.p90_rent_price !== null
      ? formatRange(group.stats.p10_rent_price, group.stats.p90_rent_price)
      : "Non disponible";

  return (
    <tr>
      <td>{propertyTypeLabel(group.property_type)}</td>
      <td>{group.bedrooms === null ? "Non renseigné" : bedroomsLabel(group.bedrooms)}</td>
      <td className="tabular numeric">{formatCount(group.stats.n_observations)}</td>
      <td className="tabular numeric">{formatFcfa(group.stats.mean_rent_price)}</td>
      <td className="tabular numeric">
        {median.published ? (
          formatFcfa(median.amount)
        ) : (
          <span className="median--hidden">
            Non publiée
            {median.belowThreshold && ` (< ${minPublishN} obs.)`}
          </span>
        )}
      </td>
      <td className="tabular numeric">{range}</td>
    </tr>
  );
}

export function MarketExplorer() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const search = searchParams.toString();
  const filters = useMemo(
    () => parseExplorerFilters(new URLSearchParams(search)),
    [search],
  );
  const requestKey = explorerHref(filters);

  const [cities, setCities] = useState<CitiesResponse | null>(null);
  const [citiesFailure, setCitiesFailure] = useState(false);
  const [neighborhoodList, setNeighborhoodList] =
    useState<NeighborhoodsResponse | null>(null);
  const [neighborhoodListFailureCity, setNeighborhoodListFailureCity] = useState<
    string | null
  >(null);

  const [table, setTable] = useState<ExplorerTable | null>(null);
  const [failure, setFailure] = useState<{ key: string; message: string } | null>(
    null,
  );

  // Villes, période et biais : une seule lecture, indépendante des filtres.
  useEffect(() => {
    let cancelled = false;
    apiGet<CitiesResponse>(CITIES_PATH)
      .then((data) => {
        if (!cancelled) {
          setCities(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCitiesFailure(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Liste des quartiers de la ville : sans filtre, pour que le sélecteur reste
  // complet même quand un type ou un nombre de chambres réduit la table.
  useEffect(() => {
    let cancelled = false;
    const city = filters.city;
    apiGet<NeighborhoodsResponse>(
      neighborhoodsPath({
        city,
        neighborhood: null,
        propertyType: null,
        bedrooms: null,
      }),
    )
      .then((data) => {
        if (!cancelled && data.city === city) {
          setNeighborhoodList(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setNeighborhoodListFailureCity(city);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [filters.city]);

  // Table du filtre courant : synthèse par quartier, ou détail d'un quartier.
  // Une réponse arrivée après un changement de filtre est ignorée : l'écran ne
  // mélange jamais deux combinaisons.
  useEffect(() => {
    let cancelled = false;
    const key = requestKey;
    const detailPath = pricesPath(filters);

    const request = detailPath
      ? apiGet<PricesResponse>(detailPath).then((data) => ({
          kind: "groups" as const,
          data,
        }))
      : apiGet<NeighborhoodsResponse>(neighborhoodsPath(filters)).then((data) => ({
          kind: "neighborhoods" as const,
          data,
        }));

    request
      .then((result) => {
        if (!cancelled) {
          setTable({ key, ...result });
          setFailure(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setTable(null);
          setFailure({ key, message: MARKET_UNAVAILABLE });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [filters, requestKey]);

  const currentTable = table !== null && table.key === requestKey ? table : null;
  const currentFailure = failure !== null && failure.key === requestKey ? failure.message : null;
  const loading = currentTable === null && currentFailure === null;

  const cityStats = cities?.cities.find((item) => item.city === filters.city) ?? null;
  const minPublishN = currentTable?.data.min_publish_n ?? cities?.min_publish_n ?? 30;
  const options =
    neighborhoodList !== null && neighborhoodList.city === filters.city
      ? neighborhoodList.neighborhoods.map((item) => item.neighborhood)
      : [];

  function applyFilters(next: Partial<ExplorerFilters>) {
    router.replace(explorerHref({ ...filters, ...next }), { scroll: false });
  }

  const resetFilters = () => {
    applyFilters({ neighborhood: null, propertyType: null, bedrooms: null });
  };

  return (
    <div className="explorer">
      <form className="filter-bar" aria-label="Filtres d'exploration">
        <div className="field">
          <label className="field__label" htmlFor="explorer-ville">
            Ville
          </label>
          <select
            id="explorer-ville"
            className="field__input"
            value={filters.city}
            onChange={(event) => applyFilters({ city: event.target.value, neighborhood: null })}
          >
            {CITIES.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="explorer-quartier">
            Quartier
          </label>
          <select
            id="explorer-quartier"
            className="field__input"
            value={filters.neighborhood ?? ""}
            onChange={(event) =>
              applyFilters({
                neighborhood: event.target.value === "" ? null : event.target.value,
              })
            }
          >
            <option value="">Tous les quartiers</option>
            {options.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          {neighborhoodListFailureCity === filters.city && (
            <p className="field__hint">
              Liste des quartiers momentanément indisponible : la table reste lisible,
              le filtre de quartier est désactivé.
            </p>
          )}
        </div>

        <div className="field">
          <label className="field__label" htmlFor="explorer-type">
            Type de bien
          </label>
          <select
            id="explorer-type"
            className="field__input"
            value={filters.propertyType ?? ""}
            onChange={(event) =>
              applyFilters({
                propertyType: event.target.value === "" ? null : event.target.value,
              })
            }
          >
            <option value="">Tous les types</option>
            {PROPERTY_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label className="field__label" htmlFor="explorer-chambres">
            Chambres
          </label>
          <select
            id="explorer-chambres"
            className="field__input"
            value={filters.bedrooms === null ? "" : String(filters.bedrooms)}
            onChange={(event) =>
              applyFilters({
                bedrooms:
                  event.target.value === "" ? null : Number(event.target.value),
              })
            }
          >
            <option value="">Toutes</option>
            {roomChoices().map((count) => (
              <option key={count} value={count}>
                {count}
              </option>
            ))}
          </select>
        </div>

        {hasActiveFilters(filters) && (
          <div className="field filter-bar__reset">
            <button className="button button--secondary" type="button" onClick={resetFilters}>
              Retirer les filtres
            </button>
          </div>
        )}
      </form>

      <div className="explorer__results" aria-live="polite">
        {currentFailure !== null && (
          <div className="notice notice--warning" role="alert">
            <h2>Statistiques indisponibles</h2>
            <p>{currentFailure}</p>
          </div>
        )}

        {loading && <p className="small muted">Chargement des statistiques…</p>}

        {currentTable?.kind === "neighborhoods" && (
          <section aria-labelledby="quartiers-titre">
            <h2 id="quartiers-titre">Quartiers observés — {currentTable.data.city}</h2>
            <p className="small muted">
              {formatCount(currentTable.data.n_neighborhoods)} quartiers et{" "}
              {formatCount(currentTable.data.n_observations)} observations pour ce filtre.
              La médiane n&apos;est pas agrégée au niveau quartier : choisissez un quartier
              pour la voir par type et nombre de chambres.
            </p>
            {currentTable.data.neighborhoods.length === 0 ? (
              <EmptyState filters={filters} onReset={resetFilters} />
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <caption className="visually-hidden">
                    Statistiques par quartier, avec leur nombre d&apos;observations
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Quartier</th>
                      <th scope="col" className="numeric">Observations</th>
                      <th scope="col" className="numeric">Prix moyen demandé</th>
                      <th scope="col" className="numeric">Minimum – maximum</th>
                      <th scope="col" className="numeric">Groupes</th>
                      <th scope="col">
                        <span className="visually-hidden">Détail</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentTable.data.neighborhoods.map((item) => (
                      <NeighborhoodRow
                        key={item.neighborhood}
                        item={item}
                        onSelect={(name) => applyFilters({ neighborhood: name })}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {currentTable?.kind === "groups" && (
          <section aria-labelledby="detail-titre">
            <h2 id="detail-titre">Détail du quartier : {filters.neighborhood}</h2>
            <p className="small muted">
              Détail par type de bien et nombre de chambres, au grain réellement observé.
              Chaque ligne porte son nombre d&apos;observations ; une médiane n&apos;est
              publiée qu&apos;à partir de {minPublishN} observations.
            </p>
            {currentTable.data.groups.length === 0 ? (
              <EmptyState filters={filters} onReset={resetFilters} />
            ) : (
              <>
                <div className="table-wrap">
                  <table className="data-table">
                    <caption className="visually-hidden">
                      Statistiques de {filters.neighborhood}, avec nombre d&apos;observations,
                      moyenne, médiane publiée et centiles 10–90
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Type</th>
                        <th scope="col">Chambres</th>
                        <th scope="col" className="numeric">Observations</th>
                        <th scope="col" className="numeric">Prix moyen</th>
                        <th scope="col" className="numeric">Prix médian</th>
                        <th scope="col" className="numeric">p10 – p90</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentTable.data.groups.map((group) => (
                        <GroupRow
                          key={`${group.property_type}-${String(group.bedrooms)}`}
                          group={group}
                          minPublishN={minPublishN}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="table-legend small muted">
                  {formatCount(currentTable.data.n_observations)} observations au total.{" "}
                  {currentTable.data.groups.filter((group) => !group.neighborhood_recognized)
                    .length > 0 &&
                    "Certaines lignes portent un libellé de quartier non reconnu : " +
                      "le rapprochement au référentiel n'a pas pu être fait."}
                </p>
              </>
            )}
          </section>
        )}

        {currentTable !== null && cityStats !== null && (
          <aside className="notice notice--warning explorer__limits" aria-labelledby="limites-titre">
            <h2 id="limites-titre">Limites de la donnée — {filters.city}</h2>
            <ul className="list-check list-check--warning">
              {qualityNotes(cityStats.quality).map((note) => (
                <li key={note.key}>
                  {note.label} : {formatCount(note.count)} observations (
                  {formatShare(note.percent)})
                </li>
              ))}
              <li>
                Période observée : du {formatDate(cities?.observed_period.start)} au{" "}
                {formatDate(cities?.observed_period.end)} — seule période disponible.
              </li>
              <li>
                Médiane publiée à partir de {minPublishN} observations ; en dessous, le N et
                la moyenne restent affichés, jamais une médiane.
              </li>
              <li>
                Prix <strong>demandés</strong> dans les annonces, jamais des prix payés.
              </li>
            </ul>
            {qualityNotes(cityStats.quality).length === 0 && (
              <p className="small muted">Aucun biais connu signalé pour cette ville.</p>
            )}
          </aside>
        )}

        {currentTable !== null && citiesFailure && (
          <p className="small muted">
            Limites de la donnée momentanément indisponibles : les statistiques affichées
            restent celles des marts.
          </p>
        )}
      </div>
    </div>
  );
}
