import type { Metadata } from "next";
import { ModerationPage } from "@/components/civic/moderation";
import { SiteShell } from "@/components/civic/site-shell";

// Staff tool: not linked from public navigation and kept out of search results.
export const metadata: Metadata = { title: "Staff moderation tool", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";
export default function Moderation() { return <SiteShell><ModerationPage/></SiteShell>; }
