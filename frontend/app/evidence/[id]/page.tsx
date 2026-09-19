import { EvidenceDetailPage } from "@/components/civic/evidence-detail";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";
export default async function EvidencePage({ params }: PageProps<"/evidence/[id]">) { const { id } = await params; return <SiteShell><EvidenceDetailPage id={id}/></SiteShell>; }
