import type { Metadata } from "next";

import { PendingScreen } from "@/components/pending-screen";

export const metadata: Metadata = {
  title: "Estimer mon loyer",
};

export default function EstimerPage() {
  return (
    <PendingScreen
      title="Estimer mon loyer"
      description="Le formulaire d’estimation demandera la ville, le quartier, le type de bien, le nombre de chambres et de salles de bain — les seules caractéristiques réellement prises en charge par le modèle."
      ticket="09a.2"
    />
  );
}
