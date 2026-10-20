import Link from "next/link";

/**
 * Navigation du parcours public (spec 09 §2).
 *
 * Composant serveur : aucun état client, aucun JavaScript envoyé pour la
 * navigation. Les cibles existent dès ce socle, même si les écrans métier
 * arrivent avec 09a.2 à 09a.4.
 */
const FLOW_LINKS = [
  { href: "/", label: "Accueil" },
  { href: "/estimer", label: "Estimer" },
  { href: "/explorer", label: "Explorer" },
  { href: "/comparer", label: "Comparer" },
] as const;

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <Link href="/" className="brand">
          <span className="brand__mark" aria-hidden="true" />
          CamRent
        </Link>
        <nav aria-label="Parcours principal" className="nav">
          {FLOW_LINKS.map((link) => (
            <Link key={link.href} href={link.href}>
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
