import type { Metadata } from "next";

import { EstimationForm } from "@/components/estimation-form";

export const metadata: Metadata = {
  title: "Estimer mon loyer",
};

export default function EstimerPage() {
  return (
    <div className="estimer">
      <header className="page-header">
        <span className="badge">Étape 1</span>
        <h1>Estimer mon loyer</h1>
        <p className="page-header__lead">
          Cinq caractéristiques, rien de plus : celles que le modèle sait réellement
          exploiter. La superficie, le mobilier ou le parking ne sont pas demandés,
          parce que la donnée n&apos;existe pas et que l&apos;estimation ne les
          prend pas en compte.
        </p>
      </header>

      <EstimationForm />

      <aside className="notice notice--warning" aria-label="Limites de l'estimation">
        <h2>Ce que cette estimation n&apos;est pas</h2>
        <ul className="list-check list-check--warning">
          <li>Elle porte sur le loyer <strong>demandé</strong> dans les annonces, jamais sur un prix payé.</li>
          <li>Une fourchette accompagne toujours le montant : un chiffre seul n&apos;est pas une estimation fiable.</li>
          <li>Ce n&apos;est pas la valeur officielle du bien.</li>
          <li>Un quartier du référentiel jamais observé à l&apos;entraînement est refusé, pas « estimé à l&apos;aveugle ».</li>
        </ul>
      </aside>
    </div>
  );
}
