"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { fetchHealth } from "@/lib/api";
import { Brand, Icon } from "./ui";

const nav = [
  { href: "/", label: "Home", icon: "home" as const },
  { href: "/projects", label: "Projects", icon: "projects" as const },
  { href: "/civic-action", label: "Civic Action / Reports", icon: "report" as const },
  { href: "/comments", label: "Comments", icon: "comment" as const },
  { href: "/evidence", label: "Evidence", icon: "evidence" as const },
  { href: "/moderation", label: "Moderation", icon: "moderation" as const },
];

function isActive(path: string, href: string) {
  return href === "/" ? path === "/" : path.startsWith(href);
}

export function StatusIndicator({ compact = false }: { compact?: boolean }) {
  const [status, setStatus] = useState<"online" | "offline">("offline");
  useEffect(() => { void fetchHealth().then((health) => setStatus(health.status === "ok" ? "online" : "offline")).catch(() => setStatus("offline")); }, []);
  return <span className={`backend-status backend-status--${status}`} title={status === "online" ? "Backend Online" : "Backend unavailable"}><i />{!compact && <span><strong>{status === "online" ? "Backend Online" : "Backend unavailable"}</strong><small>API v1</small></span>}</span>;
}

export function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [pathname]);
  return <header className="site-header">
    <div className="site-header__inner">
      <Brand />
      <nav className="primary-nav" aria-label="Primary navigation">{nav.map((item) => <Link key={item.href} className={isActive(pathname, item.href) ? "is-active" : ""} href={item.href}><Icon name={item.icon} size={15}/><span>{item.label}</span></Link>)}</nav>
      <div className="header-actions"><Link href="/projects" className="header-search" aria-label="Search projects"><Icon name="search" size={19}/></Link><span className="header-divider"/><StatusIndicator/><button className="menu-button" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="mobile-nav" aria-label={open ? "Close menu" : "Open menu"}><Icon name={open ? "close" : "menu"} size={22}/></button></div>
    </div>
    {open && <nav id="mobile-nav" className="mobile-nav" aria-label="Mobile navigation">{nav.map((item) => <Link key={item.href} className={isActive(pathname, item.href) ? "is-active" : ""} href={item.href}><Icon name={item.icon}/>{item.label}</Link>)}<StatusIndicator/></nav>}
  </header>;
}

export function Footer() {
  return <footer className="site-footer"><div className="site-footer__inner"><div className="footer-brand"><Brand inverse/><p>Public information citizens can understand, verify and act on.</p></div><nav aria-label="Footer navigation"><Link href="/about">About</Link><Link href="/help">Help</Link><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link></nav><div className="footer-status"><span>API v1</span><StatusIndicator compact/></div></div></footer>;
}

export function SiteShell({ children }: { children: ReactNode }) {
  return <div className="app-shell"><Header/><main>{children}</main><Footer/></div>;
}

export function PageIntro({ eyebrow, title, body, children }: { eyebrow?: string; title: string; body: string; children?: ReactNode }) {
  return <section className="page-intro"><div className="content-wrap"><p className="eyebrow">{eyebrow ?? "CIVICACT"}</p><h1>{title}</h1><p>{body}</p>{children}</div></section>;
}
