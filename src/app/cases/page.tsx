import { cases } from "@/lib/site-data";
import { CaseCard } from "@/components/site/CaseCard";
import { PageHero } from "@/components/site/PageHero";

export default function CasesPage() {
  return (
    <>
      <PageHero
        eyebrow="装修案例"
        title="真实住家的灵感合集"
        description="不同面积、风格与预算的真实案例，帮你更快找到适合自己的家。"
        image="/images/case-1.jpg"
        compact
      />
      <section className="content-section">
        <div className="case-grid">
          {cases.map((item) => (
            <CaseCard key={item.slug} item={item} />
          ))}
        </div>
      </section>
    </>
  );
}
