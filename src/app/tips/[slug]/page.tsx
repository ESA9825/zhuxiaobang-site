import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, CheckCircle2, Lightbulb } from "lucide-react";
import { tips } from "@/lib/site-data";

type TipDetailPageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return tips.map((item) => ({ slug: item.slug }));
}

export async function generateMetadata({ params }: TipDetailPageProps) {
  const { slug } = await params;
  const item = tips.find((entry) => entry.slug === slug);
  return { title: item?.title ?? "装修锦囊" };
}

export default async function TipDetailPage({ params }: TipDetailPageProps) {
  const { slug } = await params;
  const item = tips.find((entry) => entry.slug === slug);
  if (!item) notFound();

  return (
    <article className="detail-page tip-detail">
      <div className="tip-detail-hero">
        <Image src={item.image} alt={item.title} fill priority sizes="100vw" />
        <div className="page-hero-overlay" />
        <div className="page-hero-content">
          <Link href="/decorate-tips" className="detail-back">
            <ArrowLeft size={15} />
            返回装修锦囊
          </Link>
          <span className="eyebrow">{item.category}</span>
          <h1>{item.title}</h1>
          <p>{item.summary}</p>
        </div>
      </div>
      <div className="detail-body">
        <div className="detail-section-label">
          <Lightbulb size={15} />
          操作步骤
        </div>
        <div className="tip-steps">
          {item.steps.map((step, index) => (
            <div key={step}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <CheckCircle2 size={15} />
              <p>{step}</p>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}
