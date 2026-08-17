import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import type { CaseItem } from "@/lib/site-data";

type CaseCardProps = {
  item: CaseItem;
};

export function CaseCard({ item }: CaseCardProps) {
  return (
    <article className="case-card">
      <Link href={`/cases/${item.slug}`} className="case-card-media">
        <Image src={item.image} alt={item.title} fill sizes="(max-width: 768px) 100vw, 33vw" />
        <span>{item.area}</span>
      </Link>
      <div className="case-card-body">
        <div className="case-card-tags">
          {item.tags.map((tag) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>
        <Link href={`/cases/${item.slug}`}>
          <h2>{item.title}</h2>
          <ArrowUpRight size={16} />
        </Link>
        <p>{item.summary}</p>
      </div>
    </article>
  );
}
