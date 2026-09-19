"use client";
import { SiteShell } from "@/components/civic/site-shell";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) { return <html lang="en"><body><SiteShell><section className="content-wrap page-space"><div className="not-found"><p className="eyebrow">SERVICE NOTICE</p><h1>We could not load this page.</h1><p>Please try again. The public service may be temporarily unavailable.</p><button className="button button--dark" onClick={reset}>Try again</button></div></section></SiteShell></body></html>; }
