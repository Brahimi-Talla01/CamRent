import type { Metadata } from "next";

import { PendingScreen } from "@/components/pending-screen";

export const metadata: Metadata = {
  title: "Explorer le marché",
};

export default function ExplorerPage() {
  return (
    <PendingScreen
      title="Explorer le marché"
      description="L’écran d’exploration présentera les prix par quartier et par type de logement, avec la moyenne, la médiane lorsqu’elle est publiée, la fourchette et le nombre d’observations."
      ticket="09a.3"
    />
  );
}
