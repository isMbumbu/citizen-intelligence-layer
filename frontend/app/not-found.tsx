import Link from "next/link";
import { SiteShell } from "@/components/civic/site-shell";

export default function NotFound() { return <SiteShell><section className="content-wrap page-space"><div className="not-found"><p className="eyebrow">404</p><h1>This public page could not be found.</h1><p>The record may be unavailable, protected, or no longer published.</p><Link className="button button--dark" href="/projects">Browse projects</Link></div></section></SiteShell>; }
