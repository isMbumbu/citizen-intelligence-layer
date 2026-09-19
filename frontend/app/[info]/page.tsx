import { notFound } from "next/navigation";
import { SiteShell } from "@/components/civic/site-shell";

const pages: Record<string, { eyebrow: string; title: string; body: string }> = {
  about: { eyebrow: "ABOUT CIVICACT", title: "Public information for public action.", body: "CIVICACT helps citizens explore public projects, understand sources and verification, and make evidence-aware civic reports." },
  help: { eyebrow: "HELP", title: "How CIVICACT works", body: "Start with projects, open a project record to understand its available information, then use civic reporting, comments, and evidence tools where the API supports them." },
  privacy: { eyebrow: "PRIVACY", title: "Privacy and public submissions", body: "The interface only sends information to the backend endpoints you actively use. Avoid sharing unnecessary personal information in public comments or reports." },
  terms: { eyebrow: "TERMS", title: "Using CIVICACT responsibly", body: "Treat public discussion and citizen-submitted evidence as inputs, not verification. Review the source and verification panels before drawing conclusions." },
};

export default async function InformationPage({ params }: PageProps<"/[info]">) {
  const { info } = await params;
  const page = pages[info];
  if (!page) notFound();
  return <SiteShell><section className="page-intro"><div className="content-wrap"><p className="eyebrow">{page.eyebrow}</p><h1>{page.title}</h1><p>{page.body}</p></div></section></SiteShell>;
}
