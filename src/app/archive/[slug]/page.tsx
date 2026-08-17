import { redirect } from "next/navigation";

const archiveSlugs = [
  "account-logout",
  "about",
  "apply-and-use",
  "decorate-tips",
  "home",
  "institute",
  "merchant",
  "privacy",
  "sensitive-personal-message",
  "terms",
  "third-party-sdk",
  "zhuhaojia",
];

export function generateStaticParams() {
  return archiveSlugs.map((slug) => ({ slug }));
}

export default async function ArchiveRedirect({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  if (slug === "about") {
    redirect("/site/about");
  }
  if (slug === "decorate-tips") {
    redirect("/site/decorateTips");
  }
  if (slug === "institute") {
    redirect("/site/institute");
  }
  redirect(`/archive/${slug}/index.html`);
}
