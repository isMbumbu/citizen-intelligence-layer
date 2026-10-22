import { EvidenceSourcesPage } from "@/components/civic/evidence-browse";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";
export default function Evidence() { return <SiteShell><EvidenceSourcesPage/></SiteShell>; }
