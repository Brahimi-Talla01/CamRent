import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "CamRent — estimer et comprendre les loyers",
    template: "%s · CamRent",
  },
  description:
    "Estimation indicative du loyer mensuel demandé à Yaoundé et Douala : fourchette, " +
    "nombre d'observations et contexte de marché. Une estimation n'est pas une valeur " +
    "officielle du bien.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <body>
        <a className="skip-link" href="#contenu">
          Aller au contenu
        </a>
        <SiteHeader />
        <main id="contenu" className="container page">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}
