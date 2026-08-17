import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Download, FileText } from "lucide-react";
import { reports } from "@/lib/site-data";

type ReportDetailPageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return reports.map((item) => ({ slug: item.slug }));
}

export async function generateMetadata({ params }: ReportDetailPageProps) {
  const { slug } = await params;
  const item = reports.find((entry) => entry.slug === slug);
  return { title: item?.title ?? "居住研究院" };
}

export default async function ReportDetailPage({ params }: ReportDetailPageProps) {
  const { slug } = await params;
  const item = reports.find((entry) => entry.slug === slug);
  if (!item) notFound();

  return (
    <article className="report-detail">
      <div className="report-detail-media">
        <Image src={item.image} alt={item.title} fill priority sizes="100vw" />
      </div>
      <div className="report-detail-body">
        <Link href="/institute" className="detail-back">
          <ArrowLeft size={15} />
          返回居住研究院
        </Link>
        <span className="eyebrow">{item.author}</span>
        <h1>{item.title}</h1>
        <p>{item.summary}</p>
        <div className="report-highlights">
          {item.highlights.map((highlight) => (
            <div key={highlight}>
              <FileText size={15} />
              <span>{highlight}</span>
            </div>
          ))}
        </div>
        <button className="primary-button">
          下载报告
          <Download size={15} />
        </button>
      </div>
    </article>
  );
}
