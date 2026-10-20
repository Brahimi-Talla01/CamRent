import Link from "next/link";

type FlowCardProps = {
  step: string;
  title: string;
  description: string;
  href: string;
  /** Où en est l'écran : ne jamais laisser croire qu'il est déjà livré. */
  status: string;
};

/** Une étape du parcours, avec son état réel. */
export function FlowCard({ step, title, description, href, status }: FlowCardProps) {
  return (
    <article className="card">
      <span className="badge">{step}</span>
      <h3>{title}</h3>
      <p>{description}</p>
      <p className="card__status">{status}</p>
      <Link className="card__link" href={href}>
        Ouvrir l’écran<span aria-hidden="true"> →</span>
      </Link>
    </article>
  );
}
