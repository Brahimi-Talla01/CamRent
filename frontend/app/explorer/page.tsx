import type { Metadata } from "next";
import { Suspense } from "react";

import { MarketExplorer } from "@/components/market-explorer";

export const metadata: Metadata = {
  title: "Explorer le marché",
};

/**
 * Écran d'exploration (09a.3) : le socle de la page reste un composant serveur,
 * la partie interactive est isolée dans `MarketExplorer` sous `Suspense`
 * (lecture des filtres dans l'URL, donc rendu client après hydration).
 */
export default function ExplorerPage() {
  return (
    <div className="explorer-page">
      <header className="page-header">
        <span className="badge">Étape 2</span>
        <h1>Explorer le marché</h1>
        <p className="page-header__lead">
          Les prix <strong>demandés</strong> par quartier, type de logement et nombre de
          chambres, tels qu&apos;observés dans les annonces. Chaque statistique porte son
          nombre d&apos;observations ; une médiane n&apos;est publiée qu&apos;au-delà du seuil
          fixé par la plateforme de données, et son absence est expliquée.
        </p>
      </header>

      <Suspense fallback={<p className="small muted">Chargement des filtres…</p>}>
        <MarketExplorer />
      </Suspense>

      <aside className="notice notice--warning" aria-label="Ce que cet écran ne fait pas">
        <h2>Ce que cet écran ne prétend pas faire</h2>
        <ul className="list-check list-check--warning">
          <li>
            Aucun classement ni palmarès de quartiers : l&apos;outil informe, il ne désigne
            pas un « meilleur » quartier.
          </li>
          <li>
            Aucune recherche par budget et aucune cartographie fine : les coordonnées
            exploitables n&apos;existent pas encore dans les données.
          </li>
          <li>
            Aucun chiffre officiel : ce sont des prix demandés dans des annonces, pas des
            loyers payés ni une valeur garantie.
          </li>
        </ul>
      </aside>
    </div>
  );
}
