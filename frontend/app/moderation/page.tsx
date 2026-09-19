import { ModerationPage } from "@/components/civic/moderation";
import { SiteShell } from "@/components/civic/site-shell";

export const dynamic = "force-dynamic";
export default function Moderation() { return <SiteShell><ModerationPage/></SiteShell>; }
