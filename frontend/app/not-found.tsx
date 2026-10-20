import Link from "next/link";

export default function NotFound() {
  return (
    <div className="pending">
      <span className="badge">Page inconnue</span>
      <h1>Cette page n’existe pas</h1>
      <p>Le parcours CamRent se limite à l’estimation, à l’exploration du marché et à la comparaison de logements.</p>
      <Link className="button button--secondary" href="/">
        Retour à l’accueil
      </Link>
    </div>
  );
}
