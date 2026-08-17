import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Check, MapPin, Ruler } from "lucide-react";
import { cases } from "@/lib/site-data";

type CaseDetailPageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return cases.map((item) => ({ slug: item.slug }));
}

export async function generateMetadata({ params }: CaseDetailPageProps) {
  const { slug } = await params;
  const item = cases.find((entry) => entry.slug === slug);
  return { title: item?.title ?? "装修案例" };
}

export default async function CaseDetailPage({ params }: CaseDetailPageProps) {
  const { slug } = await params;
  const item = cases.find((entry) => entry.slug === slug);
  if (!item) notFound();

  return (
    <article className="detail-page">
      <div className="detail-page-hero">
        <Image src={item.image} alt={item.title} fill priority sizes="100vw" />
        <div className="detail-page-hero-overlay" />
        <div className="detail-page-hero-content">
          <Link href="/cases" className="detail-back">
            <ArrowLeft size={15} />
            返回案例列表
          </Link>
          <span className="eyebrow">{item.style}</span>
          <h1>{item.title}</h1>
          <div className="detail-meta">
            <span>
              <Ruler size={14} />
              {item.area}
            </span>
            <span>
              <MapPin size={14} />
              参考案例
            </span>
            {item.tags.map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
        </div>
      </div>
      <div className="detail-body">
        <p className="detail-summary">{item.summary}</p>
        <div className="detail-points">
          {item.details.map((detail) => (
            <div key={detail}>
              <Check size={15} />
              <span>{detail}</span>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}
