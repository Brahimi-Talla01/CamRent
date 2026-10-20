import type { Metadata } from "next";

import { PendingScreen } from "@/components/pending-screen";

export const metadata: Metadata = {
  title: "Comparer des logements",
};

export default function ComparerPage() {
  return (
    <PendingScreen
      title="Comparer des logements"
      description="L’écran de comparaison placera côte à côte le prix demandé, l’estimation et la référence locale d’un à dix logements, avec des écarts signés et le nombre d’observations de chaque groupe."
      ticket="09a.4"
    />
  );
}
