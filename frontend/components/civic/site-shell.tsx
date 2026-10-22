"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { fetchHealth } from "@/lib/api";
import { useApiQuery } from "@/lib/use-api-query";
import { Brand, Icon } from "./ui";

const nav = [
  { href: "/projects", label: "Projects", icon: "projects" as const },
  { href: "/reports", label: "Reports", icon: "report" as const },
  { href: "/categories", label: "Categories", icon: "folder" as const },
  { href: "/evidence", label: "Evidence & Sources", icon: "evidence" as const },
  { href: "/how-it-works", label: "How it works", icon: "shield" as const },
];

function isActive(path: string, href: string) {
  return path === href || (href !== "/" && path.startsWith(`${href}/`));
}

export function StatusIndicator({ compact = false }: { compact?: boolean }) {
  const { data, loading, refresh } = useApiQuery(fetchHealth, { retries: 0 });
  const status = loading ? "checking" : data?.status === "ok" ? "online" : "offline";
  const label = status === "online" ? "System live" : status === "checking" ? "Checking API" : "API unavailable";

  return (
    <span className={`status-pill status-pill--${status}`} title={label} aria-live="polite">
      <span className="status-pill__dot" aria-hidden="true" />
      {!compact && <span className="status-pill__label font-mono">{label}</span>}
      {status === "offline" && <button type="button" className="status-pill__retry" onClick={() => void refresh()} aria-label="Retry API connection">Retry</button>}
    </span>
  );
}

function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    let saved: string | null = null;
    try {
      saved = window.localStorage.getItem("civicact-theme");
    } catch {
      // Keep using the system preference when storage is unavailable.
    }
    const selected = saved === "dark" || saved === "light"
      ? saved
      : window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    document.documentElement.dataset.theme = selected;
    setTheme(selected);
  }, []);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      window.localStorage.setItem("civicact-theme", next);
    } catch {
      // Apply the selected theme for this session even if storage is unavailable.
    }
    setTheme(next);
  };

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
    >
      <Icon name={theme === "dark" ? "sun" : "moon"} size={17} />
    </button>
  );
}

export function Header() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => setOpen(false), [pathname]);

  return (
    <header className="site-header">
      <div className="kenya-flag-banner" role="img" aria-label="Kenyan flag in a brush painted style" />
      <div className="site-header__inner">
        <Brand />
        <nav className="primary-nav" aria-label="Primary navigation">
          {nav.map((item) => <Link key={item.href} className={`primary-nav__link ${isActive(pathname, item.href) ? "is-active" : ""}`} href={item.href}><Icon name={item.icon} size={16}/><span>{item.label}</span></Link>)}
        </nav>
        <div className="header-actions">
          <Link href="/projects" className="header-search" aria-label="Search public projects"><Icon name="search" size={19}/></Link>
          <ThemeToggle />
          <span className="header-divider" aria-hidden="true"/>
          <StatusIndicator />
          <button type="button" className="menu-button" onClick={() => setOpen((value) => !value)} aria-expanded={open} aria-controls="mobile-nav" aria-label={open ? "Close menu" : "Open menu"}>
            <Icon name={open ? "close" : "menu"} size={22}/>
          </button>
        </div>
      </div>
      {open && <nav id="mobile-nav" className="mobile-nav" aria-label="Mobile navigation">
        {nav.map((item) => <Link key={item.href} className={`mobile-nav__link ${isActive(pathname, item.href) ? "is-active" : ""}`} href={item.href}><Icon name={item.icon} size={18}/><span>{item.label}</span></Link>)}
        <StatusIndicator />
      </nav>}
    </header>
  );
}

export function Footer() {
  return <footer className="site-footer"><div className="site-footer__inner">
    <div className="footer-brand"><Brand inverse/><p>Public information citizens can understand, verify and act on.</p></div>
    <nav className="footer-nav" aria-label="Footer navigation"><Link href="/about">About</Link><Link href="/how-it-works">How it works</Link><Link href="/community-safety">Community safety</Link><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link></nav>
    <div className="footer-status"><span className="font-mono text-xs">API v1</span><StatusIndicator compact/></div>
  </div></footer>;
}

function RouteTransition({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [pending, setPending] = useState(false);
  const timeout = useRef<number | undefined>(undefined);

  useEffect(() => {
    setPending(false);
    window.clearTimeout(timeout.current);
  }, [pathname]);

  useEffect(() => {
    const handleNavigation = (event: MouseEvent) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if (!(event.target instanceof Element)) return;

      const link = event.target.closest<HTMLAnchorElement>("a[href]");
      if (!link || link.target === "_blank" || link.hasAttribute("download")) return;

      const destination = new URL(link.href, window.location.href);
      if (destination.origin !== window.location.origin) return;
      if (destination.pathname === window.location.pathname && destination.search === window.location.search) return;

      setPending(true);
      window.clearTimeout(timeout.current);
      timeout.current = window.setTimeout(() => setPending(false), 8000);
    };

    document.addEventListener("click", handleNavigation);
    return () => {
      document.removeEventListener("click", handleNavigation);
      window.clearTimeout(timeout.current);
    };
  }, []);

  return (
    <>
      <div className={`route-progress${pending ? " is-active" : ""}`} aria-hidden="true"><span /></div>
      <span className="sr-only" aria-live="polite">{pending ? "Loading page" : ""}</span>
      <div className="route-page" key={pathname}>{children}</div>
    </>
  );
}

export function SiteShell({ children }: { children: ReactNode }) {
  return <div className="app-shell"><Header/><main className="app-main"><RouteTransition>{children}</RouteTransition></main><Footer/></div>;
}

export function PageIntro({ eyebrow, title, body, children }: { eyebrow?: string; title: string; body: string; children?: ReactNode }) {
  return <section className="page-intro"><div className="content-wrap"><div className="page-intro__header">{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1><p className="page-intro__body">{body}</p></div>{children}</div></section>;
}
