import Image from "next/image";

type PageHeroProps = {
  eyebrow: string;
  title: string;
  description: string;
  image: string;
  compact?: boolean;
};

export function PageHero({
  eyebrow,
  title,
  description,
  image,
  compact = false,
}: PageHeroProps) {
  return (
    <section className={compact ? "page-hero compact" : "page-hero"}>
      <Image className="page-hero-bg" src={image} alt="" fill priority sizes="100vw" />
      <div className="page-hero-overlay" />
      <div className="page-hero-content">
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
    </section>
  );
}
