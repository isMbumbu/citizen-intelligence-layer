import { ProjectDetailPage } from "@/components/civic/project-detail";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";
export default async function ProjectPage({ params }: PageProps<"/projects/[id]">) { const { id } = await params; return <SiteShell><ProjectDetailPage id={id}/></SiteShell>; }
