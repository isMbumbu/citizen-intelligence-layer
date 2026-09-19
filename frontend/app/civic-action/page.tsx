import { CivicActionPage } from "@/components/civic/support-pages";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";
export default function CivicAction() { return <SiteShell><CivicActionPage/></SiteShell>; }
