import Link from "next/link";

import { FlowCard } from "@/components/flow-card";

const FLOW_STEPS = [
  {
    step: "Étape 1",
    title: "Estimer mon loyer",
    description:
      "Ville, quartier, type de bien, chambres et salles de bain : cinq informations " +
      "seulement, celles que le modèle sait réellement exploiter.",
    href: "/estimer",
    status: "Formulaire livré avec le ticket 09a.2",
  },
  {
    step: "Étape 2",
    title: "Explorer le marché",
    description:
      "Prix moyen, médiane, fourchette et nombre d’observations par quartier et par type " +
      "de logement, sans mélanger deux niveaux de détail.",
    href: "/explorer",
    status: "Écran livré avec le ticket 09a.3",
  },
  {
    step: "Étape 3",
    title: "Comparer des logements",
    description:
      "Prix demandé, estimation et référence locale côte à côte, avec des écarts signés " +
      "et le nombre d’observations qui les soutient.",
    href: "/comparer",
    status: "Écran livré avec le ticket 09a.4",
  },
] as const;

export default function HomePage() {
  return (
    <>
      <section className="hero" aria-labelledby="accueil-titre">
        <span className="eyebrow">Marché locatif · Yaoundé &amp; Douala</span>
        <h1 id="accueil-titre">Comprendre le marché avant de fixer un loyer</h1>
        <p className="hero__lead">
          CamRent estime un loyer mensuel <strong>demandé</strong> dans les annonces, avec une
          fourchette et le nombre d’observations qui la soutiennent. Il aide ensuite à situer ce
          loyer dans son quartier, puis à comparer plusieurs logements.
        </p>
        <div className="hero__actions">
          <Link className="button button--primary" href="/estimer">
            Estimer un loyer
          </Link>
          <Link className="button button--secondary" href="/explorer">
            Explorer le marché
          </Link>
        </div>
      </section>

      <section className="section" aria-labelledby="parcours-titre">
        <h2 id="parcours-titre">Le parcours</h2>
        <p className="muted">
          Une question par écran : le prix d’un logement, le niveau du quartier, puis la
          comparaison de plusieurs biens.
        </p>
        <div className="card-grid card-grid--three">
          {FLOW_STEPS.map((item) => (
            <FlowCard
              key={item.href}
              step={item.step}
              title={item.title}
              description={item.description}
              href={item.href}
              status={item.status}
            />
          ))}
        </div>
        <div className="notice notice--warning" role="status">
          <h2>Le socle est en place, les écrans arrivent</h2>
          <p>
            Cette version livre la structure, le thème et le client d’API. Les écrans
            d’estimation, d’exploration et de comparaison seront livrés par les tickets 09a.2 à
            09a.4 : d’ici là, aucune estimation n’est proposée et aucun chiffre n’est affiché.
          </p>
        </div>
      </section>

      <section className="section" aria-labelledby="limites-titre">
        <h2 id="limites-titre">Ce que CamRent fait — et ne fait pas</h2>
        <div className="card-grid">
          <article className="card">
            <h3>Ce que l’outil fait</h3>
            <ul className="list-check">
              <li>Estimer un loyer <strong>demandé</strong> avec une fourchette, jamais un chiffre seul.</li>
              <li>Rattacher chaque statistique à son nombre d’observations.</li>
              <li>Distinguer le prix demandé de la référence locale du quartier.</li>
              <li>Dire quand une médiane n’est pas publiée faute d’observations suffisantes.</li>
            </ul>
          </article>
          <article className="card">
            <h3>Ce que l’outil ne fait pas</h3>
            <ul className="list-check list-check--warning">
              <li>Présenter une estimation comme la valeur officielle d’un bien.</li>
              <li>Afficher un pourcentage de confiance non justifié statistiquement.</li>
              <li>Afficher une statistique sans son nombre d’observations.</li>
              <li>Chercher un logement par budget : hors périmètre du MVP.</li>
            </ul>
          </article>
        </div>
      </section>
    </>
  );
}
