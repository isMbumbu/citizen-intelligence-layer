import { ProjectExplorer } from "@/components/civic/discovery";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";
export default function ProjectsPage() { return <SiteShell><ProjectExplorer intro="Explore public projects, their locations, categories, and available project information."/></SiteShell>; }
