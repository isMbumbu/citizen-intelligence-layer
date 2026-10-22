import { ReportsPage } from "@/components/civic/reports";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";
export default function Reports() { return <SiteShell><ReportsPage/></SiteShell>; }
