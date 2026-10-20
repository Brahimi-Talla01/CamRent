/**
 * Rappel permanent des limites : prix **demandés**, fourchette obligatoire,
 * nombre d'observations. Le pied de page ne présente aucun chiffre.
 */
export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__inner">
        <div>
          <p>
            CamRent estime un loyer mensuel <strong>demandé</strong> dans les annonces, à
            Yaoundé et Douala. Ce n&apos;est pas une valeur officielle du bien : c&apos;est une
            indication, toujours accompagnée d&apos;une fourchette.
          </p>
          <p>
            Chaque statistique de marché affiche son nombre d&apos;observations. Une médiane
            n&apos;est publiée qu&apos;au-delà du seuil fixé par la plateforme de données.
          </p>
        </div>
        <div>
          <p>
            Données : annonces immobilières publiques, nettoyées et agrégées. Prix demandés,
            jamais des prix payés.
          </p>
        </div>
      </div>
    </footer>
  );
}
