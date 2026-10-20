import Link from "next/link";

type PendingScreenProps = {
  title: string;
  description: string;
  /** Ticket qui livrera l'écran : l'utilisateur sait ce qui manque, et pourquoi. */
  ticket: string;
};

/**
 * Écran d'une étape du parcours **pas encore livrée**.
 *
 * Le socle (09a.1) ne propose pas d'estimation : afficher un résultat simulé ou
 * un formulaire inerte laisserait croire à une capacité absente. Cet écran le dit
 * explicitement et renvoie à l'accueil.
 */
export function PendingScreen({ title, description, ticket }: PendingScreenProps) {
  return (
    <div className="pending">
      <span className="badge">Écran à venir</span>
      <h1>{title}</h1>
      <p>{description}</p>
      <p className="small muted">
        Cet écran sera livré par le ticket {ticket}. Aucune estimation, aucun chiffre et aucune
        statistique ne sont simulés ici.
      </p>
      <Link className="button button--secondary" href="/">
        Retour à l’accueil
      </Link>
    </div>
  );
}
